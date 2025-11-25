# src/api/app_admin_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func
from src.db.models import User, UserRole, College, Student, Branch
from src.db.database import get_db
from src.db.models import User, UserRole, College
from src.schemas.user_schema import AppAdminRegisterSchema, CollegeAdminCreateSchema
from src.schemas.college_schema import CollegeCreateSchema
from passlib.context import CryptContext

router = APIRouter(prefix="/app-admin", tags=["App Admin"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_app_admin(db: Session, app_admin_id: int) -> User:
    user = db.query(User).filter(User.id == app_admin_id).first()
    if not user or user.role != UserRole.APP_ADMIN:
        raise HTTPException(status_code=403, detail="Only App Admin can perform this action")
    return user


@router.post("/register")
def register_app_admin(payload: AppAdminRegisterSchema, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            phone=payload.phone,
            role=UserRole.APP_ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to register App Admin")

    return {"message": "App admin registered", "user_id": user.id}


@router.post("/colleges")
def create_college(
    payload: CollegeCreateSchema,
    app_admin_id: int,
    db: Session = Depends(get_db),
):
    _ = get_app_admin(db, app_admin_id)

    # Duplicate college code check
    existing_college = db.query(College).filter(
        College.college_code == payload.college_code
    ).first()

    if existing_college:
        raise HTTPException(
            status_code=400,
            detail=f"College with code '{payload.college_code}' already exists"
        )

    try:
        college = College(
            college_name=payload.college_name,
            college_code=payload.college_code,
            city=payload.city,
            state=payload.state,
            phone=payload.phone,
            email=payload.email,
            website=payload.website,
        )
        db.add(college)
        db.commit()
        db.refresh(college)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create college")

    return {"message": "College created", "college_id": college.id}


@router.post("/college-admins")
def create_college_admin(
    payload: CollegeAdminCreateSchema,
    app_admin_id: int,
    db: Session = Depends(get_db),
):
    _ = get_app_admin(db, app_admin_id)

    college = db.query(College).filter(College.id == payload.college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    # Duplicate email validation
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    try:
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            phone=payload.phone,
            role=UserRole.COLLEGE_ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        college.college_admin_id = user.id
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=500, detail="Failed to create college admin"
        )

    return {
        "message": "College admin created and assigned",
        "college_admin_id": user.id,
        "college_id": payload.college_id,
    }

@router.get("/colleges")
def list_colleges(app_admin_id: int, db: Session = Depends(get_db)):
    _ = get_app_admin(db, app_admin_id)

    colleges = (
        db.query(
            College.id,
            College.college_name,
            College.college_code,
            College.city,
            College.state,
            College.phone,
            College.email,
            College.college_admin_id,
            func.count(Student.id).label("total_students"),
            func.count(Branch.id).label("total_branches")
        )
        .outerjoin(Student, Student.college_id == College.id)
        .outerjoin(Branch, Branch.college_id == College.id)
        .group_by(College.id)
        .all()
    )

    response = []
    for c in colleges:
        response.append({
            "college_id": c.id,
            "college_name": c.college_name,
            "college_code": c.college_code,
            "location": f"{c.city}, {c.state}",
            "phone": c.phone,
            "email": c.email,
            "total_students": c.total_students,
            "total_branches": c.total_branches,
            "college_admin_assigned": True if c.college_admin_id else False
        })

    return {"colleges": response}


@router.get("/college-admins/{college_id}")
def get_college_admin_info(college_id: int, app_admin_id: int, db: Session = Depends(get_db)):
    _ = get_app_admin(db, app_admin_id)

    college = db.query(College).filter(College.id == college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    admin_user = None
    if college.college_admin_id:
        user = db.query(User).filter(User.id == college.college_admin_id).first()
        admin_user = {
            "admin_id": user.id,
            "email": user.email,
            "phone": user.phone
        }

    return {
        "college_id": college.id,
        "college_name": college.college_name,
        "college_code": college.college_code,
        "college_admin": admin_user
    }
