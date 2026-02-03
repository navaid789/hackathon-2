import os
import httpx
import jwt as pyjwt
from jwt import PyJWKClient
from fastapi import HTTPException, Security
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from dotenv import load_dotenv

load_dotenv()

JWKS_URL = os.environ.get("JWKS_URL", "http://localhost:3000/api/auth/jwks")

security = HTTPBearer()

_jwk_client = PyJWKClient(JWKS_URL)


def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)) -> dict:
    import logging
    logger = logging.getLogger(__name__)
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(credentials.credentials)
        payload = pyjwt.decode(
            credentials.credentials,
            signing_key.key,
            algorithms=["EdDSA", "ES256", "RS256", "PS256"],
            options={"verify_aud": False},
        )
        return payload
    except Exception as e:
        logger.error(f"Token verification failed: {type(e).__name__}: {e}")
        # Retry with fresh JWKS keys
        try:
            _jwk_client.fetch_data()
            signing_key = _jwk_client.get_signing_key_from_jwt(credentials.credentials)
            payload = pyjwt.decode(
                credentials.credentials,
                signing_key.key,
                algorithms=["EdDSA", "ES256", "RS256", "PS256"],
                options={"verify_aud": False},
            )
            return payload
        except Exception as e2:
            logger.error(f"Token verification retry failed: {type(e2).__name__}: {e2}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {e2}")


def get_user_id(token_payload: dict) -> str:
    user_id = token_payload.get("sub") or token_payload.get("userId") or token_payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user ID in token")
    return user_id
