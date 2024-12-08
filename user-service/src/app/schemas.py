from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional, List, Generic, TypeVar
from enum import Enum


T = TypeVar('T')

class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    skip: int
    limit: int

# User schemas
class UserLevel(str, Enum):
    CHRISTIAN = "基督徒"
    VIP = "慕道友"
    NEW_FRIEND = "新朋友"

class UserRole(str, Enum):
    MEMBER = "會友"
    EKK_LEADER = "小家長"
    GROUP_LEADER = "小組長"
    DISTRICT_LEADER = "區長"
    BRANCH_LEADER = "分堂領袖"
    PASTOR = "牧師"
    MINISTER = "傳道"

class UserBase(BaseModel):
    name: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    birthday: date
    mobile_number: str = Field(..., pattern=r'^09\d{8}$')
    level: UserLevel
    role: UserRole

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    birthday: Optional[date] = None
    mobile_number: Optional[str] = Field(None, pattern=r'^09\d{8}$')
    level: Optional[UserLevel] = None
    role: Optional[UserRole] = None

class UserInDB(UserBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Organization Category schemas
class OrganizationCategoryBase(BaseModel):
    category_name: str

class OrganizationCategoryCreate(OrganizationCategoryBase):
    pass

class OrganizationCategoryUpdate(BaseModel):
    category_name: Optional[str] = None

class OrganizationCategoryInDB(OrganizationCategoryBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Organization Unit schemas
class OrganizationUnitBase(BaseModel):
    unit_name: str
    category_id: int
    parent_unit_id: Optional[int] = None
    leader_id: Optional[int] = None

class OrganizationUnitCreate(OrganizationUnitBase):
    pass

class OrganizationUnitUpdate(BaseModel):
    unit_name: Optional[str] = None
    category_id: Optional[int] = None
    parent_unit_id: Optional[int] = None
    leader_id: Optional[int] = None

class OrganizationUnitInDB(OrganizationUnitBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        json_encoders={
            datetime: lambda dt: dt.isoformat() if dt else None
        }

# User Organization Unit schemas
class UserOrganizationUnitBase(BaseModel):
    user_id: int
    unit_id: int

class UserOrganizationUnitCreate(UserOrganizationUnitBase):
    pass

class UserOrganizationUnitUpdate(BaseModel):
    user_id: Optional[int] = None
    unit_id: Optional[int] = None

class UserOrganizationUnitInDB(UserOrganizationUnitBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True