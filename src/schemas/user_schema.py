# src/schemas/user_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional


class AppAdminRegisterSchema(BaseModel):
    email: EmailStr
    password: str
    phone: Optional[str] = None


class CollegeAdminCreateSchema(BaseModel):
    college_id: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class BranchAdminCreateSchema(BaseModel):
    branch_id: str
    email: EmailStr
    password: str
    phone: Optional[str] = None
