"""
API v1 router aggregator.
All v1 sub-routers are registered here.
"""

from fastapi import APIRouter

from app.api.v1 import ai_results, auth, groups, homeworks, submissions, group_members

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(groups.router)
router.include_router(group_members.router)
router.include_router(homeworks.router)
router.include_router(submissions.router)
router.include_router(ai_results.router)
