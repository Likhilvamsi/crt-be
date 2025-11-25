# src/schemas/college_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional


class CollegeCreateSchema(BaseModel):
    college_name: str
    college_code: str
    city: Optional[str] = None
    state: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[EmailStr] = None
    website: Optional[str] = None
