import ssl

import certifi
import jwt
from fastapi import HTTPException, Request, status

from app.core.config import settings

# Supabase signs session tokens asymmetrically (ES256). We verify against
# the project's public signing keys (JWKS) rather than a shared secret, so
# the backend never needs to hold a key capable of *issuing* tokens.
# PyJWKClient caches keys by `kid` internally, so one client is reused across
# requests instead of refetching the JWKS every time.
#
# An explicit certifi-backed SSL context is passed because some local
# Python installs (python.org's macOS build in particular) don't wire up a
# system trust store, which would otherwise fail every JWKS fetch.
_ssl_context = ssl.create_default_context(cafile=certifi.where())
_jwk_client = jwt.PyJWKClient(
    f"{settings.supabase_url}/auth/v1/.well-known/jwks.json",
    ssl_context=_ssl_context,
)


def extract_bearer_token(request: Request) -> str:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Authorization header")
    return header.removeprefix("Bearer ")


def decode_access_token(token: str) -> dict:
    # aud="authenticated" is also checked, so a token minted for some other
    # purpose can't be replayed against this API.
    try:
        signing_key = _jwk_client.get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=["ES256"],
            audience="authenticated",
        )
    except jwt.PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
