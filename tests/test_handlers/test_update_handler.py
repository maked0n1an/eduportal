from uuid import uuid4

import pytest
from httpx import AsyncClient

from tests.conftest import create_test_auth_header_for_user


async def test_update_user(
    client: AsyncClient, create_user_in_database, get_user_from_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Vlad",
        "surname": "Zelenka",
        "email": "zvlad@gmail.com",
        "hashed_password": "SampleHashPassword",
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
        headers=create_test_auth_header_for_user(user_data["email"]),
    )
    response_data = response.json()

    users_from_db = await get_user_from_database(user_data["user_id"])
    user_from_db = dict(users_from_db[0])

    assert response.status_code == 200
    assert response_data["updated_user_id"] == str(user_data["user_id"])
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
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Steve",
        "surname": "Harris",
        "email": "sharris@gmail.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    user_data_3 = {
        "user_id": uuid4(),
        "name": "Don",
        "surname": "Huan",
        "email": "donhuan@gmail.com",
        "hashed_password": "SampleHashPassword",
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
        headers=create_test_auth_header_for_user(user_data_1["email"]),
    )
    response_data = response.json()

    assert response.status_code == 200

    user_1_from_db = await get_user_from_database(user_data_1["user_id"])
    user_from_db = dict(user_1_from_db[0])
    assert response_data["updated_user_id"] == str(user_data_1["user_id"])
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
    "case",
    [
        pytest.param(
            {
                "user_data_updated": {},
                "expected_status_code": 422,
                "expected_detail": {
                    "detail": "At least one parameter for user update info should be provided"
                },
            },
            id="empty_update",
        ),
        pytest.param(
            {
                "user_data_updated": {"name": "123"},
                "expected_status_code": 422,
                "expected_detail": {"detail": "Name should contains only letters"},
            },
            id="invalid_name_numbers",
        ),
        pytest.param(
            {
                "user_data_updated": {"surname": "123"},
                "expected_status_code": 422,
                "expected_detail": {"detail": "Surname should contains only letters"},
            },
            id="invalid_surname_numbers",
        ),
        pytest.param(
            {
                "user_data_updated": {"email": ""},
                "expected_status_code": 422,
                "expected_detail": {
                    "detail": [
                        {
                            "type": "value_error",
                            "loc": ["body", "email"],
                            "msg": "value is not a valid email address: An email address must have an @-sign.",
                            "input": "",
                            "ctx": {"reason": "An email address must have an @-sign."},
                        }
                    ]
                },
            },
            id="empty_email",
        ),
        pytest.param(
            {
                "user_data_updated": {"surname": ""},
                "expected_status_code": 422,
                "expected_detail": {
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
            },
            id="empty_surname",
        ),
        pytest.param(
            {
                "user_data_updated": {"name": ""},
                "expected_status_code": 422,
                "expected_detail": {
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
            },
            id="empty_name",
        ),
        pytest.param(
            {
                "user_data_updated": {"email": "123"},
                "expected_status_code": 422,
                "expected_detail": {
                    "detail": [
                        {
                            "type": "value_error",
                            "loc": ["body", "email"],
                            "msg": "value is not a valid email address: An email address must have an @-sign.",
                            "input": "123",
                            "ctx": {"reason": "An email address must have an @-sign."},
                        }
                    ]
                },
            },
            id="invalid_email_format",
        ),
    ],
)
async def test_update_user_validation_error(
    client: AsyncClient,
    create_user_in_database,
    case: dict,
):
    user_data = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    response = await client.patch(
        "/user/",
        params={"user_id": user_data["user_id"]},
        json=case["user_data_updated"],
        headers=create_test_auth_header_for_user(user_data["email"]),
    )

    assert response.status_code == case["expected_status_code"]
    assert response.json() == case["expected_detail"]


async def test_update_user_id_validation_error(
    client: AsyncClient, create_user_in_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    user_data_updated = {
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
    }

    response = await client.patch(
        "/user/",
        params={"user_id": 123},
        json=user_data_updated,
        headers=create_test_auth_header_for_user(user_data["email"]),
    )

    assert response.status_code == 422
    assert response.json() == {
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


async def test_update_user_not_found_error(
    client: AsyncClient, create_user_in_database
):
    user_data = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    user_data_updated = {
        "name": "Michael",
        "surname": "Jordan",
        "email": "jordan@gmail.com",
    }
    user_id = uuid4()

    response = await client.patch(
        "/user/",
        params={"user_id": user_id},
        json=user_data_updated,
        headers=create_test_auth_header_for_user(user_data_updated["email"]),
    )

    assert response.status_code == 404
    assert response.json() == {"detail": f"User with id {user_id} not found."}


async def test_update_user_duplicate_email_error(
    client: AsyncClient, create_user_in_database
):
    user_data_1 = {
        "user_id": uuid4(),
        "name": "Michael",
        "surname": "Jackson",
        "email": "mjackson@mail.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    user_data_2 = {
        "user_id": uuid4(),
        "name": "Steve",
        "surname": "Harris",
        "email": "sharris@gmail.com",
        "hashed_password": "SampleHashPassword",
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
        headers=create_test_auth_header_for_user(user_data_1["email"]),
    )

    assert response.status_code == 503
    assert (
        'duplicate key value violates unique constraint "users_email_key"'
        in response.json()["detail"]
    )


@pytest.mark.parametrize(
    "test_case",
    [
        pytest.param(
            {
                "headers": lambda email: create_test_auth_header_for_user(email + "a"),
                "expected_status": 401,
                "expected_response": {"detail": "Could not validate credentials"},
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
                "expected_response": {"detail": "Could not validate credentials"},
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
        "name": "Michael",
        "surname": "Jackson",
        "email": "lol@kek.com",
        "hashed_password": "SampleHashPassword",
        "is_active": True,
    }
    await create_user_in_database(**user_data)

    user_data_updated = {
        "surname": "Jordan",
    }

    headers = test_case["headers"](user_data["email"])
    response = await client.patch(
        "/user/",
        params={"user_id": user_data["user_id"]},
        json=user_data_updated,
        headers=headers,
    )

    assert response.status_code == test_case["expected_status"]

    if callable(test_case["expected_response"]):
        assert response.json() == test_case["expected_response"](user_data)
    else:
        assert response.json() == test_case["expected_response"]
