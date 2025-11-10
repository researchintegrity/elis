"""
Test suite for user operations: registration, login, and deletion
"""
import pytest
from fastapi import status


class TestUserRegistration:
    """Tests for user registration"""

    def test_register_user_success(self, client, clean_users_collection, test_user_data):
        """Test successful user registration"""
        response = client.post(
            "/auth/register",
            json=test_user_data
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Verify token response
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "user" in data
        assert "expires_in" in data

        # Verify user data
        user = data["user"]
        assert user["username"] == test_user_data["username"]
        assert user["email"] == test_user_data["email"]
        assert user["full_name"] == test_user_data["full_name"]
        assert user["is_active"] is True

    def test_register_user_missing_required_fields(self, client, clean_users_collection):
        """Test registration with missing required fields"""
        incomplete_data = {
            "username": "testuser",
            # missing email and password
        }

        response = client.post(
            "/auth/register",
            json=incomplete_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_invalid_email(self, client, clean_users_collection):
        """Test registration with invalid email format"""
        invalid_data = {
            "username": "testuser",
            "email": "invalid-email",
            "password": "Test@Password123",
            "full_name": "Test User"
        }

        response = client.post(
            "/auth/register",
            json=invalid_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_user_short_password(self, client, clean_users_collection):
        """Test registration with password less than 8 characters"""
        short_pass_data = {
            "username": "testuser",
            "email": "testuser@example.com",
            "password": "short",  # Less than 8 characters
            "full_name": "Test User"
        }

        response = client.post(
            "/auth/register",
            json=short_pass_data
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_duplicate_username(self, client, clean_users_collection, test_user_data, test_user_data_2):
        """Test registration with duplicate username"""
        # Register first user
        response1 = client.post(
            "/auth/register",
            json=test_user_data
        )
        assert response1.status_code == status.HTTP_200_OK

        # Try to register with same username but different email
        duplicate_data = {
            "username": test_user_data["username"],  # Same username
            "email": "different@example.com",
            "password": "AnotherPass123",
            "full_name": "Different User"
        }

        response2 = client.post(
            "/auth/register",
            json=duplicate_data
        )

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response2.json()["detail"]

    def test_register_duplicate_email(self, client, clean_users_collection, test_user_data):
        """Test registration with duplicate email"""
        # Register first user
        response1 = client.post(
            "/auth/register",
            json=test_user_data
        )
        assert response1.status_code == status.HTTP_200_OK

        # Try to register with same email but different username
        duplicate_data = {
            "username": "differentuser",
            "email": test_user_data["email"],  # Same email
            "password": "AnotherPass123",
            "full_name": "Different User"
        }

        response2 = client.post(
            "/auth/register",
            json=duplicate_data
        )

        assert response2.status_code == status.HTTP_400_BAD_REQUEST
        assert "already registered" in response2.json()["detail"]


class TestUserLogin:
    """Tests for user login"""

    def test_login_with_username(self, client, clean_users_collection, test_user_data):
        """Test login using username"""
        # Register user first
        client.post("/auth/register", json=test_user_data)

        # Login with username
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user_data["username"]
        assert data["user"]["email"] == test_user_data["email"]

    def test_login_with_email(self, client, clean_users_collection, test_user_data):
        """Test login using email instead of username"""
        # Register user first
        client.post("/auth/register", json=test_user_data)

        # Login with email
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["email"],  # Use email as username
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["username"] == test_user_data["username"]

    def test_login_invalid_username(self, client, clean_users_collection):
        """Test login with non-existent username"""
        response = client.post(
            "/auth/login",
            data={
                "username": "nonexistent",
                "password": "SomePassword123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_wrong_password(self, client, clean_users_collection, test_user_data):
        """Test login with incorrect password"""
        # Register user first
        client.post("/auth/register", json=test_user_data)

        # Login with wrong password
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["username"],
                "password": "WrongPassword123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "Invalid username or password" in response.json()["detail"]

    def test_login_returns_valid_token(self, client, clean_users_collection, test_user_data):
        """Test that login returns a valid JWT token"""
        # Register user
        client.post("/auth/register", json=test_user_data)

        # Login
        response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert response.status_code == status.HTTP_200_OK
        token = response.json()["access_token"]

        # Verify token can be used to access protected endpoint
        auth_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert auth_response.status_code == status.HTTP_200_OK
        assert auth_response.json()["username"] == test_user_data["username"]


class TestUserDeletion:
    """Tests for user deletion"""

    def test_delete_user_success(self, client, clean_users_collection, test_user_data):
        """Test successful user deletion"""
        # Register user
        register_response = client.post(
            "/auth/register",
            json=test_user_data
        )
        assert register_response.status_code == status.HTTP_200_OK
        token = register_response.json()["access_token"]

        # Delete user
        response = client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert "deleted" in data["message"].lower()

    def test_delete_user_cannot_login_after_deletion(self, client, clean_users_collection, test_user_data):
        """Test that deleted user cannot login"""
        # Register user
        register_response = client.post(
            "/auth/register",
            json=test_user_data
        )
        token = register_response.json()["access_token"]

        # Delete user
        delete_response = client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Try to login with deleted user
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )

        assert login_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_user_without_auth(self, client, clean_users_collection):
        """Test deletion without authentication fails"""
        response = client.delete("/users/me")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_delete_user_with_invalid_token(self, client, clean_users_collection):
        """Test deletion with invalid token fails"""
        response = client.delete(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token_xyz"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestUserOperationsIntegration:
    """Integration tests for complete user workflows"""

    def test_complete_user_lifecycle(self, client, clean_users_collection, test_user_data):
        """Test complete user lifecycle: register -> login -> delete"""
        # Step 1: Register user
        register_response = client.post(
            "/auth/register",
            json=test_user_data
        )
        assert register_response.status_code == status.HTTP_200_OK
        register_data = register_response.json()
        token = register_data["access_token"]

        assert register_data["user"]["username"] == test_user_data["username"]
        assert register_data["user"]["email"] == test_user_data["email"]

        # Step 2: Login with registered user
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        login_data = login_response.json()

        assert login_data["user"]["username"] == test_user_data["username"]
        assert login_data["access_token"] != ""

        # Step 3: Get current user info
        user_info_response = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert user_info_response.status_code == status.HTTP_200_OK
        user_info = user_info_response.json()

        assert user_info["username"] == test_user_data["username"]
        assert user_info["email"] == test_user_data["email"]

        # Step 4: Delete user
        delete_response = client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Step 5: Verify user is deleted (cannot login)
        final_login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data["username"],
                "password": test_user_data["password"]
            }
        )
        assert final_login_response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_multiple_users_independent_operations(self, client, clean_users_collection, test_user_data, test_user_data_2):
        """Test that multiple users can operate independently"""
        # Register first user
        response1 = client.post("/auth/register", json=test_user_data)
        assert response1.status_code == status.HTTP_200_OK
        token1 = response1.json()["access_token"]

        # Register second user
        response2 = client.post("/auth/register", json=test_user_data_2)
        assert response2.status_code == status.HTTP_200_OK
        token2 = response2.json()["access_token"]

        # Verify each user can access their own info
        user1_info = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert user1_info.json()["username"] == test_user_data["username"]

        user2_info = client.get(
            "/users/me",
            headers={"Authorization": f"Bearer {token2}"}
        )
        assert user2_info.json()["username"] == test_user_data_2["username"]

        # Delete first user
        delete_response = client.delete(
            "/users/me",
            headers={"Authorization": f"Bearer {token1}"}
        )
        assert delete_response.status_code == status.HTTP_200_OK

        # Verify second user still exists and can login
        login_response = client.post(
            "/auth/login",
            data={
                "username": test_user_data_2["username"],
                "password": test_user_data_2["password"]
            }
        )
        assert login_response.status_code == status.HTTP_200_OK
        assert login_response.json()["user"]["username"] == test_user_data_2["username"]
