from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.conftest import create_user_in_database, get_user_from_database

USER_DATA = [
    {"name": "Michael", "surname": "Jackson", "email": "mijackson@gmail.com"},
    {"name": "Donald", "surname": "Trump", "email": "donny@maga.com"},
    {"name": "Don", "surname": "Huan", "email": "dhuan@rambler.com"},
]


@pytest.mark.parametrize("user", USER_DATA)
async def test_create_user_parametrise(client: AsyncClient, user: dict):
    response = await client.post("/user/", json=user)
    data = response.json()

    assert response.status_code == 200
    assert data["user_id"] is not None
    assert data["name"] == user["name"]
    assert data["surname"] == user["surname"]
    assert data["email"] == user["email"]
    assert data["is_active"] == True


async def test_create_user(client: AsyncClient, get_user_from_database):
    user_data = {
        "name": "Alex",
        "surname": "Sokol",
        "email": "nice@example.com",
    }

    response = await client.post("/user/", json=user_data)
    data_from_resp = response.json()

    assert response.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True
    users_from_db = await get_user_from_database(data_from_resp["user_id"])
    assert len(users_from_db) == 1
    user_from_db = dict(users_from_db[0])
    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is True
    assert str(user_from_db["user_id"]) == data_from_resp["user_id"]


async def test_create_and_get_user(client: AsyncClient):
    response = await client.post(
        "/user/",
        json={
            "name": "Mykola",
            "surname": "Shevchenko",
            "email": "sheva@example.com",
        },
    )
    data_from_resp = response.json()

    assert response.status_code == 200
    assert data_from_resp["user_id"] is not None
    assert data_from_resp["name"] == "Mykola"
    assert data_from_resp["surname"] == "Shevchenko"
    assert data_from_resp["email"] == "sheva@example.com"
    assert data_from_resp["is_active"] == True

    response = await client.get(
        "/user/by-email", params={"email": "sheva@example.com"}
    )
    user_json = response.json()

    assert response.status_code == 200
    assert user_json["user_id"] == data_from_resp["user_id"]
    assert user_json["name"] == data_from_resp["name"]
    assert user_json["surname"] == data_from_resp["surname"]
    assert user_json["email"] == data_from_resp["email"]
    assert user_json["is_active"] == data_from_resp["is_active"]


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
    resp_data = response.json()
    assert resp_data["updated_user_id"] == str(user_data["user_id"])
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
    resp_data = response.json()

    assert resp_data["updated_user_id"] == str(user_data_1["user_id"])
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


async def test_delete_user(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Alex",
        "surname": "Shevchenko",
        "email": "lol@kek.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    response = await client.delete(
        "/user/", params={"user_id": user_data["user_id"]}
    )
    assert response.status_code == 200
    assert response.json() == {"deleted_user_id": str(user_data["user_id"])}

    user_from_db = await get_user_from_database(user_data["user_id"])
    user_from_db = dict(user_from_db[0])

    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is False
    assert user_from_db["user_id"] == user_data["user_id"]


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
        "name": "Alex",
        "surname": "Sheva",
        "email": "nice@kek.com",
        "is_active": True,
    }
    await create_user_in_database(**user_data)
    resp = await client.patch(
        "/user/",
        params={"user_id": user_data["user_id"]},
        json=user_data_updated,
    )
    assert resp.status_code == expected_status_code
    resp_data = resp.json()
    assert resp_data == expected_detail
