from fastapi import APIRouter

from app.api.v1 import auth, courses, enrollments, lessons

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(courses.router)
api_router.include_router(lessons.router)
api_router.include_router(enrollments.router)