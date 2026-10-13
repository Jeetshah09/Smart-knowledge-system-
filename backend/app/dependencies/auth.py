"""Shared FastAPI dependencies."""
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.core.security import decode_access_token
from app.utils.mongo_utils import is_valid_object_id, to_object_id

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user_id(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> str:
    """Extract and validate the JWT from the Authorization header.

    Also accepts a token in the ?token= query param (used for direct downloads).
    """
    token = None
    if credentials is not None:
        token = credentials.credentials
    if not token:
        token = request.query_params.get("token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated. Please log in.")

    user_id = decode_access_token(token)
    if not user_id or not is_valid_object_id(user_id):
        raise HTTPException(status_code=401, detail="Invalid or expired token. Please log in again.")
    return user_id


def parse_object_id_or_400(value: str, kind: str = "id") -> object:
    try:
        return to_object_id(value)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid {kind} format.")
