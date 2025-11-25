# src/api/branch_admin_router.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from src.db.database import get_db
from src.db.models import User, UserRole, Branch, Course, Student
from src.schemas.course_schema import CourseCreateSchema
from src.schemas.student_schema import StudentCreateSchema
from passlib.context import CryptContext

router = APIRouter(prefix="/branch-admin", tags=["Branch Admin"])

# Use pbkdf2_sha256 instead of bcrypt for Windows & length safety
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def get_branch_admin(db: Session, branch_admin_id: int) -> User:
    user = db.query(User).filter(User.id == branch_admin_id).first()
    if not user or user.role != UserRole.BRANCH_ADMIN:
        raise HTTPException(status_code=403, detail="Only Branch Admin can perform this action")
    return user


@router.post("/courses")
def create_course(
    payload: CourseCreateSchema,
    branch_admin_id: int,
    db: Session = Depends(get_db),
):
    admin = get_branch_admin(db, branch_admin_id)

    branch = db.query(Branch).filter(Branch.id == payload.branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if branch.branch_admin_id != admin.id:
        raise HTTPException(status_code=403, detail="You are not admin of this branch")

    # Prevent duplicate course for same year & name in same branch
    existing_course = db.query(Course).filter(
        Course.branch_id == payload.branch_id,
        Course.course_name == payload.course_name,
        Course.year == payload.year,
    ).first()

    if existing_course:
        raise HTTPException(
            status_code=400,
            detail=f"Course '{payload.course_name}' for year {payload.year} already exists in this branch"
        )

    try:
        course = Course(
            branch_id=payload.branch_id,
            course_name=payload.course_name,
            year=payload.year,
            description=payload.description,
        )
        db.add(course)
        db.commit()
        db.refresh(course)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error inserting course")

    return {"message": "Course created", "course_id": course.id}


@router.post("/students")
def create_student(
    payload: StudentCreateSchema,
    branch_admin_id: int,
    db: Session = Depends(get_db),
):
    admin = get_branch_admin(db, branch_admin_id)

    branch = db.query(Branch).filter(Branch.id == payload.branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    if branch.branch_admin_id != admin.id:
        raise HTTPException(status_code=403, detail="You are not admin of this branch")

    # Duplicate user email check
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Duplicate roll number in same college check
    existing_roll = db.query(Student).filter(
        Student.college_id == payload.college_id,
        Student.roll_number == payload.roll_number
    ).first()
    if existing_roll:
        raise HTTPException(
            status_code=400,
            detail=f"Roll number '{payload.roll_number}' already exists in this college"
        )

    try:
        # Create User
        user = User(
            email=payload.email,
            password_hash=hash_password(payload.password),
            phone=payload.phone,
            role=UserRole.STUDENT,
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Create Student
        student = Student(
            user_id=user.id,
            college_id=payload.college_id,
            branch_id=payload.branch_id,
            roll_number=payload.roll_number,
            first_name=payload.first_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            current_year=payload.current_year,
        )
        db.add(student)
        db.commit()
        db.refresh(student)

    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Failed to create student")

    return {
        "message": "Student registered successfully",
        "student_id": student.id,
        "user_id": user.id,
    }


@router.get("/courses")
def get_branch_courses(
    branch_admin_id: int,
    db: Session = Depends(get_db),
):
    admin = get_branch_admin(db, branch_admin_id)

    branch = admin.branch
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found for this admin")

    courses = db.query(Course).filter(Course.branch_id == branch.id).all()

    return {
        "branch_id": branch.id,
        "branch_name": branch.branch_name,
        "total_courses": len(courses),
        "courses": [
            {
                "course_id": c.id,
                "course_name": c.course_name,
                "year": c.year,
                "description": c.description,
                "is_active": c.is_active,
            }
            for c in courses
        ],
    }


@router.get("/students")
def get_branch_students(
    branch_admin_id: int,
    db: Session = Depends(get_db),
):
    admin = get_branch_admin(db, branch_admin_id)

    branch = admin.branch
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found for this admin")

    students = db.query(Student).filter(Student.branch_id == branch.id).all()

    return {
        "branch_id": branch.id,
        "branch_name": branch.branch_name,
        "total_students": len(students),
        "students": [
            {
                "student_id": s.id,
                "roll_number": s.roll_number,
                "full_name": f"{s.first_name} {s.last_name}",
                "current_year": s.current_year,
                "gender": s.gender,
                "is_active": s.is_active,
            }
            for s in students
        ],
    }
