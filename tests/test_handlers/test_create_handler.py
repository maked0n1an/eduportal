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

    db_records = await get_user_from_database(data_from_resp["user_id"])
    assert len(db_records) == 1
    user_from_db = dict(db_records[0])

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

    db_records = await get_user_from_database(data_from_resp["user_id"])
    assert len(db_records) == 1
    user_from_db = dict(db_records[0])

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
    "test_case",
    [
        pytest.param(
            {
                "user_data": {},
                "expected_status_code": 422,
                "expected_detail": {
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
            },
            id="empty_request",
        ),
        pytest.param(
            {
                "user_data": {"name": 123, "surname": 456, "email": "lol"},
                "expected_status_code": 422,
                "expected_detail": {
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
            },
            id="invalid_types_and_missing_password",
        ),
        pytest.param(
            {
                "user_data": {
                    "name": "123",
                    "surname": "ToSeeU",
                    "email": "nice.com",
                    "password": "",
                },
                "expected_status_code": 422,
                "expected_detail": {"detail": "Name should contains only letters"},
            },
            id="invalid_name_format",
        ),
        pytest.param(
            {
                "user_data": {
                    "name": "Alex",
                    "surname": "123",
                    "email": "nice.com",
                    "password": "",
                },
                "expected_status_code": 422,
                "expected_detail": {"detail": "Surname should contains only letters"},
            },
            id="invalid_surname_format",
        ),
        pytest.param(
            {
                "user_data": {
                    "name": "Alex",
                    "surname": "Chernyshov",
                    "email": "nice.com",
                    "password": "",
                },
                "expected_status_code": 422,
                "expected_detail": {
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
            },
            id="invalid_email_format",
        ),
    ],
)
async def test_create_user_validation_error(
    client: AsyncClient,
    test_case: dict,
):
    response = await client.post("/user/", json=test_case["user_data"])
    assert response.status_code == test_case["expected_status_code"]
    assert response.json() == test_case["expected_detail"]
