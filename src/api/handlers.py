from logging import getLogger
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.actions.auth import get_current_user_from_token
from src.api.actions.user import (
    _create_new_user,
    _delete_user,
    _get_user_by_email,
    _get_user_by_id,
    _update_user,
    check_user_permissions,
)
from src.api.schemas import (
    UserCreate,
    UserDeletedResponse,
    UserGetByEmailRequest,
    UserShowResponse,
    UserUpdatedResponse,
    UserUpdateRequest,
)
from src.db.database import get_db_session
from src.db.models import UserEntity

logger = getLogger(__name__)
user_router = APIRouter()


@user_router.post("/", response_model=UserShowResponse)
async def create_user(body: UserCreate, db: AsyncSession = Depends(get_db_session)):
    try:
        return await _create_new_user(body, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")


@user_router.patch("/admin_privilege", response_model=UserUpdatedResponse)
async def grant_admin_privilege(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserEntity = Depends(get_current_user_from_token),
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Forbidden.")
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400, detail="Cannot manage privileges of itself."
        )

    user_to_promote = await _get_user_by_id(user_id, db)

    if user_to_promote is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    if user_to_promote.is_admin or user_to_promote.is_superadmin:
        raise HTTPException(
            status_code=409,
            detail=f"User with id {user_id} already promoted to admin / superadmin.",
        )

    updated_user_params = {"roles": user_to_promote.enrich_admin_roles_by_admin_role()}

    try:
        updated_user_id = await _update_user(user_id, updated_user_params, db)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UserUpdatedResponse(updated_user_id=updated_user_id)


@user_router.delete("/admin_privilege", response_model=UserUpdatedResponse)
async def revoke_admin_privilege(
    user_id: UUID,
    db: AsyncSession = Depends(get_db_session),
    current_user: UserEntity = Depends(get_current_user_from_token),
):
    if not current_user.is_superadmin:
        raise HTTPException(status_code=403, detail="Forbidden.")
    if current_user.user_id == user_id:
        raise HTTPException(
            status_code=400, detail="Cannot manage privileges of itself."
        )
    user_for_revoke_admin_privileges = await _get_user_by_id(user_id, db)

    if user_for_revoke_admin_privileges is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    if not user_for_revoke_admin_privileges.is_admin:
        raise HTTPException(
            status_code=409, detail=f"User with id {user_id} has no admin privileges."
        )

    updated_user_params = {
        "roles": user_for_revoke_admin_privileges.remove_admin_privileges_from_model()
    }
    try:
        updated_user_id = await _update_user(
            updated_user_params=updated_user_params, session=db, user_id=user_id
        )
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UserUpdatedResponse(updated_user_id=updated_user_id)


@user_router.get("/by-email")
async def get_user_by_email(
    body: UserGetByEmailRequest = Query(...),
    db_session: AsyncSession = Depends(get_db_session),
    current_user: UserEntity = Depends(get_current_user_from_token),
) -> UserShowResponse:
    return await _get_user_by_email(body, db_session)


@user_router.get("/")
async def get_user_by_id(
    user_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: UserEntity = Depends(get_current_user_from_token),
) -> UserShowResponse:
    user = await _get_user_by_id(user_id, db_session)
    if user is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )
    return user


@user_router.patch("/")
async def update_user_by_id(
    user_id: UUID,
    body: UserUpdateRequest,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: UserEntity = Depends(get_current_user_from_token),
) -> UserUpdatedResponse:
    updated_user_params = body.model_dump(exclude_unset=True)

    if updated_user_params == {}:
        raise HTTPException(
            status_code=422,
            detail="At least one parameter for user update info should be provided",
        )

    user_to_update = await _get_user_by_id(user_id, db_session)
    if user_to_update is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )

    if user_id != current_user.user_id:
        if check_user_permissions(
            target_user=user_to_update, current_user=current_user
        ):
            raise HTTPException(status_code=403, detail="Forbidden")

    try:
        updated_user_id = await _update_user(user_id, updated_user_params, db_session)
    except IntegrityError as err:
        logger.error(err)
        raise HTTPException(status_code=503, detail=f"Database error: {err}")
    return UserUpdatedResponse(updated_user_id=updated_user_id)


@user_router.delete("/")
async def delete_user_by_id(
    user_id: UUID,
    db_session: AsyncSession = Depends(get_db_session),
    current_user: UserEntity = Depends(get_current_user_from_token),
) -> UserDeletedResponse:
    user_to_delete = await _get_user_by_id(user_id, db_session)

    if user_to_delete is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )

    if not check_user_permissions(
        target_user=user_to_delete, current_user=current_user
    ):
        raise HTTPException(status_code=403, detail="Forbidden.")

    deleted_user_id = await _delete_user(user_id, db_session)
    if deleted_user_id is None:
        raise HTTPException(
            status_code=404, detail=f"User with id {user_id} not found."
        )

    return UserDeletedResponse(deleted_user_id=deleted_user_id)
