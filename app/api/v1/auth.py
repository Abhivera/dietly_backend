
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.schemas.auth import Token, LoginRequest, GoogleAuthRequest, GoogleAuthResponse
from app.schemas.user import UserCreate, UserResponse
from app.services.auth_service import AuthService
from app.services.google_oauth_service import GoogleOAuthService
from typing import Dict
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# ===== ORIGINAL ROUTES =====

@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    """Register a new local user"""
    logger.info(f"Registration attempt for email: {user_create.email}")
    
    try:
        auth_service = AuthService(db)
        
        # Check if user already exists
        if auth_service.get_user_by_email(user_create.email):
            logger.warning(f"Registration failed: Email {user_create.email} already exists")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        if auth_service.get_user_by_username(user_create.username):
            logger.warning(f"Registration failed: Username {user_create.username} already taken")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        user = auth_service.create_user(user_create)
        logger.info(f"User registered successfully: {user.email}")
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during registration: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to internal error"
        )

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login with username and password (form data)"""
    logger.info(f"Login attempt for username: {form_data.username}")
    
    try:
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(form_data.username, form_data.password)
        
        if not user:
            logger.warning(f"Login failed for username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        
        logger.info(f"Login successful for username: {form_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )

@router.post("/login-json", response_model=Token)
def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login with username and password (JSON data)"""
    logger.info(f"JSON login attempt for username: {login_data.username}")
    
    try:
        auth_service = AuthService(db)
        user = auth_service.authenticate_user(login_data.username, login_data.password)
        
        if not user:
            logger.warning(f"JSON login failed for username: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
            )
        
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        
        logger.info(f"JSON login successful for username: {login_data.username}")
        return {"access_token": access_token, "token_type": "bearer"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during JSON login: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to internal error"
        )
    

# ===== GOOGLE OAUTH ROUTES =====

@router.get("/google/login")
def google_login():
    """Initiate Google OAuth login"""
    logger.info("Google login initiation request")
    
    try:
        google_service = GoogleOAuthService()
        auth_url, state = google_service.get_google_auth_url()
        
        logger.info(f"Google auth URL generated with state: {state}")
        # In a real application, you might want to store the state in session/cache
        # For simplicity, we're just returning the URL
        return {"auth_url": auth_url, "state": state}
        
    except Exception as e:
        logger.error(f"Error generating Google auth URL: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate Google authentication URL"
        )

@router.get("/google/callback")
async def google_callback(
    code: str,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth callback with comprehensive error handling"""
    
    # Log the incoming request
    logger.info(f"Google callback received - Code length: {len(code) if code else 0}")
    logger.info(f"State: {state}")
    
    if error:
        logger.error(f"Google OAuth error: {error}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth error: {error}"
        )
    
    if not code:
        logger.error("No authorization code provided")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
    
    try:
        google_service = GoogleOAuthService()
        
        # Exchange code for token
        logger.info("Starting token exchange")
        token_data = await google_service.exchange_code_for_token(code)
        if not token_data:
            logger.error("Token exchange failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        logger.info(f"Token exchange successful, getting user info")
        
        # Get user info
        user_info = await google_service.get_user_info(token_data['access_token'])
        if not user_info:
            logger.error("Failed to get user info")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        logger.info(f"User info retrieved: {user_info.get('email', 'unknown')}")
        
        # Authenticate or create user
        auth_service = AuthService(db)
        logger.info("Starting user authentication/creation")
        
        user, is_new_user = auth_service.authenticate_or_create_google_user(user_info)
        
        if not user:
            logger.error("Failed to authenticate or create user")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to authenticate or create user"
            )
        
        logger.info(f"User processed successfully. ID: {user.id}, New user: {is_new_user}")
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        
        logger.info("Access token generated successfully")
        
        response_data = {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "provider": user.provider
            },
            "is_new_user": is_new_user
        }
        
        logger.info(f"Returning successful response for user: {user.email}")
        return response_data
        
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google callback: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during Google authentication: {str(e)}"
        )

@router.post("/google/auth", response_model=GoogleAuthResponse)
async def google_auth(
    auth_request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """Handle Google OAuth authentication (for mobile/SPA applications) with enhanced debugging"""
    
    logger.info(f"Google auth POST request received")
    logger.info(f"Code length: {len(auth_request.code) if auth_request.code else 0}")
    
    try:
        google_service = GoogleOAuthService()
        
        # Exchange code for token
        logger.info("Starting token exchange for POST request")
        token_data = await google_service.exchange_code_for_token(auth_request.code)
        if not token_data:
            logger.error("Token exchange failed for POST request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        # Verify ID token if present
        if 'id_token' in token_data:
            logger.info("Verifying ID token")
            id_info = google_service.verify_google_token(token_data['id_token'])
            if not id_info:
                logger.error("ID token verification failed")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid ID token"
                )
        
        # Get user info
        logger.info("Getting user info for POST request")
        user_info = await google_service.get_user_info(token_data['access_token'])
        if not user_info:
            logger.error("Failed to get user info for POST request")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user information"
            )
        
        # Authenticate or create user
        auth_service = AuthService(db)
        logger.info("Processing user for POST request")
        user, is_new_user = auth_service.authenticate_or_create_google_user(user_info)
        
        # Generate access token
        access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
        access_token = create_access_token(
            subject=user.username, expires_delta=access_token_expires
        )
        
        logger.info(f"POST request successful for user: {user.email}")
        
        return GoogleAuthResponse(
            access_token=access_token,
            token_type="bearer",
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "full_name": user.full_name,
                "avatar_url": user.avatar_url,
                "provider": user.provider
            },
            is_new_user=is_new_user
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in Google auth POST: {str(e)}")
        logger.exception("Full traceback:")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error during Google authentication: {str(e)}"
        )   