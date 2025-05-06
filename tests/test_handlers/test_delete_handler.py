from uuid import uuid4

from httpx import AsyncClient


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


async def test_delete_user_not_found(client: AsyncClient):
    user_id = uuid4()
    response = await client.delete(f"/user/?user_id={user_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": f"User with id {user_id} not found."}


async def test_delete_user_user_id_validation_error(client: AsyncClient):
    response = await client.delete("/user/", params={"user_id": 123})

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
