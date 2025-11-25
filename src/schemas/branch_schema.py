# src/schemas/branch_schema.py
from pydantic import BaseModel, EmailStr
from typing import Optional
from src.db.models import BranchType


class BranchCreateSchema(BaseModel):
    college_id: str
    branch_type: BranchType
    branch_name: str
    hod_name: Optional[str] = None
    hod_email: Optional[EmailStr] = None
