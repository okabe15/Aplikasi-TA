# auth.py - UPDATED with Login Activity Tracking
from fastapi import APIRouter, HTTPException, status, Depends, Header
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from pony.orm import db_session, flush, commit
from datetime import datetime, timedelta
from jose import jwt, JWTError
from passlib.context import CryptContext
from typing import Optional
import logging

from app.database.models import User
from app.models.schemas import UserRegister, UserResponse, Token
from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)

def get_current_user_from_token(token: str = Depends(oauth2_scheme)) -> User:
    """Get current user from JWT token and update last_active"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    with db_session:
        user = User.get(username=username)
        if user is None:
            raise credentials_exception
        
        # ✅ NEW: Update last_active on every authenticated request
        try:
            user.last_active = datetime.now()
            commit()
        except Exception as e:
            logger.warning(f"Failed to update last_active for {username}: {e}")
        
        return user

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister):
    with db_session:
        # Check username exists
        if User.get(username=user_data.username):
            raise HTTPException(400, "Username already registered")
        
        # Check email exists
        if User.get(email=user_data.email):
            raise HTTPException(400, "Email already registered")
        
        # Create user
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hash_password(user_data.password),
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True,
            created_at=datetime.now(),
            # ✅ NEW: Initialize login tracking fields
            last_active=None,
            last_login=None,
            login_count=0
        )
        
        # Flush to get ID assigned
        flush()
        
        return UserResponse(
            id=user.id,
            username=user.username,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at.isoformat()
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with db_session:
        user = User.get(username=form_data.username)
        
        if not user or not verify_password(form_data.password, user.hashed_password):
            raise HTTPException(
                status_code=401,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # ✅ NEW: Update login tracking
        now = datetime.now()
        user.last_login = now
        user.last_active = now
        user.login_count = (user.login_count or 0) + 1
        
        commit()
        
        logger.info(f"User {user.username} logged in (total logins: {user.login_count})")
        
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        
        return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user_from_token)):
    """Get current user info from token"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at.isoformat()
    )

# ============================================================================
# NEW ENDPOINT: Get user activity stats
# ============================================================================

@router.get("/activity")
async def get_my_activity(current_user: User = Depends(get_current_user_from_token)):
    """Get current user's activity statistics"""
    with db_session:
        user = User.get(id=current_user.id)
        
        return {
            "username": user.username,
            "last_login": user.last_login.isoformat() if user.last_login else None,
            "last_active": user.last_active.isoformat() if user.last_active else None,
            "login_count": user.login_count or 0,
            "member_since": user.created_at.isoformat()
        }

# ============================================================================
# CHANGES MADE:
# 1. get_current_user_from_token now updates last_active on every request
# 2. login endpoint updates last_login, last_active, and increments login_count
# 3. register endpoint initializes new tracking fields
# 4. Added /activity endpoint to get user's activity stats
# ============================================================================