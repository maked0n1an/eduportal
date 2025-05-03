import pytest
from httpx import AsyncClient


USER_DATA = [
    {
        "name": "Michael",
        "surname": "Jackson",
        "email": "mijackson@gmail.com"
    },
    {
        "name": "Donald",
        "surname": "Trump",
        "email": "donny@maga.com"
    },
    {
        "name": "Don",
        "surname": "Huan",
        "email": "dhuan@rambler.com"
    },
]


@pytest.mark.parametrize("user", USER_DATA)
async def test_create_user(client: AsyncClient, user: dict):
    response = await client.post("/user/", json=user)
    data = response.json()

    assert response.status_code == 200
    assert data["user_id"] is not None
    assert data["name"] == user["name"]
    assert data["surname"] == user["surname"]
    assert data["email"] == user["email"]
    assert data["is_active"] == True


GET_USER_BY_EMAILS_PARAMS = [
    {"email": "donny@maga.com"}
]


@pytest.mark.parametrize("user_params", GET_USER_BY_EMAILS_PARAMS)
async def test_get_user(client: AsyncClient, user_params: dict):
    response = await client.get("/user/", params=user_params)
    data = response.json()
    assert response.status_code == 200
    assert data["user_id"] is not None
    assert data["name"] == "Donald"
    assert data["surname"] == "Trump"
    assert data["email"] == "donny@maga.com"
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
