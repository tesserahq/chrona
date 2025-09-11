import pytest
from unittest.mock import Mock, patch
import jwt
from fastapi import HTTPException
from app.utils.auth import VerifyToken, UnauthorizedException, UnauthenticatedException
from app.schemas.user import UserOnboard
from app.models.user import User

# Mock JWT token for testing
MOCK_TOKEN = "mock.jwt.token"
MOCK_USER_ID = "test-user-id"
MOCK_EMAIL = "test@example.com"
MOCK_NAME = "Test User"
MOCK_AVATAR = "https://example.com/avatar.jpg"


@pytest.fixture
def mock_jwks_client():
    with patch("jwt.PyJWKClient") as mock:
        mock_instance = Mock()
        mock.return_value = mock_instance
        mock_instance.get_signing_key_from_jwt.return_value = Mock(
            key="mock-signing-key"
        )
        yield mock_instance


@pytest.fixture
def verifier(db, mock_jwks_client):
    return VerifyToken(db)


def test_verify_token_success(verifier, mock_jwks_client):
    with patch("app.utils.auth.UserService") as mock_user_service_class:
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        # Mock JWT decode
        mock_payload = {"sub": MOCK_USER_ID}
        with patch("jwt.decode", return_value=mock_payload):
            # Mock userinfo response
            mock_userinfo = {
                "email": MOCK_EMAIL,
                "first_name": "Test",
                "last_name": "User",
                "avatar_url": MOCK_AVATAR,
            }
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_userinfo
                mock_get.return_value = mock_response

                # Mock existing user
                mock_user = User(
                    id=1,
                    external_id=MOCK_USER_ID,
                    email=MOCK_EMAIL,
                    first_name="Test",
                    last_name="User",
                    avatar_url=MOCK_AVATAR,
                )
                mock_user_service.get_user_by_external_id.return_value = mock_user

                # Test verification
                verifier2 = VerifyToken(verifier.db)
                result = verifier2.verify(MOCK_TOKEN)

                assert isinstance(result, User)
                assert result.external_id == MOCK_USER_ID
                assert result.email == MOCK_EMAIL
                mock_user_service.get_user_by_external_id.assert_called_once_with(
                    MOCK_USER_ID
                )
                mock_user_service.onboard_user.assert_not_called()


def test_verify_token_new_user(verifier, mock_jwks_client):
    with patch("app.utils.auth.UserService") as mock_user_service_class:
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service
        user_id = "13d3ec54-a6b4-42a1-81b8-80d78107bbfd"

        # Mock JWT decode
        mock_payload = {"sub": MOCK_USER_ID}
        with patch("jwt.decode", return_value=mock_payload):
            # Mock userinfo response
            mock_userinfo = {
                "id": user_id,
                "email": MOCK_EMAIL,
                "first_name": "Test",
                "last_name": "User",
                "avatar_url": MOCK_AVATAR,
            }
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.json.return_value = mock_userinfo
                mock_get.return_value = mock_response

                # Mock new user
                mock_user_service.get_user_by_external_id.return_value = None
                mock_new_user = User(
                    id=user_id,
                    external_id=MOCK_USER_ID,
                    email=MOCK_EMAIL,
                    first_name="Test",
                    last_name="User",
                    avatar_url=MOCK_AVATAR,
                )
                mock_user_service.onboard_user.return_value = mock_new_user

                # Test verification
                verifier2 = VerifyToken(verifier.db)
                result = verifier2.verify(MOCK_TOKEN)

                assert isinstance(result, User)
                assert result.external_id == MOCK_USER_ID
                assert result.email == MOCK_EMAIL
                mock_user_service.get_user_by_external_id.assert_called_once_with(
                    MOCK_USER_ID
                )
                mock_user_service.onboard_user.assert_called_once()
                call_args = mock_user_service.onboard_user.call_args[0][0]
                assert isinstance(call_args, UserOnboard)
                assert call_args.external_id == MOCK_USER_ID
                assert call_args.email == MOCK_EMAIL
                assert call_args.first_name == "Test"
                assert call_args.last_name == "User"
                assert call_args.avatar_url == MOCK_AVATAR


def test_verify_token_invalid_token(verifier, mock_jwks_client):
    mock_jwks_client.get_signing_key_from_jwt.side_effect = (
        jwt.exceptions.PyJWKClientError("Invalid token")
    )

    with pytest.raises(HTTPException) as exc_info:
        verifier.verify(MOCK_TOKEN)

    assert exc_info.value.status_code == 401


def test_verify_token_missing_token(verifier):
    with pytest.raises(UnauthenticatedException):
        verifier.verify(None)


def test_verify_token_userinfo_failure(verifier, mock_jwks_client):
    with patch("app.utils.auth.UserService") as mock_user_service_class:
        mock_user_service = Mock()
        mock_user_service_class.return_value = mock_user_service

        # Mock JWT decode
        mock_payload = {"sub": MOCK_USER_ID}
        with patch("jwt.decode", return_value=mock_payload):
            # Mock user service to return None (user doesn't exist)
            mock_user_service.get_user_by_external_id.return_value = None

            # Mock failed userinfo response
            with patch("requests.get") as mock_get:
                mock_response = Mock()
                mock_response.status_code = 401
                mock_response.text = "Unauthorized"
                mock_get.return_value = mock_response

                verifier2 = VerifyToken(verifier.db)
                with pytest.raises(UnauthorizedException) as exc_info:
                    verifier2.verify(MOCK_TOKEN)

                assert "Failed to fetch user info from oidc" in str(exc_info.value)


def test_verify_token_invalid_payload(verifier, mock_jwks_client):
    with patch("jwt.decode", side_effect=jwt.InvalidTokenError("Invalid token")):
        with pytest.raises(UnauthorizedException) as exc_info:
            verifier.verify(MOCK_TOKEN)

        assert "Invalid token" in str(exc_info.value)
