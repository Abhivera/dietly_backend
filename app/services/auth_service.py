from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate, UserCreateGoogle
from app.core.security import get_password_hash, verify_password
from typing import Optional
import secrets
import string
import logging

logger = logging.getLogger(__name__)

class AuthService:
    def __init__(self, db: Session):
        self.db = db
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        try:
            user = self.db.query(User).filter(User.email == email).first()
            logger.info(f"User lookup by email {email}: {'Found' if user else 'Not found'}")
            return user
        except Exception as e:
            logger.error(f"Error looking up user by email {email}: {e}")
            return None
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        try:
            user = self.db.query(User).filter(User.username == username).first()
            logger.info(f"User lookup by username {username}: {'Found' if user else 'Not found'}")
            return user
        except Exception as e:
            logger.error(f"Error looking up user by username {username}: {e}")
            return None
    
    def get_user_by_google_id(self, google_id: str) -> Optional[User]:
        try:
            user = self.db.query(User).filter(User.google_id == google_id).first()
            logger.info(f"User lookup by Google ID {google_id}: {'Found' if user else 'Not found'}")
            return user
        except Exception as e:
            logger.error(f"Error looking up user by Google ID {google_id}: {e}")
            return None
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            logger.info(f"Authentication failed: User {username} not found")
            return None
        if not user.hashed_password:  # Google user trying to login with password
            logger.info(f"Authentication failed: User {username} is Google user")
            return None
        if not verify_password(password, user.hashed_password):
            logger.info(f"Authentication failed: Invalid password for {username}")
            return None
        logger.info(f"Authentication successful for {username}")
        return user
    
    def create_user(self, user_create: UserCreate) -> User:
        try:
            logger.info(f"Creating local user: {user_create.email}")
            
            hashed_password = get_password_hash(user_create.password)
            db_user = User(
                email=user_create.email,
                username=user_create.username,
                full_name=user_create.full_name,
                hashed_password=hashed_password,
                provider="local"
            )
            
            self.db.add(db_user)
            self.db.commit()
            self.db.refresh(db_user)
            
            logger.info(f"Local user created successfully. ID: {db_user.id}")
            return db_user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating user: {e}")
            raise Exception(f"User creation failed: Duplicate email or username")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating user: {e}")
            raise Exception(f"Database error during user creation")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating user: {e}")
            raise Exception(f"Unexpected error during user creation")
    
    def create_google_user(self, user_data: UserCreateGoogle) -> User:
        try:
            logger.info(f"Creating Google user: {user_data.email}")
            logger.info(f"Google user data: email={user_data.email}, username={user_data.username}, google_id={user_data.google_id}")
            
            db_user = User(
                email=user_data.email,
                username=user_data.username,
                full_name=user_data.full_name,
                google_id=user_data.google_id,
                avatar_url=user_data.avatar_url,
                provider="google",
                hashed_password=None  # Explicitly set to None for Google users
            )
            
            logger.info(f"User object created, adding to session")
            self.db.add(db_user)
            
            logger.info("Committing transaction")
            self.db.commit()
            
            logger.info("Refreshing user object")
            self.db.refresh(db_user)
            
            logger.info(f"Google user created successfully. ID: {db_user.id}, Email: {db_user.email}")
            return db_user
            
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Integrity error creating Google user: {e}")
            logger.error(f"This might be due to duplicate email, username, or google_id")
            raise Exception(f"Google user creation failed: Duplicate data - {str(e)}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error creating Google user: {e}")
            raise Exception(f"Database error during Google user creation: {str(e)}")
        except Exception as e:
            self.db.rollback()
            logger.error(f"Unexpected error creating Google user: {e}")
            raise Exception(f"Unexpected error during Google user creation: {str(e)}")
    
    def generate_unique_username(self, base_username: str) -> str:
        """Generate a unique username based on the base username"""
        logger.info(f"Generating unique username from base: {base_username}")
        
        username = base_username.lower().replace(" ", "_")
        
        # Remove special characters
        username = ''.join(char for char in username if char.isalnum() or char == '_')
        
        # Ensure it's not too long
        if len(username) > 20:
            username = username[:20]
        
        # Ensure it's not empty
        if not username:
            username = "user"
        
        # Check if username exists
        original_username = username
        counter = 1
        
        while self.get_user_by_username(username):
            username = f"{original_username}_{counter}"
            counter += 1
            logger.info(f"Username {original_username} taken, trying {username}")
        
        logger.info(f"Generated unique username: {username}")
        return username
    
    def authenticate_or_create_google_user(self, google_user_info: dict) -> tuple[User, bool]:
        """Authenticate existing Google user or create new one with comprehensive error handling"""
        try:
            logger.info(f"Processing Google user authentication/creation")
            logger.info(f"Google user info keys: {list(google_user_info.keys())}")
            
            google_id = google_user_info.get('id')
            email = google_user_info.get('email')
            
            if not google_id:
                logger.error("No Google ID found in user info")
                raise Exception("Google ID missing from user information")
            
            if not email:
                logger.error("No email found in user info")
                raise Exception("Email missing from user information")
            
            logger.info(f"Processing user with Google ID: {google_id}, Email: {email}")
            
            # Check if user exists by Google ID
            user = self.get_user_by_google_id(google_id)
            if user:
                logger.info(f"Found existing user by Google ID: {user.id}")
                return user, False  # Existing user
            
            # Check if user exists by email (might be a local account)
            user = self.get_user_by_email(email)
            if user:
                logger.info(f"Found existing user by email, linking Google account: {user.id}")
                # Link Google account to existing user
                user.google_id = google_id
                user.avatar_url = google_user_info.get('picture')
                if not user.full_name and google_user_info.get('name'):
                    user.full_name = google_user_info.get('name')
                
                try:
                    self.db.commit()
                    self.db.refresh(user)
                    logger.info(f"Successfully linked Google account to existing user")
                    return user, False
                except Exception as e:
                    self.db.rollback()
                    logger.error(f"Failed to link Google account: {e}")
                    raise Exception(f"Failed to link Google account: {str(e)}")
            
            # Create new user
            logger.info("Creating new Google user")
            base_username = google_user_info.get('name', '').replace(' ', '_').lower()
            if not base_username:
                base_username = email.split('@')[0]
            
            unique_username = self.generate_unique_username(base_username)
            
            user_data = UserCreateGoogle(
                email=email,
                username=unique_username,
                full_name=google_user_info.get('name'),
                google_id=google_id,
                avatar_url=google_user_info.get('picture')
            )
            
            logger.info(f"User data prepared: {user_data.dict()}")
            
            user = self.create_google_user(user_data)
            logger.info(f"New Google user created successfully: {user.id}")
            return user, True  # New user
            
        except Exception as e:
            logger.error(f"Error in authenticate_or_create_google_user: {e}")
            raise