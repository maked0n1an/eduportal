import pytest
from httpx import AsyncClient


async def test_create_user(client: AsyncClient, get_user_from_database):
    user_data = {
        "name": "Alex",
        "surname": "Sokol",
        "email": "nice@example.com",
        "password": "simple-password",
    }

    response = await client.post("/user/", json=user_data)
    data_from_resp = response.json()

    assert response.status_code == 200
    assert data_from_resp["name"] == user_data["name"]
    assert data_from_resp["surname"] == user_data["surname"]
    assert data_from_resp["email"] == user_data["email"]
    assert data_from_resp["is_active"] is True
    assert "password" not in data_from_resp

    users_from_db = await get_user_from_database(data_from_resp["user_id"])
    assert len(users_from_db) == 1
    user_from_db = dict(users_from_db[0])

    assert user_from_db["name"] == user_data["name"]
    assert user_from_db["surname"] == user_data["surname"]
    assert user_from_db["email"] == user_data["email"]
    assert user_from_db["is_active"] is True
    assert str(user_from_db["user_id"]) == data_from_resp["user_id"]


async def test_create_user_duplicate_email_error(
    client: AsyncClient, get_user_from_database
):
    user_data = {
        "name": "Alex",
        "surname": "Vachevsky",
        "email": "vachev@gmail.com",
        "password": "simple-password",
    }
    user_data_same = {
        "name": "Kyrylo",
        "surname": "Sirnuk",
        "email": "vachev@gmail.com",
        "password": "simple-password",
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
    response = await client.post("/user/", json=user_data_same)
    assert response.status_code == 503
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "user_data_for_creation, expected_status_code, expected_detail",
    [
        (
            {},
            422,
            {
                "detail": [
                    {
                        "type": "missing",
                        "loc": ["body", "name"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "surname"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "email"],
                        "msg": "Field required",
                        "input": {},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": {},
                    },
                ]
            },
        ),
        (
            {"name": 123, "surname": 456, "email": "lol"},
            422,
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["body", "name"],
                        "msg": "Input should be a valid string",
                        "input": 123,
                    },
                    {
                        "type": "string_type",
                        "loc": ["body", "surname"],
                        "msg": "Input should be a valid string",
                        "input": 456,
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "lol",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                    {
                        "type": "missing",
                        "loc": ["body", "password"],
                        "msg": "Field required",
                        "input": {"name": 123, "surname": 456, "email": "lol"},
                    },
                ]
            },
        ),
        (
            {"name": 123, "surname": 456, "email": "lol", "password": "13123131"},
            422,
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["body", "name"],
                        "msg": "Input should be a valid string",
                        "input": 123,
                    },
                    {
                        "type": "string_type",
                        "loc": ["body", "surname"],
                        "msg": "Input should be a valid string",
                        "input": 456,
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "lol",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                ]
            },
        ),
        (
            {"name": "Nice", "surname": 456, "email": "lol", "password": "13123131"},
            422,
            {
                "detail": [
                    {
                        "type": "string_type",
                        "loc": ["body", "surname"],
                        "msg": "Input should be a valid string",
                        "input": 456,
                    },
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "lol",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    },
                ]
            },
        ),
        (
            {
                "name": "Nice",
                "surname": "ToSeeU",
                "email": "nice.com",
                "password": "13123131",
            },
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "nice.com",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
        (
            {"name": "123", "surname": "ToSeeU", "email": "nice.com", "password": ""},
            422,
            {"detail": "Name should contains only letters"},
        ),
        (
            {"name": "Alex", "surname": "123", "email": "nice.com", "password": ""},
            422,
            {"detail": "Surname should contains only letters"},
        ),
        (
            {
                "name": "Alex",
                "surname": "Chernyshov",
                "email": "nice.com",
                "password": "",
            },
            422,
            {
                "detail": [
                    {
                        "type": "value_error",
                        "loc": ["body", "email"],
                        "msg": "value is not a valid email address: An email address must have an @-sign.",
                        "input": "nice.com",
                        "ctx": {"reason": "An email address must have an @-sign."},
                    }
                ]
            },
        ),
    ],
)
async def test_create_user_validation_error(
    client: AsyncClient,
    user_data_for_creation,
    expected_status_code,
    expected_detail,
):
    response = await client.post("/user/", json=user_data_for_creation)
    data_from_resp = response.json()
    assert response.status_code == expected_status_code
    assert data_from_resp == expected_detail
