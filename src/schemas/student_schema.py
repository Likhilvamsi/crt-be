from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class StudentCreateSchema(BaseModel):
    # User info
    email: EmailStr
    password: str
    phone: Optional[str] = None

    # Student info
    college_id: int
    branch_id: int
    roll_number: str
    first_name: str
    last_name: str
    date_of_birth: Optional[datetime] = None
    gender: Optional[str] = None
    current_year: int = 1
