from fastapi import APIRouter, HTTPException, Query, status

from app.dependencies import CurrentUser, DbSession
from app.models.course import Course
from app.models.user import User
from app.schemas.course import CourseCreate, CourseDetail, CourseRead, CourseUpdate
from app.services.course_service import create_course, list_courses

router = APIRouter(prefix="/courses", tags=["Courses"])


def can_manage(course: Course, user: User) -> bool:
    return user.role == "admin" or (user.role == "teacher" and course.owner_id == user.id)


@router.get("", response_model=list[CourseRead])
def get_courses(
    db: DbSession,
    user: CurrentUser,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[Course]:
    return list_courses(db, user, skip, limit)


@router.post(
    "",
    response_model=CourseRead,
    status_code=status.HTTP_201_CREATED,
)
def post_course(
    payload: CourseCreate,
    db: DbSession,
    user: CurrentUser,
) -> Course:
    if user.role not in {"admin", "teacher"}:
        raise HTTPException(status_code=403, detail="Forbidden")

    return create_course(
        db,
        user.id,
        payload.title,
        payload.description,
    )


@router.get("/{course_id}", response_model=CourseDetail)
def get_course(course_id: int, db: DbSession, user: CurrentUser) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")

    if user.role == "student" and not course.is_published:
        raise HTTPException(status_code=404, detail="Course not found")

    return course


@router.patch("/{course_id}", response_model=CourseRead)
def patch_course(
    course_id: int,
    payload: CourseUpdate,
    db: DbSession,
    user: CurrentUser,
) -> Course:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if not can_manage(course, user):
        raise HTTPException(status_code=403, detail="Forbidden")

    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(course, key, value)

    db.commit()
    db.refresh(course)
    return course


@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(course_id: int, db: DbSession, user: CurrentUser) -> None:
    course = db.get(Course, course_id)
    if course is None:
        raise HTTPException(status_code=404, detail="Course not found")
    if not can_manage(course, user):
        raise HTTPException(status_code=403, detail="Forbidden")

    db.delete(course)
    db.commit()
    return None
