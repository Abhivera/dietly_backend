# services/auth_service.py
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.security import verify_password, get_password_hash
from app.models.user import User
from app.models.pending_registration import PendingRegistration
from app.models.password_reset import PasswordResetToken
from app.models.email_verfication import EmailVerificationToken
from app.schemas.user import UserCreate
from app.services.email_service import EmailService
from app.core.config import settings

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_username_or_email(self, username_or_email: str) -> Optional[User]:
        """Get user by username or email"""
        return self.db.query(User).filter(
            or_(
                User.username == username_or_email,
                User.email == username_or_email
            )
        ).first()
    
    def authenticate_user(self, username_or_email: str, password: str) -> Optional[User]:
        """Authenticate user with username/email and password"""
        user = self.get_user_by_username_or_email(username_or_email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user
    
    def create_user(self, user_create: UserCreate) -> User:
        """Create a new user and send verification email"""
        hashed_password = get_password_hash(user_create.password)
        db_user = User(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            avatar_url=settings.default_avatar_url,
            gender=user_create.gender,
            age=user_create.age,
            weight=user_create.weight,
            height=user_create.height,
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        # Create and send verification email
        token = self.create_email_verification_token(db_user)
        self.send_verification_email(db_user, token)
        return db_user
    
    def create_password_reset_token(self, email: str) -> Optional[str]:
        """Create a password reset token for the user"""
        user = self.get_user_by_email(email)
        if not user:
            return None
        
        # Invalidate existing tokens for this user
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.user_id == user.id,
            PasswordResetToken.is_used == False
        ).update({"is_used": True})
        
        # Generate new token
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=1)  # Token expires in 1 hour
        
        reset_token = PasswordResetToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        
        self.db.add(reset_token)
        self.db.commit()
        
        return token
    
    def verify_password_reset_token(self, token: str) -> Optional[User]:
        """Verify password reset token and return user if valid"""
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_token:
            return None
        
        return reset_token.user
    
    def reset_password(self, token: str, new_password: str) -> bool:
        """Reset user password using token"""
        reset_token = self.db.query(PasswordResetToken).filter(
            PasswordResetToken.token == token,
            PasswordResetToken.is_used == False,
            PasswordResetToken.expires_at > datetime.utcnow()
        ).first()
        
        if not reset_token:
            return False
        
        # Update user password
        user = reset_token.user
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        
        # Mark token as used
        reset_token.is_used = True
        
        self.db.commit()
        return True
    
    def change_password(self, user: User, current_password: str, new_password: str) -> bool:
        """Change user password after verifying current password"""
        if not verify_password(current_password, user.hashed_password):
            return False
        
        user.hashed_password = get_password_hash(new_password)
        user.updated_at = datetime.utcnow()
        self.db.commit()
        return True
    
    def cleanup_expired_tokens(self):
        """Clean up expired password reset tokens"""
        self.db.query(PasswordResetToken).filter(
            PasswordResetToken.expires_at < datetime.utcnow()
        ).update({"is_used": True})
        self.db.commit()

    def create_email_verification_token(self, user: User) -> str:
        """Create an email verification token for the user"""
        # Invalidate existing tokens for this user
        self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.user_id == user.id,
            EmailVerificationToken.is_used == False
        ).update({"is_used": True})
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)  # Token expires in 24 hours
        verification_token = EmailVerificationToken(
            user_id=user.id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(verification_token)
        self.db.commit()
        return token

    def send_verification_email(self, user: User, token: str) -> bool:
        email_service = EmailService()
        return email_service.send_verification_email(user.email, user.username, token)

    def verify_email_token(self, token: str) -> bool:
        verification_token = self.db.query(EmailVerificationToken).filter(
            EmailVerificationToken.token == token,
            EmailVerificationToken.is_used == False,
            EmailVerificationToken.expires_at > datetime.utcnow()
        ).first()
        if not verification_token:
            return False
        user = verification_token.user
        verification_token.is_used = True
        self.db.commit()
        return True

    def create_pending_registration(self, user_create: UserCreate) -> str:
        """Create a pending registration and send verification email"""
        # Check for existing pending registration or user
        if self.db.query(User).filter((User.email == user_create.email) | (User.username == user_create.username)).first():
            raise Exception("Email or username already registered")
        if self.db.query(PendingRegistration).filter((PendingRegistration.email == user_create.email) | (PendingRegistration.username == user_create.username)).first():
            raise Exception("A registration is already pending for this email or username")
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(hours=24)
        hashed_password = get_password_hash(user_create.password)
        pending = PendingRegistration(
            email=user_create.email,
            username=user_create.username,
            full_name=user_create.full_name,
            hashed_password=hashed_password,
            avatar_url=None,
            gender=user_create.gender,
            age=user_create.age,
            weight=user_create.weight,
            height=user_create.height,
            token=token,
            expires_at=expires_at
        )
        self.db.add(pending)
        self.db.commit()
        email_service = EmailService()
        email_service.send_verification_email(user_create.email, user_create.username, token)
        return token

    def complete_registration(self, token: str) -> User:
        """Complete registration if token is valid, create user, and remove pending registration"""
        pending = self.db.query(PendingRegistration).filter(
            PendingRegistration.token == token,
            PendingRegistration.expires_at > datetime.utcnow()
        ).first()
        if not pending:
            raise Exception("Invalid or expired verification token")
        # Create user
        user = User(
            email=pending.email,
            username=pending.username,
            full_name=pending.full_name,
            hashed_password=pending.hashed_password,
            avatar_url=settings.default_avatar_url,
            is_superuser=False,
            gender=pending.gender if hasattr(pending, 'gender') else None,
            age=pending.age if hasattr(pending, 'age') else None,
            weight=pending.weight if hasattr(pending, 'weight') else None,
            height=pending.height if hasattr(pending, 'height') else None,
        )
        self.db.add(user)
        self.db.delete(pending)
        self.db.commit()
        self.db.refresh(user)
        return user