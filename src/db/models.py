from datetime import datetime
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Float, Enum, ForeignKey, UniqueConstraint, Index, Text
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()



class UserRole(enum.Enum):
    APP_ADMIN = "app_admin"
    COLLEGE_ADMIN = "college_admin"
    BRANCH_ADMIN = "branch_admin"
    STUDENT = "student"

class BranchType(enum.Enum):
    CSE = "cse"
    ECE = "ece"
    AIML = "aiml"
    MECHANICAL = "mechanical"
    CIVIL = "civil"

# ============= MODELS =============

class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        UniqueConstraint("email", name="uq_user_email"),
        Index("idx_user_email", "email"),
        Index("idx_user_role", "role"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(15))
    role = Column(Enum(UserRole), nullable=False)
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    college = relationship("College", uselist=False, back_populates="college_admin")
    branch = relationship("Branch", uselist=False, back_populates="branch_admin")
    student = relationship("Student", uselist=False, back_populates="user")


class College(Base):
    __tablename__ = "college"
    __table_args__ = (
        UniqueConstraint("college_code", name="uq_college_code"),
        Index("idx_college_name", "college_name"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    college_name = Column(String(255), nullable=False)
    college_code = Column(String(50), nullable=False, unique=True)
    city = Column(String(100))
    state = Column(String(100))
    phone = Column(String(15))
    email = Column(String(255))
    website = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    college_admin_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    college_admin = relationship("User", back_populates="college", foreign_keys=[college_admin_id])

    branches = relationship("Branch", back_populates="college", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="college", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branch"
    __table_args__ = (
        UniqueConstraint("college_id", "branch_type", name="uq_college_branch"),
        Index("idx_branch_college_id", "college_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    college_id = Column(Integer, ForeignKey("college.id", ondelete="CASCADE"), nullable=False)
    branch_type = Column(Enum(BranchType), nullable=False)
    branch_name = Column(String(100), nullable=False)
    hod_name = Column(String(255))
    hod_email = Column(String(255))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch_admin_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"))
    branch_admin = relationship("User", back_populates="branch", foreign_keys=[branch_admin_id])

    college = relationship("College", back_populates="branches")
    courses = relationship("Course", back_populates="branch", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="branch")


class Course(Base):
    __tablename__ = "course"
    __table_args__ = (
        UniqueConstraint("branch_id", "year", "course_name", name="uq_course_unique"),
        Index("idx_course_branch_id", "branch_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    branch_id = Column(Integer, ForeignKey("branch.id", ondelete="CASCADE"), nullable=False)
    course_name = Column(String(255), nullable=False)
    year = Column(Integer, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    branch = relationship("Branch", back_populates="courses")
    subjects = relationship("Subject", back_populates="course", cascade="all, delete-orphan")
    student_courses = relationship("StudentCourse", back_populates="course", cascade="all, delete-orphan")


class Subject(Base):
    __tablename__ = "subject"
    __table_args__ = (
        UniqueConstraint("course_id", "subject_name", name="uq_course_subject"),
        Index("idx_subject_course_id", "course_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    subject_name = Column(String(255), nullable=False)
    total_marks = Column(Float, nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    course = relationship("Course", back_populates="subjects")
    marks = relationship("StudentMarks", back_populates="subject", cascade="all, delete-orphan")


class Student(Base):
    __tablename__ = "student"
    __table_args__ = (
        UniqueConstraint("college_id", "roll_number", name="uq_college_student_roll"),
        Index("idx_student_college_id", "college_id"),
        Index("idx_student_branch_id", "branch_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False, unique=True)
    college_id = Column(Integer, ForeignKey("college.id", ondelete="CASCADE"), nullable=False)
    branch_id = Column(Integer, ForeignKey("branch.id", ondelete="CASCADE"), nullable=False)
    roll_number = Column(String(50), nullable=False)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(DateTime)
    gender = Column(String(20))
    current_year = Column(Integer, default=1)
    cgpa = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="student")
    college = relationship("College", back_populates="students")
    branch = relationship("Branch", back_populates="students")
    student_courses = relationship("StudentCourse", back_populates="student", cascade="all, delete-orphan")
    student_marks = relationship("StudentMarks", back_populates="student", cascade="all, delete-orphan")


class StudentCourse(Base):
    __tablename__ = "student_course"
    __table_args__ = (
        UniqueConstraint("student_id", "course_id", name="uq_student_course"),
        Index("idx_student_course_student_id", "student_id"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False)
    enrolled_at = Column(DateTime, default=datetime.utcnow)
    is_completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    course_percentage = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="student_courses")
    course = relationship("Course", back_populates="student_courses")


class StudentMarks(Base):
    __tablename__ = "student_marks"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", name="uq_student_subject_marks"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    student_id = Column(Integer, ForeignKey("student.id", ondelete="CASCADE"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subject.id", ondelete="CASCADE"), nullable=False)
    marks_obtained = Column(Float, nullable=False)
    percentage = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = relationship("Student", back_populates="student_marks")
    subject = relationship("Subject", back_populates="marks")
