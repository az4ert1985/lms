import uuid

from fastapi import APIRouter, status

from app.api.dependencies import CurrentUser, DBSession, build_module_service
from app.schemas.module import ModuleCreate, ModuleResponse

router = APIRouter(prefix="/courses/{course_id}/modules", tags=["Modules"])


@router.post(
    "/",
    response_model=ModuleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_module(
    course_id: uuid.UUID,
    payload: ModuleCreate,
    db: DBSession,
    current_user: CurrentUser,
) -> ModuleResponse:
    module = await build_module_service(db).create_module(
        course_id,
        payload,
        current_user,
    )
    return ModuleResponse.model_validate(module)


@router.get("/", response_model=list[ModuleResponse])
async def list_modules(
    course_id: uuid.UUID,
    db: DBSession,
    current_user: CurrentUser,
) -> list[ModuleResponse]:
    modules = await build_module_service(db).list_modules(
        course_id,
        current_user,
    )
    return [ModuleResponse.model_validate(module) for module in modules]
