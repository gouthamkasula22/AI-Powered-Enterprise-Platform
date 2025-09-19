"""

Exposed endpoints:
  GET /users/me  - current authenticated user info
  GET /users     - admin-only paginated list

Admin write/mutation operations live in `admin_users.py`.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from ....application.dto import UserDTO
from ....infrastructure.database.database import get_db_session
from ....infrastructure.database.repositories import SqlUserRepository
from ..dependencies.auth import get_current_user, require_admin

router = APIRouter(tags=["users"])


class CurrentUserResponse(BaseModel):
    id: int
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    display_name: Optional[str] = None
    profile_picture_url: Optional[str] = None
    bio: Optional[str] = None
    phone_number: Optional[str] = None
    date_of_birth: Optional[str] = None
    is_active: bool
    is_verified: bool
    is_staff: bool
    is_superuser: bool
    role: str
    timezone: Optional[str] = None
    locale: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    last_login: Optional[str] = None


class SimpleUserItem(BaseModel):
    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    is_active: bool
    created_at: Optional[str]
    last_login: Optional[str]


class UserListResponse(BaseModel):
    users: List[SimpleUserItem]
    total: int
    page: int
    per_page: int
    total_pages: int


async def get_user_repository(session: AsyncSession = Depends(get_db_session)) -> SqlUserRepository:
    return SqlUserRepository(session)


def _dt(dt) -> Optional[str]:  # helper avoids repeated pylance Optional warnings
    return dt.isoformat() if dt else None


@router.get("/me", response_model=CurrentUserResponse)
async def get_me(current_user: UserDTO = Depends(get_current_user)) -> CurrentUserResponse:
    return CurrentUserResponse(
        id=current_user.id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        display_name=current_user.display_name,
        profile_picture_url=current_user.profile_picture_url,
        bio=current_user.bio,
        phone_number=current_user.phone_number,
        date_of_birth=_dt(getattr(current_user, "date_of_birth", None)),
        is_active=current_user.is_active,
        is_verified=current_user.is_verified,
        is_staff=current_user.is_staff,
        is_superuser=current_user.is_superuser,
        role=(current_user.role.value.upper() if getattr(current_user, "role", None) else "USER"),
        timezone=current_user.timezone,
        locale=current_user.locale,
        created_at=_dt(getattr(current_user, "created_at", None)),
        updated_at=_dt(getattr(current_user, "updated_at", None)),
        last_login=_dt(getattr(current_user, "last_login", None)),
    )


@router.get("/", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    current_user: UserDTO = Depends(require_admin),
    user_repo: SqlUserRepository = Depends(get_user_repository),
):
    try:
        offset = (page - 1) * per_page
        users = await user_repo.list_users(limit=per_page, offset=offset, include_inactive=True)
        total = len(users)
        total_pages = (total + per_page - 1) // per_page
        items: List[SimpleUserItem] = []
        for u in users:
            if u.id is None:  # skip any anomalous rows lacking id
                continue
            items.append(
                SimpleUserItem(
                    id=u.id,
                    email=u.email.value if u.email else "",
                    first_name=u.first_name,
                    last_name=u.last_name,
                    role=(u.role.value.upper() if getattr(u, "role", None) else "USER"),
                    is_active=u.is_active,
                    created_at=_dt(getattr(u, "created_at", None)),
                    last_login=_dt(getattr(u, "last_login", None)),
                )
            )
        return UserListResponse(
            users=items,
            total=total,
            page=page,
            per_page=per_page,
            total_pages=total_pages,
        )
    except Exception as e:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list users: {e}",
        )


__all__ = ["router", "CurrentUserResponse", "SimpleUserItem", "UserListResponse"]