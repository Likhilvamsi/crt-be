from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func

from src.db.database import get_db
from src.db.models import User, UserRole, College, Branch, Student
from src.schemas.branch_schema import BranchCreateSchema
from src.schemas.user_schema import BranchAdminCreateSchema
from passlib.context import CryptContext

router = APIRouter(prefix="/college-admin", tags=["College Admin"])

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_college_admin(db: Session, college_admin_id: int) -> User:
    user = db.query(User).filter(User.id == college_admin_id).first()
    if not user or user.role != UserRole.COLLEGE_ADMIN:
        raise HTTPException(status_code=403, detail="Only College Admin can perform this action")
    return user


# Create Branch
@router.post("/branches")
def create_branch(
    payload: BranchCreateSchema,
    college_admin_id: int,
    db: Session = Depends(get_db),
):
    admin = get_college_admin(db, college_admin_id)

    college = db.query(College).filter(College.id == payload.college_id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")
    if college.college_admin_id != admin.id:
        raise HTTPException(status_code=403, detail="Not authorized for this college")

    # Duplicate branch validation
    existing_branch = db.query(Branch).filter(
        Branch.college_id == payload.college_id,
        Branch.branch_type == payload.branch_type
    ).first()

    if existing_branch:
        raise HTTPException(
            status_code=400,
            detail=f"{payload.branch_type.value.upper()} branch already exists for this college"
        )

    try:
        branch = Branch(
            college_id=payload.college_id,
            branch_type=payload.branch_type,
            branch_name=payload.branch_name,
            hod_name=payload.hod_name,
            hod_email=payload.hod_email,
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create branch")

    return {"message": "Branch created successfully", "branch_id": branch.id}


# Create Branch Admin
@router.post("/branch-admins")
def create_branch_admin(
    payload: BranchAdminCreateSchema,
    college_admin_id: int,
    db: Session = Depends(get_db),
):
    admin = get_college_admin(db, college_admin_id)

    branch = db.query(Branch).filter(Branch.id == payload.branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if branch.college.college_admin_id != admin.id:
        raise HTTPException(status_code=403, detail="Not authorized for this branch")

    # Duplicate email check
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    try:
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            phone=payload.phone,
            role=UserRole.BRANCH_ADMIN,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        branch.branch_admin_id = user.id
        db.commit()

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create branch admin")

    return {
        "message": "Branch admin added successfully",
        "branch_admin_id": user.id,
        "branch_id": branch.id
    }


# College Dashboard API
@router.get("/dashboard")
def college_dashboard(
    college_admin_id: int,
    db: Session = Depends(get_db)
):
    admin = get_college_admin(db, college_admin_id)

    college = db.query(College).filter(College.college_admin_id == admin.id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    # Total students in the college
    total_students = db.query(func.count(Student.id))\
        .filter(Student.college_id == college.id).scalar()

    # Student Performance List
    students_query = db.query(
        Student.first_name,
        Student.last_name,
        Student.roll_number,
        Branch.branch_name,
        Student.current_year,
        Student.cgpa
    ).join(Branch, Branch.id == Student.branch_id)\
     .filter(Student.college_id == college.id)\
     .order_by(Student.cgpa.desc()).all()

    student_performance = [
        {
            "student_name": f"{fn} {ln}",
            "roll_number": roll,
            "branch_name": branch,
            "current_year": year,
            "cgpa": cgpa
        }
        for fn, ln, roll, branch, year, cgpa in students_query
    ]

    # Students per Branch
    students_per_branch_query = db.query(
        Branch.branch_name,
        func.count(Student.id)
    ).outerjoin(Student, Branch.id == Student.branch_id)\
     .filter(Branch.college_id == college.id)\
     .group_by(Branch.id).all()

    students_per_branch = [
        {"branch_name": b, "student_count": c} for b, c in students_per_branch_query
    ]

    # Students per Year
    students_per_year_query = db.query(
        Student.current_year,
        func.count(Student.id)
    ).filter(Student.college_id == college.id)\
     .group_by(Student.current_year).all()

    students_per_year = [
        {"year": y, "student_count": c} for y, c in students_per_year_query
    ]

    # Overall college CGPA
    average_cgpa = db.query(func.avg(Student.cgpa))\
        .filter(Student.college_id == college.id).scalar() or 0.0

    return {
        "college_name": college.college_name,
        "collage_id" : college.id,
        "total_students": total_students,
        "average_cgpa": round(average_cgpa, 2),
        "students_per_branch": students_per_branch,
        "students_per_year": students_per_year,
        "student_performance_list": student_performance,
    }
 

@router.get("/branches")
def get_college_branches(
    college_admin_id: int,
    db: Session = Depends(get_db)
):
    admin = get_college_admin(db, college_admin_id)

    college = db.query(College).filter(College.college_admin_id == admin.id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    branches = db.query(Branch).filter(Branch.college_id == college.id).all()

    return {
        "college_id": college.id,
        "college_name": college.college_name,
        "total_branches": len(branches),
        "branches": [
            {
                "branch_id": b.id,
                "branch_name": b.branch_name,
                "branch_type": b.branch_type.value,
                "hod_name": b.hod_name,
                "is_active": b.is_active,
            }
            for b in branches
        ]
    }

@router.get("/branch-admins")
def get_all_branch_admins(
    college_admin_id: int,
    db: Session = Depends(get_db)
):
    admin = get_college_admin(db, college_admin_id)

    college = db.query(College).filter(College.college_admin_id == admin.id).first()
    if not college:
        raise HTTPException(status_code=404, detail="College not found")

    branches = db.query(Branch).filter(Branch.college_id == college.id).all()

    data = []
    for branch in branches:
        admin_user = None
        if branch.branch_admin_id:
            user = db.query(User).filter(User.id == branch.branch_admin_id).first()
            admin_user = {
                "admin_id": user.id,
                "email": user.email,
                "phone": user.phone
            }

        data.append({
            "branch_id": branch.id,
            "branch_name": branch.branch_name,
            "branch_type": branch.branch_type.value,
            "branch_admin": admin_user
        })

    return {
        "college_id": college.id,
        "college_name": college.college_name,
        "branches_with_admins": data
    }
