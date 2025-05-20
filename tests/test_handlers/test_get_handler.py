from uuid import uuid4

import pytest
from httpx import AsyncClient

from src.db.models import PortalRole
from tests.conftest import create_test_auth_header_for_user


async def test_get_user(client: AsyncClient, create_user_in_database):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
        "roles": [PortalRole.USER],
    }
    await create_user_in_database(**user_data)

    response = await client.get(
        "/user/",
        params={"user_id": user_data["user_id"]},
        headers=create_test_auth_header_for_user(user_data["email"]),
    )
    user_from_response = response.json()

    assert response.status_code == 200
    assert user_from_response["user_id"] == str(user_data["user_id"])
    assert user_from_response["name"] == user_data["name"]
    assert user_from_response["surname"] == user_data["surname"]
    assert user_from_response["email"] == user_data["email"]
    assert user_from_response["is_active"] == user_data["is_active"]


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            {
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
            id="user_id_validation_error",
        ),
        pytest.param(
            {
                "input_data": lambda user_id: uuid4(),
                "expected_status": 404,
                "expected_response": lambda user_id: {
                    "detail": f"User with id {user_id} not found."
                },
            },
            id="user_not_found",
        ),
    ],
)
async def test_get_user_validation_scenarios(
    client: AsyncClient, create_user_in_database, test_case
):
    user_data = {
        "user_id": uuid4(),
        "name": "Nikolai",
        "surname": "Sviridov",
        "email": "lol@kek.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
        "roles": [PortalRole.USER],
    }
    await create_user_in_database(**user_data)

    # Pass None since we don't need the input parameter
    request_user_id = test_case["input_data"](None)

    response = await client.get(
        "/user/",
        params={"user_id": request_user_id},
        headers=create_test_auth_header_for_user(user_data["email"]),
    )

    assert response.status_code == test_case["expected_status"]

    if callable(test_case["expected_response"]):
        assert response.json() == test_case["expected_response"](
            request_user_id
        )
    else:
        assert response.json() == test_case["expected_response"]


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            {
                "headers": lambda email: create_test_auth_header_for_user(
                    email
                ),
                "expected_status": 200,
                "expected_response": lambda user_data: {
                    "user_id": str(user_data["user_id"]),
                    "name": user_data["name"],
                    "surname": user_data["surname"],
                    "email": user_data["email"],
                    "is_active": user_data["is_active"],
                },
            },
            id="valid_auth",
        ),
        pytest.param(
            {
                "headers": lambda email: create_test_auth_header_for_user(
                    email + "a"
                ),
                "expected_status": 401,
                "expected_response": {
                    "detail": "Could not validate credentials"
                },
            },
            id="bad_credentials",
        ),
        pytest.param(
            {
                "headers": lambda email: {
                    "Authorization": create_test_auth_header_for_user(email)[
                        "Authorization"
                    ]
                    + "a"
                },
                "expected_status": 401,
                "expected_response": {
                    "detail": "Could not validate credentials"
                },
            },
            id="bad_jwt",
        ),
        pytest.param(
            {
                "headers": lambda _: {},
                "expected_status": 401,
                "expected_response": {"detail": "Not authenticated"},
            },
            id="no_jwt",
        ),
    ],
)
async def test_get_user_authentication_scenarios(
    client: AsyncClient, create_user_in_database, test_case
):
    user_data = {
        "user_id": uuid4(),
        "name": "Mykola",
        "surname": "Svyrydov",
        "email": "lol@kek.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
        "roles": [PortalRole.USER],
    }
    await create_user_in_database(**user_data)

    headers = test_case["headers"](user_data["email"])
    response = await client.get(
        "/user/", params={"user_id": user_data["user_id"]}, headers=headers
    )

    assert response.status_code == test_case["expected_status"]

    if callable(test_case["expected_response"]):
        assert response.json() == test_case["expected_response"](user_data)
    else:
        assert response.json() == test_case["expected_response"]
