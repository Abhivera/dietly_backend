import httpx
import logging
from typing import Dict, Optional, Tuple
from google.oauth2 import id_token
from google.auth.transport import requests
from app.core.config import settings
import secrets
import string

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleOAuthService:
    def __init__(self):
        self.client_id = settings.google_client_id
        self.client_secret = settings.google_client_secret
        self.redirect_uri = settings.google_redirect_uri
        self.google_discovery_url = "https://accounts.google.com/.well-known/openid_configuration"
        
        # Log configuration (remove in production)
        logger.info(f"Google OAuth initialized with client_id: {self.client_id[:10]}...")
        logger.info(f"Redirect URI: {self.redirect_uri}")
    
    def get_google_auth_url(self) -> Tuple[str, str]:
        """Generate Google OAuth authorization URL and state"""
        state = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        
        auth_url = (
            f"https://accounts.google.com/o/oauth2/auth?"
            f"response_type=code&"
            f"client_id={self.client_id}&"
            f"redirect_uri={self.redirect_uri}&"
            f"scope=openid email profile&"
            f"state={state}&"
            f"access_type=offline&"
            f"prompt=consent"
        )
        
        logger.info(f"Generated auth URL with state: {state}")
        return auth_url, state
    
    async def exchange_code_for_token(self, code: str) -> Optional[Dict]:
        """Exchange authorization code for access token with enhanced error handling"""
        token_url = "https://oauth2.googleapis.com/token"
        
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": self.redirect_uri,
        }
        
        logger.info(f"Exchanging code for token. Code length: {len(code)}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(token_url, data=data)
                
                logger.info(f"Token exchange response status: {response.status_code}")
                
                if response.status_code == 200:
                    token_data = response.json()
                    logger.info(f"Token exchange successful. Keys: {list(token_data.keys())}")
                    return token_data
                else:
                    error_text = response.text
                    logger.error(f"Token exchange failed: Status {response.status_code}, Response: {error_text}")
                    try:
                        error_json = response.json()
                        logger.error(f"Error details: {error_json}")
                    except:
                        pass
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Token exchange timed out")
            return None
        except Exception as e:
            logger.error(f"Token exchange exception: {str(e)}")
            return None
    
    def verify_google_token(self, id_token_string: str) -> Optional[Dict]:
        """Verify Google ID token and extract user info with enhanced error handling"""
        try:
            logger.info("Verifying Google ID token")
            
            # Verify the token
            idinfo = id_token.verify_oauth2_token(
                id_token_string, 
                requests.Request(), 
                self.client_id
            )
            
            logger.info(f"ID token verified. User ID: {idinfo.get('sub', 'unknown')}")
            
            # Verify the issuer
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                logger.error(f"Wrong issuer: {idinfo['iss']}")
                raise ValueError('Wrong issuer.')
            
            logger.info(f"ID token info keys: {list(idinfo.keys())}")
            return idinfo
            
        except ValueError as e:
            logger.error(f"Token verification failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during token verification: {e}")
            return None
    
    async def get_user_info(self, access_token: str) -> Optional[Dict]:
        """Get user information from Google using access token with enhanced error handling"""
        user_info_url = f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}"
        
        logger.info("Fetching user info from Google")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(user_info_url)
                
                logger.info(f"User info response status: {response.status_code}")
                
                if response.status_code == 200:
                    user_info = response.json()
                    logger.info(f"User info retrieved. Email: {user_info.get('email', 'unknown')}")
                    logger.info(f"User info keys: {list(user_info.keys())}")
                    return user_info
                else:
                    error_text = response.text
                    logger.error(f"Failed to get user info: Status {response.status_code}, Response: {error_text}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("User info request timed out")
            return None
        except Exception as e:
            logger.error(f"User info request exception: {str(e)}")
            return None