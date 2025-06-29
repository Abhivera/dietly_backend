from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from app.models.user import User
from app.schemas.user import UserCreate
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
   