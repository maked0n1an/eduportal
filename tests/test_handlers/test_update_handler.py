from uuid import uuid4

import pytest
from httpx import AsyncClient


async def test_update_user(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Vlad",
        "surname": "Zelenka",
        "email": "zvlad@gmail.com",
        "is_active": True,
    }
    user_data_updated = {
        "name": "Ivan",
        "surname": "Zolotoverkh",
        "email": "cheburek@kek.com",
    }
    await create_user_in_database(**user_data)

    response = await client.patch(
        "/user/",
        params={"user_id": user_data["user_id"]},
        json=user_data_updated,
    )
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["updated_user_id"] == str(user_data["user_id"])
    users_from_db = await get_user_from_database(user_data["user_id"])
    user_from_db = dict(users_from_db[0])

    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert user_from_db["is_active"] == user_data["is_active"]
    assert user_from_db["user_id"] == user_data["user_id"]


async def test_update_only_one_user(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jackson",
        "email": "mjackson@mail.com",
        "is_active": True,
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Steve",
        "surname": "Harris",
        "email": "sharris@gmail.com",
        "is_active": True,
    }
    user_data_3 = {
        "user_id": uuid4(),
        "name": "Don",
        "surname": "Huan",
        "email": "donhuan@gmail.com",
        "is_active": True,
    }
    user_data_updated = {
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
    }
    for user_data in [user_data_1, user_data_2, user_data_3]:
        await create_user_in_database(**user_data)

    response = await client.patch(
        "/user/",
        params={"user_id": user_data_1["user_id"]},
        json=user_data_updated,
    )
    assert response.status_code == 200
    response_data = response.json()

    assert response_data["updated_user_id"] == str(user_data_1["user_id"])
    user_1_from_db = await get_user_from_database(user_data_1["user_id"])
    user_from_db = dict(user_1_from_db[0])
    assert user_from_db["user_id"] == user_data_1["user_id"]
    assert user_from_db["name"] == user_data_updated["name"]
    assert user_from_db["surname"] == user_data_updated["surname"]
    assert user_from_db["email"] == user_data_updated["email"]
    assert user_from_db["is_active"] is user_data_1["is_active"]

    user_2_from_db = await get_user_from_database(user_data_2["user_id"])
    user_from_db = dict(user_2_from_db[0])
    assert user_from_db["user_id"] == user_data_2["user_id"]
    assert user_from_db["name"] == user_data_2["name"]
    assert user_from_db["surname"] == user_data_2["surname"]
    assert user_from_db["email"] == user_data_2["email"]
    assert user_from_db["is_active"] == user_data_2["is_active"]

    user_3_from_db = await get_user_from_database(user_data_3["user_id"])
    user_from_db = dict(user_3_from_db[0])
    assert user_from_db["user_id"] == user_data_3["user_id"]
    assert user_from_db["name"] == user_data_3["name"]
    assert user_from_db["surname"] == user_data_3["surname"]
    assert user_from_db["email"] == user_data_3["email"]
    assert user_from_db["is_active"] == user_data_3["is_active"]


@pytest.mark.parametrize(
    "user_data_updated, expected_status_code, expected_detail",
    [
        (
            {},
            422,
            {
                "detail": "At least one parameter for user update info should be provided"
            },
        ),
        (
            {"name": "123"},
            422,
            {"detail": "Name should contains only letters"},
        ),
        (
            {"surname": "123"},
            422,
            {"detail": "Surname should contains only letters"},
        ),
        (
            {"email": ""},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "",
                        "ctx": {
                            "reason": "An email address must have an @-sign."
                        },
                    }
                ]
            },
        ),
        (
            {"surname": ""},
            422,
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "surname"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ]
            },
        ),
        (
            {"name": ""},
            422,
            {
                "detail": [
                    {
                        "type": "string_too_short",
                        "loc": ["body", "name"],
                        "msg": "String should have at least 1 character",
                        "input": "",
                        "ctx": {"min_length": 1},
                    }
                ]
            },
        ),
        (
            {"email": "123"},
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "123",
                        "ctx": {
                            "reason": "An email address must have an @-sign."
                        },
                    }
                ]
            },
        ),
    ],
)
async def test_update_user_validation_error(
    client: AsyncClient,
    create_user_in_database,
    user_data_updated,
    expected_status_code,
    expected_detail,
):
    user_data = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    response = await client.patch(
        "/user/",
        params={"user_id": user_data["user_id"]},
        json=user_data_updated,
    )
    response_data = response.json()

    assert response.status_code == expected_status_code
    assert response_data == expected_detail


async def test_update_user_id_validation_error(client: AsyncClient):
    user_data_updated = {
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
    }

    response = await client.patch(
        "/user/", params={"user_id": 123}, json=user_data_updated
    )
    data_from_response = response.json()

    assert response.status_code == 422
    assert data_from_response == {
        "detail": [
            {
                "type": "uuid_parsing",
                "loc": ["query", "user_id"],
                "msg": "Input should be a valid UUID, invalid length: expected length 32 for simple format, found 3",
                "input": "123",
                "ctx": {
                    "error": "invalid length: expected length 32 for simple format, found 3"
                },
            }
        ]
    }


async def test_update_user_not_found_error(client: AsyncClient):
    user_data_updated = {
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
    }
    user_id = uuid4()

    response = await client.patch(
        "/user/", params={"user_id": user_id}, json=user_data_updated
    )
    response_data = response.json()
    assert response.status_code == 404
    assert response_data == {"detail": f"User with id {user_id} not found."}


async def test_update_user_duplicate_email_error(
    client: AsyncClient, create_user_in_database
):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jackson",
        "email": "mjackson@mail.com",
        "is_active": True,
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Steve",
        "surname": "Harris",
        "email": "sharris@gmail.com",
        "is_active": True,
    }
    user_data_updated = {
        "email": user_data_2["email"],
    }

    for user_data in [user_data_1, user_data_2]:
        await create_user_in_database(**user_data)

    response = await client.patch(
        "/user/",
        params={"user_id": user_data_1["user_id"]},
        json=user_data_updated,
    )

    assert response.status_code == 503
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in response.json()["detail"]
    )
