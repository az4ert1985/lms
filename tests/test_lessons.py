from uuid import uuid4

import pytest
from app.api.dependencies import build_lesson_service
from app.api.v1 import lessons
from app.db.models import UserRole
from app.schemas.lesson import LessonCreate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_lesson_module_not_found(
    fake_db,
    make_user,
    make_result,
) -> None:
    fake_db.execute.return_value = make_result(one=None)

    with pytest.raises(HTTPException) as exc:
        await lessons.create_lesson(
            uuid4(),
            LessonCreate(title="Lesson"),
            build_lesson_service(fake_db),
            make_user(),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_lesson_forbidden(
    fake_db,
    make_user,
    make_course,
    make_module,
    make_result,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    module = make_module(course.id)
    fake_db.execute.return_value = make_result(one=(module, course))

    with pytest.raises(HTTPException) as exc:
        await lessons.create_lesson(
            module.id,
            LessonCreate(title="Lesson"),
            build_lesson_service(fake_db),
            user,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_create_lesson_success(
    fake_db,
    make_user,
    make_course,
    make_module,
    make_result,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(user.id)
    module = make_module(course.id)
    fake_db.execute.return_value = make_result(one=(module, course))

    async def refresh(lesson) -> None:
        lesson.id = uuid4()

    fake_db.refresh.side_effect = refresh

    response = await lessons.create_lesson(
        module.id,
        LessonCreate(title="Lesson", content="Content", position=1),
        build_lesson_service(fake_db),
        user,
    )

    assert response.title == "Lesson"
    assert response.module_id == module.id
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_list_lessons_module_not_found(
    fake_db,
    make_user,
    make_result,
) -> None:
    fake_db.execute.return_value = make_result(one=None)

    with pytest.raises(HTTPException) as exc:
        await lessons.list_lessons(uuid4(), build_lesson_service(fake_db), make_user())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_lessons_student_unpublished(
    fake_db,
    make_user,
    make_course,
    make_module,
    make_result,
) -> None:
    user = make_user(role=UserRole.STUDENT)
    course = make_course(uuid4(), is_published=False)
    module = make_module(course.id)
    fake_db.execute.return_value = make_result(one=(module, course))

    with pytest.raises(HTTPException) as exc:
        await lessons.list_lessons(module.id, build_lesson_service(fake_db), user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_lessons_teacher_forbidden(
    fake_db,
    make_user,
    make_course,
    make_module,
    make_result,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    module = make_module(course.id)
    fake_db.execute.return_value = make_result(one=(module, course))

    with pytest.raises(HTTPException) as exc:
        await lessons.list_lessons(module.id, build_lesson_service(fake_db), user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_list_lessons_success(
    fake_db,
    make_user,
    make_course,
    make_module,
    make_lesson,
    make_result,
) -> None:
    user = make_user(role=UserRole.ADMIN)
    course = make_course(uuid4())
    module = make_module(course.id)
    lesson = make_lesson(module.id)
    fake_db.execute.side_effect = [
        make_result(one=(module, course)),
        make_result(rows=[lesson]),
    ]

    response = await lessons.list_lessons(
        module.id, build_lesson_service(fake_db), user
    )

    assert len(response) == 1
    assert response[0].id == lesson.id
