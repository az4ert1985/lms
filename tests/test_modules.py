from uuid import uuid4

import pytest
from app.api.dependencies import build_module_service
from app.api.v1 import modules
from app.db.models import UserRole
from app.schemas.module import ModuleCreate
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_create_module_success(
    fake_db,
    make_user,
    make_course,
    make_result,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(user.id)
    fake_db.execute.return_value = make_result(scalar=course)

    async def refresh(module) -> None:
        module.id = uuid4()

    fake_db.refresh.side_effect = refresh

    response = await modules.create_module(
        course.id,
        ModuleCreate(title="Python basics", position=1),
        build_module_service(fake_db),
        user,
    )

    assert response.title == "Python basics"
    assert response.course_id == course.id
    fake_db.add.assert_called_once()
    fake_db.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_module_course_not_found(
    fake_db,
    make_user,
    make_result,
) -> None:
    fake_db.execute.return_value = make_result(scalar=None)

    with pytest.raises(HTTPException) as exc:
        await modules.create_module(
            uuid4(),
            ModuleCreate(title="Module"),
            build_module_service(fake_db),
            make_user(),
        )

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_create_module_forbidden(
    fake_db,
    make_user,
    make_course,
    make_result,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await modules.create_module(
            course.id,
            ModuleCreate(title="Module"),
            build_module_service(fake_db),
            user,
        )

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_list_modules_course_not_found(
    fake_db,
    make_user,
    make_result,
) -> None:
    fake_db.execute.return_value = make_result(scalar=None)

    with pytest.raises(HTTPException) as exc:
        await modules.list_modules(uuid4(), build_module_service(fake_db), make_user())

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_modules_student_unpublished(
    fake_db,
    make_user,
    make_course,
    make_result,
) -> None:
    user = make_user(role=UserRole.STUDENT)
    course = make_course(uuid4(), is_published=False)
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await modules.list_modules(course.id, build_module_service(fake_db), user)

    assert exc.value.status_code == 404


@pytest.mark.asyncio
async def test_list_modules_teacher_forbidden(
    fake_db,
    make_user,
    make_course,
    make_result,
) -> None:
    user = make_user(role=UserRole.TEACHER)
    course = make_course(uuid4())
    fake_db.execute.return_value = make_result(scalar=course)

    with pytest.raises(HTTPException) as exc:
        await modules.list_modules(course.id, build_module_service(fake_db), user)

    assert exc.value.status_code == 403


@pytest.mark.asyncio
async def test_list_modules_success(
    fake_db,
    make_user,
    make_course,
    make_module,
    make_result,
) -> None:
    user = make_user(role=UserRole.ADMIN)
    course = make_course(uuid4())
    module = make_module(course.id)
    fake_db.execute.side_effect = [
        make_result(scalar=course),
        make_result(rows=[module]),
    ]

    response = await modules.list_modules(
        course.id, build_module_service(fake_db), user
    )

    assert len(response) == 1
    assert response[0].id == module.id
