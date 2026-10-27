from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.course import Course
from app.models.user import User


def list_courses(
    db: Session,
    user: User,
    skip: int = 0,
    limit: int = 20,
) -> list[Course]:
    query = select(Course)

    if user.role == "student":
        query = query.where(Course.is_published.is_(True))

    return list(db.scalars(query.order_by(Course.id).offset(skip).limit(limit)).all())


def get_course(db: Session, course_id: int) -> Course | None:
    return db.get(Course, course_id)


def create_course(
    db: Session,
    owner_id: int,
    title: str,
    description: str | None,
) -> Course:
    course = Course(
        owner_id=owner_id,
        title=title,
        description=description,
    )
    db.add(course)
    db.commit()
    db.refresh(course)
    return course
