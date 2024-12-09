from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import List, Optional
from .. import schemas, models
from ..database import get_db
from app.schemas import PaginatedResponse

router = APIRouter()

# Set template directory
templates = Jinja2Templates(directory="src/app/templates")

# ========== User routes ==========
@router.get("/user/create")
async def get_user_create_form(request: Request):
    return templates.TemplateResponse(
        "user/create.html",
        {
            "request": request, 
            "title": "新增使用者"
        }
    )

@router.post("/user/create", response_model=schemas.UserInDB)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    db_user = models.User(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/users/", response_model=List[schemas.UserInDB])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/users/by-role/{role_id}", response_model=List[schemas.UserInDB])
def read_users_by_role(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # TODO: Read users by role
    users = db.query(models.User).offset(skip).limit(limit).all()
    return users

@router.get("/user/{user_id}", response_model=schemas.UserInDB)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.put("/user/{user_id}", response_model=schemas.UserInDB)
def update_user(user_id: int, user: schemas.UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    for key, value in user.model_dump(exclude_unset=True).items():
        setattr(db_user, key, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user

@router.delete("/user/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    
    db.delete(db_user)
    db.commit()
    return {"detail": "User deleted"}

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
    # TODO: Create a page to update organization unit information and return this page
    return templates.TemplateResponse(
        "organization_unit/update.html",
        {
            "request": request,
            "title": "更新組織單位資料"
        }
    )

@router.get("/organization-units/{unit_id}", response_model=schemas.OrganizationUnitInDB)
def read_organization_unit(unit_id: int, db: Session = Depends(get_db)):
    db_unit = db.query(models.Organization_units).filter(models.Organization_units.id == unit_id).first()
    if db_unit is None:
        raise HTTPException(status_code=404, detail="Organization unit not found")
    return db_unit

@router.post("/organization-units/{unit_id}/update", response_model=schemas.OrganizationUnitUpdate)
def update_organization_unit(
    unit_id: int,
    unit: schemas.OrganizationUnitUpdate,
    db: Session = Depends(get_db)
):
    # Confirm if organization unit exists
    db_unit = db.query(models.Organization_units).filter(models.Organization_units.id == unit_id).first()
    if not db_unit:
        raise HTTPException(status_code=404, detail="Organization unit not found")

    # 更新資料
    for key, value in unit.dict(exclude_unset=True).items():
        setattr(db_unit, key, value)

    try:
        db.commit()
        return db_unit
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))

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

@router.get("/organization-units/parent/by-category/{category_id}", response_model=List[schemas.OrganizationUnitInDB])
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

@router.get("/organization-units/hierarchy", response_model=List[dict])
async def get_organization_hierarchy(
    db: Session = Depends(get_db)
):
    # TODO: Confirm this api works properly
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

# User Organization Unit routes
@router.post("/user-organization-units/", response_model=schemas.UserOrganizationUnitInDB)
def create_user_organization_unit(
    user_unit: schemas.UserOrganizationUnitCreate, 
    db: Session = Depends(get_db)
):
    # TODO: Confirm this api works properly
    db_user_unit = models.User_organization_units(**user_unit.model_dump())
    db.add(db_user_unit)
    db.commit()
    db.refresh(db_user_unit)
    return db_user_unit

@router.get("/user-organization-units/by-user/{user_id}", response_model=List[schemas.UserOrganizationUnitInDB])
def read_user_organization_units(user_id: int, db: Session = Depends(get_db)):
    # TODO: Confirm this api works properly
    user_units = db.query(models.User_organization_units).filter(
        models.User_organization_units.user_id == user_id
    ).all()
    return user_units

@router.get("/users/{user_id}/organization-units", response_model=List[schemas.OrganizationUnitInDB])
async def get_user_organization_units(
    user_id: int,
    db: Session = Depends(get_db)
):
    # TODO: Confirm this api works properly
    units = db.query(models.Organization_units)\
        .join(models.User_organization_units)\
        .filter(models.User_organization_units.user_id == user_id)\
        .all()
    return units