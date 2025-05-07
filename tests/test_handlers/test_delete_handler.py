from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.conftest import create_test_auth_header_for_user


async def test_delete_user(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Alex",
        "surname": "Shevchenko",
        "email": "lol@kek.com",
        "is_active": True,
        "hashed_password": "SampleHashPassword",
    }
    await create_user_in_database(**user_data)

    response = await client.delete(
        url="/user/",
        params={"user_id": user_data["user_id"]},
        headers=create_test_auth_header_for_user(user_data["email"]),
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
    "test_case",
    [
        {
            "name": "user_id_validation_error",
            "input_data": lambda user_id: 123,
            "expected_status": 422,
            "expected_response": {
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
            },
        },
        {
            "name": "user_not_found",
            "input_data": lambda user_id: uuid4(),
            "expected_status": 404,
            "expected_response": lambda user_id: {
                "detail": f"User with id {user_id} not found."
            },
        },
    ],
)
async def test_delete_user_validation_scenarios(
    client: AsyncClient, create_user_in_database, test_case
):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    # Pass None since we don't need the input parameter
    request_user_id = test_case["input_data"](None)

    response = await client.delete(
        "/user/",
        params={"user_id": request_user_id},
        headers=create_test_auth_header_for_user(user_data["email"]),
    )

    assert response.status_code == test_case["expected_status"]

    if callable(test_case["expected_response"]):
        assert response.json() == test_case["expected_response"](request_user_id)
    else:
        assert response.json() == test_case["expected_response"]


@pytest.mark.parametrize(
    "test_case",
    [
        {
            "name": "bad_credentials",
            "headers": lambda email: create_test_auth_header_for_user(email + "a"),
            "expected_status": 401,
            "expected_response": {"detail": "Could not validate credentials"},
        },
        {
            "name": "bad_jwt",
            "headers": lambda email: {
                "Authorization": create_test_auth_header_for_user(email)[
                    "Authorization"
                ]
                + "a"
            },
            "expected_status": 401,
            "expected_response": {"detail": "Could not validate credentials"},
        },
        {
            "name": "no_jwt",
            "headers": lambda _: {},
            "expected_status": 401,
            "expected_response": {"detail": "Not authenticated"},
        },
    ],
)
async def test_delete_user_authentication_scenarios(
    client: AsyncClient, create_user_in_database, test_case
):
    user_data = {
        "user_id": uuid4(),
        "name": "Mykola",
        "surname": "Svyrydov",
        "email": "lol@kek.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    headers = test_case["headers"](user_data["email"])
    response = await client.delete(
        "/user/", params={"user_id": user_data["user_id"]}, headers=headers
    )

    assert response.status_code == test_case["expected_status"]

    if callable(test_case["expected_response"]):
        assert response.json() == test_case["expected_response"](user_data)
    else:
        assert response.json() == test_case["expected_response"]
