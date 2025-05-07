from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.db.models import PortalRole
from tests.conftest import create_test_auth_header_for_user


async def test_add_admin_role_to_user_by_superadmin(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_to_promote = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
        "roles": [PortalRole.USER],
    }
    user_who_promote = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
        "roles": [PortalRole.SUPERADMIN],
    }
    for user_data in [user_to_promote, user_who_promote]:
        await create_user_in_database(**user_data)
    resp = await client.patch(
        "/user/admin_privilege",
        params={"user_id": user_to_promote["user_id"]},
        headers=create_test_auth_header_for_user(user_who_promote["email"]),
    )
    data_from_resp = resp.json()

    assert resp.status_code == 200
    db_users = await get_user_from_database(data_from_resp["updated_user_id"])
    assert len(db_users) == 1
    updated_user = dict(db_users[0])
    assert updated_user["user_id"] == user_to_promote["user_id"]
    assert PortalRole.ADMIN in updated_user["roles"]


async def test_revoke_admin_role_from_user_by_superadmin(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_data_for_revoke = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
        "roles": [PortalRole.USER, PortalRole.ADMIN],
    }
    user_data_who_revoke = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
        "roles": [PortalRole.SUPERADMIN],
    }
    for user_data in [user_data_for_revoke, user_data_who_revoke]:
        await create_user_in_database(**user_data)
    resp = await client.delete(
        "/user/admin_privilege",
        params={"user_id": user_data_for_revoke["user_id"]},
        headers=create_test_auth_header_for_user(user_data_who_revoke["email"]),
    )
    data_from_resp = resp.json()
    assert resp.status_code == 200
    db_users = await get_user_from_database(data_from_resp["updated_user_id"])
    assert len(db_users) == 1
    revoked_user_from_dbs = dict(db_users[0])
    assert revoked_user_from_dbs["user_id"] == user_data_for_revoke["user_id"]
    assert PortalRole.ADMIN not in revoked_user_from_dbs["roles"]


@pytest.mark.parametrize(
    "current_user_roles",
    [
        pytest.param(
            [PortalRole.USER, PortalRole.ADMIN],
            id="admin_attempts_to_revoke_another_admin",
        ),
        pytest.param(
            [PortalRole.USER], id="regular_user_attempts_to_revoke_another_admin"
        ),
    ],
)
async def test_prevent_unauthorized_admin_role_revocation(
    client: AsyncClient,
    create_user_in_database,
    get_user_from_database,
    current_user_roles,
):
    user_who_revoke = {
        "user_id": uuid4(),
        "name": "Ivan",
        "surname": "Ivanov",
        "email": "ivan@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
        "roles": current_user_roles,
    }
    user_to_revoke = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashedPass",
        "roles": [PortalRole.USER, PortalRole.ADMIN],
    }
    for user_data in [user_who_revoke, user_to_revoke]:
        await create_user_in_database(**user_data)

    resp = await client.delete(
        "/user/admin_privilege",
        params={"user_id": user_to_revoke["user_id"]},
        headers=create_test_auth_header_for_user(user_who_revoke["email"]),
    )
    data_from_resp = resp.json()

    assert resp.status_code == 403
    assert data_from_resp == {"detail": "Forbidden."}
    not_revoked_user_from_db = await get_user_from_database(user_to_revoke["user_id"])
    assert len(not_revoked_user_from_db) == 1
    not_revoked_user_from_db = dict(not_revoked_user_from_db[0])
    assert not_revoked_user_from_db["user_id"] == user_to_revoke["user_id"]
    assert PortalRole.ADMIN in not_revoked_user_from_db["roles"]
