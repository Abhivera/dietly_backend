# api/auth.py
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.core.security import create_access_token
from app.api.deps import get_current_user
from app.core.config import settings
from app.schemas.auth import (
    Token, LoginRequest, PasswordResetRequest, 
    PasswordResetConfirm, PasswordChange
)
from app.schemas.user import UserCreate, UserResponse, UserProfile
from app.services.auth_service import AuthService
from app.services.email_service import EmailService
from app.models.user import User

router = APIRouter()

@router.post("/register", status_code=status.HTTP_202_ACCEPTED)
async def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Start registration: store pending registration and send verification email"""
    auth_service = AuthService(db)
    try:
        auth_service.create_pending_registration(user_create)
        return {"message": "Verification email sent. Please check your inbox to complete registration."}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with form data (OAuth2 compatible) - supports username or email"""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(form_data.username, form_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login-json", response_model=Token)
async def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with JSON data - supports username or email"""
    auth_service = AuthService(db)
    user = auth_service.authenticate_user(login_data.username_or_email, login_data.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username/email or password",
        )
    
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        subject=user.username, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/password-reset-request")
async def request_password_reset(
    reset_request: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Request password reset - sends email with reset token"""
    auth_service = AuthService(db)
    email_service = EmailService()
    
    # Always return success to prevent email enumeration
    user = auth_service.get_user_by_email(reset_request.email)
    if user:
        token = auth_service.create_password_reset_token(reset_request.email)
        if token:
            # Send email in background to avoid blocking
            background_tasks.add_task(
                email_service.send_password_reset_email,
                user.email,
                user.username,
                token
            )
    
    return {"message": "If the email exists, a password reset link has been sent"}

@router.post("/password-reset-confirm")
async def confirm_password_reset(
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token and new password"""
    auth_service = AuthService(db)
    
    success = auth_service.reset_password(reset_confirm.token, reset_confirm.new_password)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    return {"message": "Password has been reset successfully"}

@router.post("/change-password")
async def change_password(
    password_change: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user"""
    auth_service = AuthService(db)
    
    success = auth_service.change_password(
        current_user,
        password_change.current_password,
        password_change.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: User = Depends(get_current_user)):
    """Get current user profile"""
    return current_user

# @router.post("/logout")
# async def logout():
#     """Logout endpoint (token blacklisting would be implemented here)"""
#     return {"message": "Successfully logged out"}

# @router.post("/refresh", response_model=Token)
# async def refresh_token(current_user: User = Depends(get_current_user)):
#     """Refresh access token"""
#     access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
#     access_token = create_access_token(
#         subject=current_user.username, expires_delta=access_token_expires
#     )
    
#     return {"access_token": access_token, "token_type": "bearer"}

# @router.get("/verify-reset-token/{token}")
# async def verify_reset_token(token: str, db: Session = Depends(get_db)):
#     """Verify if password reset token is valid"""
#     auth_service = AuthService(db)
#     user = auth_service.verify_password_reset_token(token)
    
#     if not user:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail="Invalid or expired reset token"
#         )
    
#     return {"message": "Token is valid", "username": user.username}

@router.get("/verify-email", response_model=UserResponse)
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verify email and complete registration"""
    auth_service = AuthService(db)
    try:
        user = auth_service.complete_registration(token)
        return user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )