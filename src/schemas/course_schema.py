# src/schemas/course_schema.py
from pydantic import BaseModel
from typing import Optional


class CourseCreateSchema(BaseModel):
    branch_id: str
    course_name: str
    year: int
    description: Optional[str] = None
