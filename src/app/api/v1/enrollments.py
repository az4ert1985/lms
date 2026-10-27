from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.dependencies import CurrentUser, DbSession
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.user import User
from app.schemas.enrollment import EnrollmentCreate, EnrollmentRead

router = APIRouter(prefix="/enrollments", tags=["Enrollments"])


@router.post(
    "",
    response_model=EnrollmentRead,
    status_code=status.HTTP_201_CREATED,
)
def enroll(payload: EnrollmentCreate, db: DbSession, user: CurrentUser):
    student_id = user.id

    if user.role == "admin":
        student_id = payload.student_id
    elif payload.student_id != user.id:
        raise HTTPException(status_code=403, detail="Forbidden")

    student = db.get(User, student_id)
    course = db.get(Course, payload.course_id)

    if student is None or student.role != "student":
        raise HTTPException(status_code=404, detail="Student not found")
    if not student.is_active:
        raise HTTPException(status_code=400, detail="Student is inactive")
    if course is None or not course.is_published:
        raise HTTPException(status_code=404, detail="Published course not found")

    existing = db.scalar(
        select(Enrollment).where(
            Enrollment.student_id == student_id,
            Enrollment.course_id == course.id,
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Already enrolled")

    enrollment = Enrollment(
        student_id=student_id,
        course_id=course.id,
    )
    db.add(enrollment)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Already enrolled",
        ) from None

    db.refresh(enrollment)
    return enrollment


@router.get("/me", response_model=list[EnrollmentRead])
def my_enrollments(db: DbSession, user: CurrentUser):
    return list(
        db.scalars(
            select(Enrollment)
            .where(Enrollment.student_id == user.id)
            .order_by(Enrollment.enrolled_at.desc())
        ).all()
    )
