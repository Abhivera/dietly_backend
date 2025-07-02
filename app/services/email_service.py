import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        # Load from environment with fallback to working values
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME", "abhijitakadeveloper@gmail.com")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "hyoqoqjlahflqlbr")  # No spaces
        self.from_email = os.getenv("FROM_EMAIL", "abhijitakadeveloper@gmail.com")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Debug logging
        print(f"Email Debug - Server: {self.smtp_server}:{self.smtp_port}")
        print(f"Email Debug - Username: {self.smtp_username}")
        print(f"Email Debug - Password length: {len(self.smtp_password) if self.smtp_password else 0}")
        print(f"Email Debug - Password (masked): {self.smtp_password[:4]}****{self.smtp_password[-4:] if len(self.smtp_password) >= 8 else 'TOO_SHORT'}")
    
    def send_email(self, to_email: str, subject: str, body: str, html_body: Optional[str] = None) -> bool:
        """Send email using the exact same method as your working test"""
        try:
            if html_body:
                # Use multipart for HTML
                msg = MIMEMultipart('alternative')
                msg['Subject'] = subject
                msg['From'] = self.from_email
                msg['To'] = to_email
                
                text_part = MIMEText(body, 'plain')
                html_part = MIMEText(html_body, 'html')
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                # Use simple MIMEText like your working example
                msg = MIMEText(body)
                msg["Subject"] = subject
                msg["From"] = self.from_email
                msg["To"] = to_email
            
            # Use exact same SMTP flow as your working code
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"Email sent successfully to {to_email}")
            print(f"SUCCESS: Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {to_email}: {str(e)}")
            print(f"ERROR: Failed to send email to {to_email}: {str(e)}")
            return False
    
    def send_password_reset_email(self, to_email: str, username: str, reset_token: str) -> bool:
        """Send password reset email"""
        reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"
        
        subject = "Password Reset Request"
        
        # Plain text version
        text_body = f"""
Hi {username},

You requested a password reset for your account. Click the link below to reset your password:

{reset_url}

This link will expire in 1 hour.

If you didn't request this password reset, please ignore this email.

Best regards,
Your App Team
        """.strip()
        
        # HTML version
        html_body = f"""
        <html>
            <body>
                <h2>Password Reset Request</h2>
                <p>Hi {username},</p>
                <p>You requested a password reset for your account. Click the button below to reset your password:</p>
                <p>
                    <a href="{reset_url}" 
                       style="background-color: #007bff; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px; display: inline-block;">
                        Reset Password
                    </a>
                </p>
                <p>Or copy and paste this link in your browser:</p>
                <p><a href="{reset_url}">{reset_url}</a></p>
                <p><strong>This link will expire in 1 hour.</strong></p>
                <p>If you didn't request this password reset, please ignore this email.</p>
                <p>Best regards,<br>Your App Team</p>
            </body>
        </html>
        """
        
        return self.send_email(to_email, subject, text_body, html_body)

    def send_verification_email(self, to_email: str, username: str, verification_token: str) -> bool:
        """Send email verification email"""
        verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
        subject = "Verify Your Email Address"
        text_body = f"""
Hi {username},

Thank you for registering. Please verify your email address by clicking the link below:

{verification_url}

If you did not create an account, please ignore this email.

Best regards,
Your App Team
        """.strip()
        html_body = f"""
        <html>
            <body>
                <h2>Verify Your Email Address</h2>
                <p>Hi {username},</p>
                <p>Thank you for registering. Please verify your email address by clicking the button below:</p>
                <p>
                    <a href=\"{verification_url}\" 
                       style=\"background-color: #28a745; color: white; padding: 10px 20px; \
                              text-decoration: none; border-radius: 5px; display: inline-block;\">
                        Verify Email
                    </a>
                </p>
                <p>Or copy and paste this link in your browser:</p>
                <p><a href=\"{verification_url}\">{verification_url}</a></p>
                <p>If you did not create an account, please ignore this email.</p>
                <p>Best regards,<br>Your App Team</p>
            </body>
        </html>
        """
        return self.send_email(to_email, subject, text_body, html_body)