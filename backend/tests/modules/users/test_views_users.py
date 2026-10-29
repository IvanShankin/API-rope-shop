import pytest

from tests.helpers.functions import comparison_models
from tests.modules.users.fixtures.models_dto import CreateUserFixtureDTO


@pytest.mark.asyncio
async def test_get_me(client_for_tests, create_user_fixture):
    user, accesses_token = await create_user_fixture()

    response = await client_for_tests.get(
        "/users/me",
        headers={"Authorization": f"Bearer {accesses_token}"}
    )

    assert response.status_code == 200
    assert comparison_models(
        user,
        response.json(),
        keys_not_checked=["hashed_password", "is_active", "updated_at"]
    )


@pytest.mark.asyncio
async def test_change_password_success(client_for_tests, create_user_fixture):
    old_password = "initial_secret_password_123"
    new_password = "updated_super_secret_456"

    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(password=old_password)
    )

    # Change password
    response = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": old_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["detail"] == "Password changed successfully"
    assert data["message"] == "Password changed successfully"

    # Old password no longer works
    fail_login_response = await client_for_tests.post(
        "/auth/login",
        data={
            "username": user.username,
            "password": old_password,
        },
    )
    assert fail_login_response.status_code == 401

    # New password works
    success_login_response = await client_for_tests.post(
        "/auth/login",
        data={
            "username": user.username,
            "password": new_password,
        },
    )
    assert success_login_response.status_code == 200
    assert "access_token" in success_login_response.json()


@pytest.mark.asyncio
async def test_change_password_with_alias_old_password(client_for_tests, create_user_fixture):
    old_password = "secret_old_pwd"
    new_password = "secret_new_pwd"

    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(password=old_password)
    )

    response = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "old_password": old_password,
            "new_password": new_password,
        },
    )

    assert response.status_code == 200
    assert response.json()["detail"] == "Password changed successfully"


@pytest.mark.asyncio
async def test_change_password_confirmation_mismatch(client_for_tests, create_user_fixture):
    old_password = "initial_pwd_123"

    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(password=old_password)
    )

    response = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": old_password,
            "new_password": "new_password_123",
            "confirm_password": "different_password_456",
        },
    )

    assert response.status_code == 422
    assert "different_password_456" not in response.text
    assert "new_password_123" not in response.text
    assert old_password not in response.text


@pytest.mark.asyncio
async def test_change_password_incorrect_current_password(client_for_tests, create_user_fixture):
    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(password="correct_password")
    )

    response = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "wrong_password",
            "new_password": "new_password_123",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Incorrect current password"


@pytest.mark.asyncio
async def test_change_password_unauthorized(client_for_tests):
    response = await client_for_tests.post(
        "/users/change-password",
        json={
            "current_password": "some_password",
            "new_password": "new_password",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_change_password_inactive_user(client_for_tests, create_user_fixture):
    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(
            password="test_password",
            is_active=False,
        )
    )

    response = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "test_password",
            "new_password": "new_password",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "User account is inactive"


@pytest.mark.asyncio
async def test_change_password_short_password_fails(client_for_tests, create_user_fixture):
    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(password="original_secret_123")
    )

    response = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": "original_secret_123",
            "new_password": "short",
        },
    )

    assert response.status_code == 422
    assert "original_secret_123" not in response.text
    assert response.json()["errors"][0]["input"] == "[FILTERED]"

@pytest.mark.asyncio
async def test_change_password_revokes_refresh_tokens(client_for_tests, create_user_fixture):
    password = "initial_password_123"
    user, access_token = await create_user_fixture(
        new_user=CreateUserFixtureDTO(password=password)
    )

    # Login to obtain a refresh token
    login_res = await client_for_tests.post(
        "/auth/login",
        data={"username": user.username, "password": password},
    )
    assert login_res.status_code == 200
    refresh_token = login_res.json()["refresh_token"]

    # Verify refresh works initially
    refresh_res = await client_for_tests.post(
        "/auth/refresh_tokens",
        json={"refresh_token": refresh_token},
    )
    assert refresh_res.status_code == 200

    new_refresh_token = refresh_res.json()["refresh_token"]

    # Now change password
    change_res = await client_for_tests.post(
        "/users/change-password",
        headers={"Authorization": f"Bearer {access_token}"},
        json={
            "current_password": password,
            "new_password": "brand_new_password_890",
        },
    )
    assert change_res.status_code == 200

    # The previous refresh token should now be invalid/revoked
    revoked_refresh_res = await client_for_tests.post(
        "/auth/refresh_tokens",
        json={"refresh_token": new_refresh_token},
    )
    assert revoked_refresh_res.status_code in (401, 404)

