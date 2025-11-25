from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
import os
import PyPDF2
from fastapi import Query
from src.db.database import get_db
from src.db.models import User, UserRole, Student, Branch, College, StudentMarks, Subject, StudentCourse
from src.db.models import Student, Branch
from src.db.models import User, UserRole, College, Student, Branch
router = APIRouter(prefix="/student", tags=["Student"])


def get_student_user(db: Session, user_id: int) -> User:
    user = db.query(User).filter(User.id == user_id).first()
    if not user or user.role != UserRole.STUDENT:
        raise HTTPException(status_code=403, detail="Only Student can access this dashboard")
    return user


@router.get("/dashboard")
def student_dashboard(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = get_student_user(db, user_id)

    student = db.query(Student).filter(Student.user_id == user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    branch = db.query(Branch).filter(Branch.id == student.branch_id).first()
    college = db.query(College).filter(College.id == student.college_id).first()

    # Marks per subject
    subject_marks = db.query(
        Subject.subject_name,
        Subject.total_marks,
        StudentMarks.marks_obtained,
        StudentMarks.percentage
    ).join(StudentMarks, Subject.id == StudentMarks.subject_id)\
     .filter(StudentMarks.student_id == student.id).all()

    marks_list = [
        {
            "subject": sub,
            "marks_obtained": mo,
            "total_marks": tm,
            "percentage": pct
        }
        for sub, tm, mo, pct in subject_marks
    ]

    # Course Progress
    course_progress = db.query(
        StudentCourse.course_id,
        StudentCourse.is_completed,
        StudentCourse.course_percentage
    ).filter(StudentCourse.student_id == student.id).all()

    course_stats = [
        {"course_id": c_id, "completed": completed, "percentage": pct}
        for c_id, completed, pct in course_progress
    ]

    return {
        "student_name": f"{student.first_name} {student.last_name}",
        "roll_number": student.roll_number,
        "branch": branch.branch_name,
        "college": college.college_name,
        "collage_city":college.city,
        "collage_state":college.state,        
        "current_year": student.current_year,
        "cgpa": student.cgpa,
        "total_subjects": len(marks_list),
        "subject_marks": marks_list,
        "course_progress": course_stats,
    }






PDF_FILE_PATH = r"BE_Complete_Documentation.pdf"


@router.get("/read-material")
def read_pdf_material():
    file_path = PDF_FILE_PATH

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="PDF not found")

    try:
        with open(file_path, "rb") as pdf_file:
            reader = PyPDF2.PdfReader(pdf_file)
            extracted_text = ""

            for page in reader.pages:
                extracted_text += page.extract_text() or ""

        return {
            "file_name": "BE_Complete_Documentation.pdf",
            "content": extracted_text.strip()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading PDF: {str(e)}")
