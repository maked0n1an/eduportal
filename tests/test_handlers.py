from httpx import AsyncClient
from tests.conftest import client_fixture


async def test_create_user(client: AsyncClient):
    response = await client.post(
        "/user/",
        json={
            "name": "Nikolai",
            "surname": "Sviridov",
            "email": "lol@kek.com"
        }
    )
    data = response.json()

    assert response.status_code == 200
    assert data["user_id"] is not None
    assert data["name"] == "Nikolai"
    assert data["surname"] == "Sviridov"
    assert data["email"] == "lol@kek.com"
    assert data["is_active"] == True


async def test_get_user(client: AsyncClient):
    response = await client.get(
        "/user/",
        params={"email": "lol@kek.com"}
    )

    data = response.json()
    assert response.status_code == 200
    assert data["user_id"] is not None
    assert data["name"] == "Nikolai"
    assert data["surname"] == "Sviridov"
    assert data["email"] == "lol@kek.com"
    assert data["is_active"] == True


async def test_create_and_get_user(client: AsyncClient):
    response = await client.post(
        "/user/",
        json={
            "name": "Nikolai",
            "surname": "Sviridov",
            "email": "nice@example.com"
        }
    )
    data_from_resp = response.json()

    assert response.status_code == 200
    assert data_from_resp["user_id"] is not None
    assert data_from_resp["name"] == "Nikolai"
    assert data_from_resp["surname"] == "Sviridov"
    assert data_from_resp["email"] == "nice@example.com"
    assert data_from_resp["is_active"] == True

    response = await client.get(
        "/user/",
        params={"email": "nice@example.com"}
    )

    user_json = response.json()
    assert response.status_code == 200
    assert user_json["user_id"] == data_from_resp["user_id"]
    assert user_json["name"] == data_from_resp["name"]
    assert user_json["surname"] == data_from_resp["surname"]
    assert user_json["email"] == data_from_resp["email"]
    assert user_json["is_active"] == data_from_resp["is_active"]
