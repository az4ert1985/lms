from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dependencies import CurrentUser, DbSession
from app.models.course import Course, Lesson
from app.models.enrollment import Enrollment
from app.schemas.lesson import LessonCreate, LessonRead, LessonUpdate

router = APIRouter(tags=["Lessons"])


def get_course_or_404(db: Session, course_id: int) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    return course


def check_manager(course: Course, user) -> None:
    if not (user.role == "admin" or (user.role == "teacher" and course.owner_id == user.id)):
        raise HTTPException(status_code=403, detail="Forbidden")


def check_lesson_access(db: Session, course: Course, user) -> None:
    if user.role in {"admin"}:
        return
    if user.role == "teacher" and course.owner_id == user.id:
        return
    if user.role != "student" or not course.is_published:
        raise HTTPException(status_code=404, detail="Lesson not found")

    enrolled = db.scalar(
        select(Enrollment.id).where(
            Enrollment.student_id == user.id,
            Enrollment.course_id == course.id,
        )
    )
    if enrolled is None:
        raise HTTPException(status_code=403, detail="Enrollment required")


@router.get(
    "/courses/{course_id}/lessons",
    response_model=list[LessonRead],
)
def list_lessons(course_id: int, db: DbSession, user: CurrentUser):
    course = get_course_or_404(db, course_id)
    check_lesson_access(db, course, user)
    return list(
        db.scalars(
            select(Lesson).where(Lesson.course_id == course_id).order_by(Lesson.position, Lesson.id)
        ).all()
    )


@router.post(
    "/courses/{course_id}/lessons",
    response_model=LessonRead,
    status_code=status.HTTP_201_CREATED,
)
def create_lesson(
    course_id: int,
    payload: LessonCreate,
    db: DbSession,
    user: CurrentUser,
):
    course = get_course_or_404(db, course_id)
    check_manager(course, user)

    lesson = Lesson(course_id=course_id, **payload.model_dump())
    db.add(lesson)
    db.commit()
    db.refresh(lesson)
    return lesson


@router.patch("/lessons/{lesson_id}", response_model=LessonRead)
def update_lesson(
    lesson_id: int,
    payload: LessonUpdate,
    db: DbSession,
    user: CurrentUser,
):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    check_manager(lesson.course, user)

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(lesson, key, value)

    db.commit()
    db.refresh(lesson)
    return lesson


@router.delete(
    "/lessons/{lesson_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_lesson(lesson_id: int, db: DbSession, user: CurrentUser):
    lesson = db.get(Lesson, lesson_id)
    if lesson is None:
        raise HTTPException(status_code=404, detail="Lesson not found")

    check_manager(lesson.course, user)
    db.delete(lesson)
    db.commit()
    return None
