from fastapi import APIRouter, Depends, HTTPException

from sqlalchemy.orm import Session

from passlib.context import CryptContext

import datetime
 
from src.db.database import get_db

from src.db.models import User, UserRole

from src.schemas.auth_schema import LoginSchema, LoginResponse
 
router = APIRouter(prefix="/auth", tags=["Auth"])
 
pwd_context = CryptContext(

    schemes=["pbkdf2_sha256"],

    deprecated="auto"

)
 
 
def verify_password(plain: str, hashed: str) -> bool:

    return pwd_context.verify(plain, hashed)
 
 
@router.post("/login", response_model=LoginResponse)

def login(payload: LoginSchema, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == payload.email).first()

    if not user:

        raise HTTPException(status_code=401, detail="Invalid email or password")
 
    if not verify_password(payload.password, user.password_hash):

        raise HTTPException(status_code=401, detail="Invalid email or password")
 
    response_data = {

        "user_id": user.id,

        "role": user.role.value,

        "email": user.email,

    }
 
    # If Branch Admin → include Branch & College details

    if user.role == UserRole.BRANCH_ADMIN and user.branch:

        response_data["branch_id"] = user.branch.id

        response_data["college_id"] = user.branch.college_id
 
    # If College Admin → include college_id

    if user.role == UserRole.COLLEGE_ADMIN and user.college:

        response_data["college_id"] = user.college.id
 
    # Update last login timestamp

    user.last_login = datetime.datetime.utcnow()

    db.commit()
 
    return response_data

 