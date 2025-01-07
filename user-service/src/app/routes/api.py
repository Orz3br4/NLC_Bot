from datetime import date, timedelta
import logging
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy import and_
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, ProgrammingError, OperationalError
from typing import Dict, List, Optional
from .. import schemas, models
from ..database import get_db
from app.schemas import AttendanceStats, PaginatedResponse, WeeklyAttendanceReport

router = APIRouter()

# Set template directory
templates = Jinja2Templates(directory="src/app/templates")

logger = logging.getLogger(__name__)

# ========== User routes ==========
@router.get("/user/create")
async def get_user_create_form(request: Request):
    """
    Get the form template for creating a new user
    
    Args:
        request: The FastAPI request object
        
    Returns:
        TemplateResponse: The rendered create user form template
    """
    return templates.TemplateResponse(
        "user/create.html",
        {
            "request": request, 
            "title": "新增使用者"
        }
    )

@router.post("/user/create", response_model=schemas.UserInDB)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    """
    Create a new user in the system
    
    Args:
        user: The user data to create
        db: Database session dependency
        
    Returns:
        UserInDB: The created user object
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        if user.email:
            db_user = db.query(models.User).filter(models.User.email == user.email).first()
            if db_user:
                raise HTTPException(status_code=400, detail="Email already registered")
        
        # Convert user data to dictionary data type and remove all "None" value
        user_data = user.model_dump(exclude_none=True)
        
        # Create new user
        db_user = models.User(**user_data)
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/user/update")
async def get_user_update_form(request: Request):
    return templates.TemplateResponse(
        "user/update.html",
        {
            "request": request,
            "title": "更新使用者資料"
        }
    )

@router.get("/user/delete")
async def get_user_delete_form(request: Request):
    return templates.TemplateResponse(
        "user/delete.html",
        {
            "request": request,
            "title": "刪除使用者"
        }
    )

@router.get("/users/", response_model=List[schemas.UserInDB])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Get a paginated list of users
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session dependency
        
    Returns:
        List[UserInDB]: List of user objects
    """
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/user/{user_id}", response_model=schemas.UserInDB)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """
    Get a specific user by ID
    
    Args:
        user_id: ID of the user to retrieve
        db: Database session dependency
        
    Returns:
        UserInDB: The requested user object
        
    Raises:
        HTTPException: If user not found
    """
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/user/{user_id}", response_model=schemas.UserInDB)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    """
    Update an existing user's information
    
    Args:
        user_id: ID of the user to update
        user: Updated user data
        db: Database session dependency
        
    Returns:
        UserInDB: The updated user object
        
    Raises:
        HTTPException: If user not found or email already exists
    """
    try:
        # Confirm if user exists
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # If email provided is different from current one, then confirm if it is used
        if user.email and user.email != db_user.email:
            existing_user = db.query(models.User).filter(models.User.email == user.email).first()
            if existing_user:
                raise HTTPException(status_code=400, detail="Email already registered")
        
        # Update user data
        update_data = user.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user, key, value)
        
        db.commit()
        db.refresh(db_user)
        return db_user
    
    except ValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    """
    Delete a user and their organization unit associations
    
    Args:
        user_id: ID of the user to delete
        db: Database session dependency
        
    Returns:
        dict: Success message
        
    Raises:
        HTTPException: If user not found or deletion fails
    """
    try:
        # Confirm if user exists
        db_user = db.query(models.User).filter(models.User.id == user_id).first()
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Delete related "user -> organization units" data
        db.query(models.User_organization_units).filter(
            models.User_organization_units.user_id == user_id
        ).delete()
        
        # Delete user
        db.delete(db_user)
        db.commit()
        
        return {"message": "User successfully deleted"}
    
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== Organization Category routes ==========
@router.get("/organization-category/create")
async def get_create_organization_category_form(request: Request):
    return templates.TemplateResponse(
        "organization_category/create.html",
        {
            "request": request,
            "title": "新增組織類別"
        }
    )

@router.post("/organization-category/create", response_model=schemas.OrganizationCategoryInDB)
def create_organization_category(
    category: schemas.OrganizationCategoryCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new organization category
    
    Args:
        category: Category data to create
        db: Database session dependency
        
    Returns:
        OrganizationCategoryInDB: The created category object
    """
    db_category = models.Organization_categories(**category.model_dump())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

