import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, Literal
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD")


class TestEmailRequest(BaseModel):
    to_email: EmailStr
    email_type: Literal["verification", "password_reset", "custom"]
    subject: Optional[str] = None
    text_content: Optional[str] = None
    html_content: Optional[str] = None


class SuccessResponse(BaseModel):
    success: bool
    message: str


def get_verification_email_text(link: str) -> str:
    return f"""
    Verify Your Email

    Please click the following link to verify your email address:
    {link}

    If you did not request this, please ignore this email.
    """


def get_verification_email_html(link: str) -> str:
    return f"""
    <html>
        <body>
            <h2>Verify Your Email</h2>
            <p>Please click the button below to verify your email address:</p>
            <a href="{link}" style="background-color: #4CAF50; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Verify Email</a>
            <p>If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """


def get_password_reset_email_text(link: str) -> str:
    return f"""
    Password Reset Request

    Please click the following link to reset your password:
    {link}

    If you did not request this, please ignore this email.
    """


def get_password_reset_email_html(link: str) -> str:
    return f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>Please click the button below to reset your password:</p>
            <a href="{link}" style="background-color: #f44336; color: white; padding: 14px 20px; text-decoration: none; border-radius: 4px; display: inline-block;">Reset Password</a>
            <p>If you did not request this, please ignore this email.</p>
        </body>
    </html>
    """


def send_email_gmail(to_email: str, subject: str, text_content: str, html_content: str) -> bool:
    """Send email using Gmail SMTP"""
    try:
        # Create message
        message = MIMEMultipart('alternative')
        message['From'] = f"Medical Advisor <{GMAIL_USER}>"
        message['To'] = to_email
        message['Subject'] = subject

        # Attach plain text and HTML
        part1 = MIMEText(text_content, 'plain')
        part2 = MIMEText(html_content, 'html')
        message.attach(part1)
        message.attach(part2)

        # Connect to Gmail SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587, timeout=10)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_APP_PASSWORD)

        # Send email
        server.send_message(message)
        server.quit()

        print(f"✓ Email sent successfully to {to_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {str(e)}")
        return False


@app.post("/api/test-email", response_model=SuccessResponse)
async def test_email(request: TestEmailRequest):
    """
    Test email sending functionality

    Sends a test email using the configured Gmail SMTP server.

    Email Types:
    - "verification": Sends a sample verification email
    - "password_reset": Sends a sample password reset email
    - "custom": Sends a custom email (requires subject, text_content, and html_content)

    Example Request:
    {
        "to_email": "test@example.com",
        "email_type": "verification"
    }

    Or for custom email:
    {
        "to_email": "test@example.com",
        "email_type": "custom",
        "subject": "Test Subject",
        "text_content": "Plain text content",
        "html_content": "<h1>HTML content</h1>"
    }
    """
    try:
        print(f"📧 Testing email send to: {request.to_email}")

        # Determine email content based on type
        if request.email_type == "verification":
            subject = "🏥 Test Verification Email"
            test_link = "https://example.com/verify?token=TEST_TOKEN_123"
            text_content = get_verification_email_text(test_link)
            html_content = get_verification_email_html(test_link)

        elif request.email_type == "password_reset":
            subject = "🔒 Test Password Reset Email"
            test_link = "https://example.com/reset?token=TEST_TOKEN_123"
            text_content = get_password_reset_email_text(test_link)
            html_content = get_password_reset_email_html(test_link)

        elif request.email_type == "custom":
            # Custom email requires all fields
            if not request.subject or not request.text_content or not request.html_content:
                raise HTTPException(
                    status_code=400,
                    detail="Custom email type requires subject, text_content, and html_content fields"
                )
            subject = request.subject
            text_content = request.text_content
            html_content = request.html_content

        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid email_type: {request.email_type}. Must be 'verification', 'password_reset', or 'custom'"
            )

        # Send the email
        email_sent = send_email_gmail(
            to_email=request.to_email,
            subject=subject,
            text_content=text_content,
            html_content=html_content
        )

        if not email_sent:
            raise HTTPException(
                status_code=500,
                detail="Failed to send test email. Check server logs for details."
            )

        print(f"✓ Test email sent successfully to: {request.to_email}")

        return SuccessResponse(
            success=True,
            message=f"Test email ({request.email_type}) sent successfully to {request.to_email}"
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Error sending test email: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to send test email: {str(e)}"
        )
