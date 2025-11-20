# auth_service.py - FIXED VERSION
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import settings
from app.models.schemas import UserRegister, TokenData
from app.database.models import User
from pony.orm import db_session
from fastapi import HTTPException, status
from typing import Optional

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AuthService:
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return pwd_context.hash(password)
    
    def create_access_token(self, data: dict, expires_delta: Optional[timedelta] = None):
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
        
        return encoded_jwt
    
    def get_current_user(self, token: str) -> User:
        """Get current user from JWT token"""
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
            username: str = payload.get("sub")
            role: str = payload.get("role")
            
            if username is None:
                raise credentials_exception
                
            token_data = TokenData(username=username, role=role)
            
        except JWTError:
            raise credentials_exception
        
        with db_session:  # ✅ Use context manager
            user = User.get(username=token_data.username)
            
            if user is None:
                raise credentials_exception
                
            if not user.is_active:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Inactive user"
                )
            
            return user
    
    def get_current_active_teacher(self, token: str) -> User:
        """Get current user and verify they are a teacher"""
        user = self.get_current_user(token)
        
        if user.role != "teacher":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only teachers can access this resource"
            )
        
        return user
    
    def create_user(self, user_data: UserRegister) -> User:
        """Create a new user - MUST be called within db_session"""
        hashed_password = self.get_password_hash(user_data.password)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            hashed_password=hashed_password,
            full_name=user_data.full_name,
            role=user_data.role,
            is_active=True
        )
        
        return user

auth_service = AuthService()