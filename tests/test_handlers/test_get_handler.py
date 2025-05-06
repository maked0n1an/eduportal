from uuid import uuid4

from httpx import AsyncClient


async def test_get_user(
    client: AsyncClient, create_user_in_database, get_user_from_database
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

    response = await client.get("/user/", params={"user_id": user_data["user_id"]})
    user_from_response = response.json()

    assert response.status_code == 200
    assert user_from_response["user_id"] == str(user_data["user_id"])
    assert user_from_response["name"] == user_data["name"]
    assert user_from_response["surname"] == user_data["surname"]
    assert user_from_response["email"] == user_data["email"]
    assert user_from_response["is_active"] == user_data["is_active"]


async def test_get_user_id_validation_error(
    client: AsyncClient, create_user_in_database, get_user_from_database
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

    response = await client.get("/user/", params={"user_id": 123})
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


async def test_get_user_not_found(
    client: AsyncClient, create_user_in_database, get_user_from_database
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

    user_id_for_finding = uuid4()
    response = await client.get("/user/", params={"user_id": user_id_for_finding})

    assert response.status_code == 404
    assert response.json() == {
        "detail": f"User with id {user_id_for_finding} not found."
    }