@router.get("/organization-categories/", response_model=PaginatedResponse[schemas.OrganizationCategoryInDB])
async def read_organization_categories(
    skip: int = 0, 
    limit: int = 100,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get a paginated list of organization categories with optional search
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        search: Optional search term for category names
        db: Database session dependency
        
    Returns:
        PaginatedResponse: Paginated list of organization categories
    """
    query = db.query(models.Organization_categories)
    
    if search:
        query = query.filter(models.Organization_categories.category_name.ilike(f"%{search}%"))
    
    total = query.count()
    categories = query.offset(skip).limit(limit).all()
    
    return {
        "items": categories,
        "total": total,
        "skip": skip,
        "limit": limit
    }

# Organization Unit routes
@router.get("/organization-unit/create")
async def get_create_organization_category_form(request: Request):
    return templates.TemplateResponse(
        "organization_unit/create.html",
        {
            "request": request,
            "title": "新增組織單位"
        }
    )

@router.post("/organization-unit/create", response_model=schemas.OrganizationUnitInDB)
def create_organization_unit(
    unit: schemas.OrganizationUnitCreate, 
    db: Session = Depends(get_db)
):
    """
    Create a new organization unit
    
    Args:
        unit: Unit data to create
        db: Database session dependency
        
    Returns:
        OrganizationUnitInDB: The created unit object
    """
    db_unit = models.Organization_units(**unit.model_dump())
    db.add(db_unit)
    db.commit()
    db.refresh(db_unit)
    return db_unit

@router.get("/organization-units/", response_model=List[schemas.OrganizationUnitInDB])
def read_organization_units(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    units = db.query(models.Organization_units).offset(skip).limit(limit).all()
    return units

# This API must be placed here, or it will never be accessible
@router.get("/organization-units/update")
async def get_organization_unit_update_form(request: Request):
    return templates.TemplateResponse(
        "organization_unit/update.html",
        {
            "request": request,
            "title": "更新組織單位資料"
        }
    )

@router.get("/organization-units/hierarchy", response_model=List[dict])
async def get_organization_hierarchy(
    db: Session = Depends(get_db)
):
    """
    Get the complete hierarchical structure of organization units
    
    Args:
        db: Database session dependency
        
    Returns:
        List[dict]: Nested dictionary representing the organization hierarchy
    """
    def build_hierarchy(parent_id: Optional[int] = None):
        units = db.query(models.Organization_units)\
            .filter(models.Organization_units.parent_unit_id == parent_id)\
            .all()
        
        return [
            {
                "id": unit.id,
                "name": unit.unit_name,
                "category_id": unit.category_id,
                "leader_id": unit.leader_id,
                "children": build_hierarchy(unit.id)
            }
            for unit in units
        ]
    
    return build_hierarchy()

@router.get("/organization-units/hierarchy-up/{unit_id}", response_model=List[schemas.OrganizationUnitInDB])
async def get_unit_hierarchy_up(unit_id: int, db: Session = Depends(get_db)):
    """
    Get the complete hierarchy from a unit up to the branch level
    
    Args:
        unit_id: ID of the starting unit
        db: Database session
        
    Returns:
        List[OrganizationUnitInDB]: List of units in hierarchical order (bottom to top)
    """
    try:
        units = []
        current_unit_id = unit_id
        
        while current_unit_id is not None:
            # Get current unit
            current_unit = db.query(models.Organization_units).filter(
                models.Organization_units.id == current_unit_id
            ).first()
            
            if not current_unit:
                break
                
            units.append(current_unit)
            current_unit_id = current_unit.parent_unit_id
            
        return units
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/organization-units/{unit_id}", response_model=schemas.OrganizationUnitInDB)
def read_organization_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(models.Organization_units).filter(models.Organization_units.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Organization unit not found")
    return db_unit

@router.put("/organization-units/{unit_id}/update", response_model=schemas.OrganizationUnitUpdate)
def update_organization_unit(
    unit_id: int,
    unit: schemas.OrganizationUnitUpdate,
    db: Session = Depends(get_db)
):
    # Confirm if organization unit exists
    db_unit = db.query(models.Organization_units).filter(models.Organization_units.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Organization unit not found")

    # Update data
    for key, value in unit.dict(exclude_unset=True).items():
        setattr(db_unit, key, value)

    try:
        db.commit()
        return db_unit
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))
    
@router.get("/organization-units/{unit_id}/members", response_model=List[schemas.UserInDB])
async def get_unit_members(
    unit_id: int,
    db: Session = Depends(get_db)
):
    """
    獲取指定組織單位及其所有子單位的所有成員
    
    Args:
        unit_id: 組織單位ID
        db: 資料庫連線
        
    Returns:
        List[UserInDB]: 該單位及其所有子單位的成員列表
    """
    try:
        # 遞迴獲取所有子單位ID的函數
        def get_all_sub_units(parent_unit_id):
            sub_units = db.query(models.Organization_units.id).filter(
                models.Organization_units.parent_unit_id == parent_unit_id
            ).all()
            unit_ids = [parent_unit_id]
            for sub_unit in sub_units:
                unit_ids.extend(get_all_sub_units(sub_unit.id))
            return unit_ids

        # 獲取當前單位及其所有子單位的ID
        all_unit_ids = get_all_sub_units(unit_id)

        # 查詢所有相關單位的成員
        members = db.query(models.User).distinct().join(
            models.User_organization_units,
            models.User.id == models.User_organization_units.user_id
        ).filter(
            models.User_organization_units.unit_id.in_(all_unit_ids)
        ).all()
        
        if not members:
            raise HTTPException(
                status_code=404, 
                detail=f"No members found in unit {unit_id} or its sub-units"
            )
        
        return members
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error retrieving members: {str(e)}"
        )
    
@router.get("/organization-units/by-parent-unit/{parent_unit_id}", response_model=List[schemas.OrganizationUnitInDB])
def read_units_by_parent_unit(parent_unit_id: int, skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    units = db.query(models.Organization_units)\
        .filter(models.Organization_units.parent_unit_id == parent_unit_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return units

@router.get("/organization-units/by-category/{category_id}", response_model=List[schemas.OrganizationUnitInDB])
async def read_organization_units_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    units = db.query(models.Organization_units)\
        .filter(models.Organization_units.category_id == category_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return units

@router.get("/organization-units/by-parent-category/{category_id}", response_model=List[schemas.OrganizationUnitInDB])
async def read_parent_organization_units_by_category(
    category_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    parent_category_id = category_id - 1
    units = db.query(models.Organization_units)\
        .filter(models.Organization_units.category_id == parent_category_id)\
        .offset(skip)\
        .limit(limit)\
        .all()
    return units

# User Organization Unit routes
@router.post("/user-organization-units/", response_model=schemas.UserOrganizationUnitInDB)
def create_user_organization_unit(
    user_unit: schemas.UserOrganizationUnitCreate, 
    db: Session = Depends(get_db)
):
    db_user_unit = models.User_organization_units(**user_unit.model_dump())
    db.add(db_user_unit)
    db.commit()
    db.refresh(db_user_unit)
    return db_user_unit

@router.get("/user-organization-units/by-user/{user_id}", response_model=List[schemas.UserOrganizationUnitInDB])
def read_user_organization_units(user_id: int, db: Session = Depends(get_db)):
    user_units = db.query(models.User_organization_units).filter(
        models.User_organization_units.user_id == user_id
    ).all()
    return user_units

@router.get("/users/{user_id}/organization-units", response_model=List[schemas.OrganizationUnitInDB])
async def get_user_organization_units(
    user_id: int,
    db: Session = Depends(get_db)
):
    units = db.query(models.Organization_units)\
        .select_from(models.User_organization_units)\
        .filter(models.User_organization_units.user_id == user_id)\
        .all()
    return units

# Attendance API
@router.get("/attendance/report")
async def get_attendance_report_form(request: Request):
    return templates.TemplateResponse(
        "numbers/attendance_report.html",
        {
            "request": request,
            "title": "回報本週主日小組民數"
        }
    )

@router.get("/attendance/query")
async def get_attendance_record_by_query(request: Request):
    return templates.TemplateResponse(
        "numbers/attendance_query.html",
        {
            "request": request,
            "title": "本週主日小組民數"
        }
    )

@router.post("/attendance/submit")
async def submit_attendance(
    data: Dict,
    db: Session = Depends(get_db)
):
    """
    Submit attendance records for multiple users
    
    Args:
        data: Dictionary containing date and attendance records
            Format: {
                'date': 'YYYY-MM-DD',
                'attendance': {
                    'user_id': {
                        'sunday': bool,
                        'group': bool
                    }
                }
            }
        db: Database session dependency
        
    Returns:
        dict: Success message with record count and date
        
    Raises:
        HTTPException: If data format is invalid or database operation fails
    """
    try:
        # 驗證日期格式
        try:
            attendance_date = date.fromisoformat(data['date'])
        except (KeyError, ValueError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="無效的日期格式。請使用 YYYY-MM-DD 格式。"
            )

        # 驗證出席資料結構
        if not data.get('attendance'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="缺少出席資料。"
            )

        attendance_records = []
        
        # 處理每個成員的出席記錄
        for user_id, meetings in data['attendance'].items():
            try:
                user_id = int(user_id)
                # 檢查用戶是否存在
                user = db.query(models.User).filter(models.User.id == user_id).first()
                if not user:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"找不到 ID 為 {user_id} 的用戶"
                    )

                # 檢查是否已有該日期的出席記錄
                existing_records = db.query(models.Meeting_attendance).filter(
                    models.Meeting_attendance.user_id == user_id,
                    models.Meeting_attendance.meeting_date == attendance_date
                ).all()

                if existing_records:
                    # 如果有現有記錄，刪除它們
                    for record in existing_records:
                        db.delete(record)

                # 添加新的出席記錄
                if meetings.get('sunday'):
                    attendance_records.append(
                        models.Meeting_attendance(
                            user_id=user_id,
                            meeting_type=schemas.MeetingType.SUNDAY_SERVICE,
                            meeting_date=attendance_date
                        )
                    )
                
                if meetings.get('group'):
                    attendance_records.append(
                        models.Meeting_attendance(
                            user_id=user_id,
                            meeting_type=schemas.MeetingType.GROUP_MEETING,
                            meeting_date=attendance_date
                        )
                    )

            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"無效的用戶 ID: {user_id}"
                )

        # 批量新增出席記錄
        try:
            db.bulk_save_objects(attendance_records)
            db.commit()
        except ProgrammingError as e:
            db.rollback()
            logger.error(f"資料庫結構錯誤: {str(e)}")
            if 'column "meeting_date" of relation "meeting_attendance" does not exist' in str(e):
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="資料庫結構不完整。請聯繫系統管理員執行資料庫遷移。"
                )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="資料庫操作錯誤，請聯繫系統管理員。"
            )
        except OperationalError as e:
            db.rollback()
            logger.error(f"資料庫連線錯誤: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="無法連接到資料庫，請稍後再試。"
            )
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"資料庫錯誤: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="儲存出席記錄時發生錯誤。"
            )

        return {
            "message": "出席記錄提交成功",
            "records_count": len(attendance_records),
            "date": attendance_date.isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"未預期的錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="處理請求時發生未預期的錯誤。"
        )

@router.get('/attendance/weekly/report/{unit_id}', response_model=WeeklyAttendanceReport)
def read_weekly_attendance_report_by_unit(
    unit_id: int, 
    report_date: date = None,
    db: Session = Depends(get_db)
):
    """
    Get weekly attendance report for a specific organization unit
    
    Args:
        unit_id: The ID of the organization unit
        report_date: The date within the week to generate report for (defaults to current date)
    """
    try:
        # Get the organization unit
        unit = db.query(models.Organization_units).filter(
            models.Organization_units.id == unit_id
        ).first()
        
        if not unit:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization unit not found"
            )
            
        # Calculate week date range
        if report_date is None:
            report_date = date.today()
            
        # Get Monday (start) and Sunday (end) of the week
        start_date = report_date - timedelta(days=report_date.weekday())
        end_date = start_date + timedelta(days=6)
        
        # Get all sub-units recursively
        def get_all_sub_units(parent_unit_id):
            sub_units = db.query(models.Organization_units.id).filter(
                models.Organization_units.parent_unit_id == parent_unit_id
            ).all()
            unit_ids = [parent_unit_id]
            for sub_unit in sub_units:
                unit_ids.extend(get_all_sub_units(sub_unit.id))
            return unit_ids

        # Get all unit IDs including the target unit and its sub-units
        all_unit_ids = get_all_sub_units(unit_id)
        
        # Get all members from all related units
        unit_members = db.query(models.User).distinct().join(
            models.User_organization_units,
            models.User.id == models.User_organization_units.user_id
        ).filter(
            models.User_organization_units.unit_id.in_(all_unit_ids)
        ).all()
        
        # Initialize stats for both meeting types
        sunday_stats = {
            "christian_count": 0,
            "vip_count": 0,
            "new_friend_count": 0,
            "total_count": 0,
            "attendees": [],
            "unique_attendees": 0
        }
        
        group_stats = {
            "christian_count": 0,
            "vip_count": 0,
            "new_friend_count": 0,
            "total_count": 0,
            "attendees": [],
            "unique_attendees": 0
        }
        
        # Get attendance records for the week
        attendance_records = db.query(models.Meeting_attendance).join(
            models.User,
            models.Meeting_attendance.user_id == models.User.id
        ).filter(
            and_(
                models.Meeting_attendance.meeting_date >= start_date,
                models.Meeting_attendance.meeting_date <= end_date,
                models.User.id.in_([member.id for member in unit_members])
            )
        ).all()
        
        # Process attendance records
        for record in attendance_records:
            user = next(m for m in unit_members if m.id == record.user_id)
            attendee_info = {
                "id": user.id,
                "name": user.name,
                "level": user.level
            }
            
            # Update stats based on meeting type
            if record.meeting_type == schemas.MeetingType.SUNDAY_SERVICE:
                stats = sunday_stats
            else:
                stats = group_stats
                
            if user.level == schemas.UserLevel.CHRISTIAN:
                stats["christian_count"] += 1
            elif user.level == schemas.UserLevel.VIP:
                stats["vip_count"] += 1
            elif user.level == schemas.UserLevel.NEW_FRIEND:
                stats["new_friend_count"] += 1
                
            stats["total_count"] += 1
            if attendee_info not in stats["attendees"]:
                stats["attendees"].append(attendee_info)
        
        # Calculate unique attendees
        sunday_stats["unique_attendees"] = len(sunday_stats["attendees"])
        group_stats["unique_attendees"] = len(group_stats["attendees"])
        
        return WeeklyAttendanceReport(
            sunday_service=AttendanceStats(**sunday_stats),
            group_meeting=AttendanceStats(**group_stats),
            unit_name=unit.unit_name,
            start_date=start_date,
            end_date=end_date
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )