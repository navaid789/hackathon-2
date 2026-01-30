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
        raise HTTPException(status_code=401, detail=f"Invalid token: {e}")


def get_user_id(token_payload: dict) -> str:
    user_id = token_payload.get("sub") or token_payload.get("userId") or token_payload.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="No user ID in token")
    return user_id
