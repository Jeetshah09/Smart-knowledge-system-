"""Authentication endpoints: register, login, logout, me, change-password."""
from fastapi import APIRouter, Depends, HTTPException
from pymongo.errors import DuplicateKeyError

from app.core.database import user_settings_collection, users_collection
from app.core.config import utc_now
from app.core.security import create_access_token, hash_password, verify_password
from app.dependencies.auth import get_current_user_id
from app.schemas.user import PasswordChange, UserCreate, UserLogin, UserResponse, UserUpdate
from app.services.activity_service import log_activity
from app.utils.mongo_utils import serialize_doc

router = APIRouter(prefix="/api/auth", tags=["Auth"])


def _user_response(doc: dict) -> dict:
    data = serialize_doc(doc)
    data.pop("password_hash", None)
    return data


@router.post("/register")
def register(payload: UserCreate):
    email = payload.email.strip().lower()
    existing = users_collection().find_one({"email": email})
    if existing:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user_doc = {
        "name": payload.name.strip(),
        "email": email,
        "password_hash": hash_password(payload.password),
        "profile_image": None,
        "is_active": True,
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }
    try:
        result = users_collection().insert_one(user_doc)
    except DuplicateKeyError:
        raise HTTPException(status_code=409, detail="An account with this email already exists.")

    user_settings_collection().update_one(
        {"user_id": result.inserted_id},
        {
            "$setOnInsert": {
                "user_id": result.inserted_id,
                "theme": "system",
                "notifications": True,
                "default_model": "balanced",
                "response_style": "balanced",
                "created_at": utc_now(),
                "updated_at": utc_now(),
            }
        },
        upsert=True,
    )

    user = users_collection().find_one({"_id": result.inserted_id})
    token = create_access_token(str(result.inserted_id))
    log_activity(str(result.inserted_id), "register", f"Account created for {email}")
    return {
        "success": True,
        "message": "Registration successful",
        "data": {"user": _user_response(user), "access_token": token, "token_type": "bearer"},
    }


@router.post("/login")
def login(payload: UserLogin):
    email = payload.email.strip().lower()
    user = users_collection().find_one({"email": email})
    if not user or not verify_password(payload.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="This account has been deactivated.")

    token = create_access_token(str(user["_id"]))
    log_activity(str(user["_id"]), "login", f"{email} logged in")
    return {
        "success": True,
        "message": "Login successful",
        "data": {"user": _user_response(user), "access_token": token, "token_type": "bearer"},
    }


@router.post("/logout")
def logout(user_id: str = Depends(get_current_user_id)):
    # JWTs are stateless; the client discards the token. Activity is logged.
    log_activity(user_id, "logout", "User logged out")
    return {"success": True, "message": "Logged out successfully", "data": None}


@router.get("/me")
def me(user_id: str = Depends(get_current_user_id)):
    user = users_collection().find_one({"_id": __import__("bson").ObjectId(user_id)})
    if not user:
        raise HTTPException(status_code=404, detail="User not found.")
    return {"success": True, "message": "User fetched", "data": {"user": _user_response(user)}}


@router.put("/me")
def update_me(payload: UserUpdate, user_id: str = Depends(get_current_user_id)):
    import bson

    updates: dict = {"updated_at": utc_now()}
    if payload.name is not None:
        updates["name"] = payload.name.strip()
    if payload.profile_image is not None:
        updates["profile_image"] = payload.profile_image

    users_collection().update_one({"_id": bson.ObjectId(user_id)}, {"$set": updates})
    user = users_collection().find_one({"_id": bson.ObjectId(user_id)})
    return {"success": True, "message": "Profile updated", "data": {"user": _user_response(user)}}


@router.post("/change-password")
def change_password(payload: PasswordChange, user_id: str = Depends(get_current_user_id)):
    import bson

    user = users_collection().find_one({"_id": bson.ObjectId(user_id)})
    if not user or not verify_password(payload.current_password, user.get("password_hash", "")):
        raise HTTPException(status_code=400, detail="Current password is incorrect.")

    users_collection().update_one(
        {"_id": bson.ObjectId(user_id)},
        {"$set": {"password_hash": hash_password(payload.new_password), "updated_at": utc_now()}},
    )
    log_activity(user_id, "changed_password", "Password changed")
    return {"success": True, "message": "Password changed successfully", "data": None}
