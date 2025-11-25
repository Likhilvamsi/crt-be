from pydantic import BaseModel
from typing import Optional
 
class LoginSchema(BaseModel):
    email: str
    password: str
 
class LoginResponse(BaseModel):
    user_id: int
    email: str
    role: str
    college_id: Optional[int] = None
    branch_id: Optional[int] = None
 
 