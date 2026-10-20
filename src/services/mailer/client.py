import logging
from collections.abc import Callable
from pathlib import Path
from typing import Any

import resend
from jinja2 import Environment, FileSystemLoader

logger = logging.getLogger("email_service")

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
TEMPLATES_DIR = BASE_DIR / "templates"

jinja_env = Environment(loader=FileSystemLoader(TEMPLATES_DIR), autoescape=True, enable_async=True)


class MailerError(Exception):
    pass


class MailerService:
    def __init__(
        self,
        api_key: str,
        resend_domain: str,
        sender_fn: Callable[..., Any] = resend.Emails.send_async,
    ):
        self.api_key = api_key
        self.resend_domain = resend_domain
        self.sender_fn = sender_fn
        resend.api_key = self.api_key

    async def send_forgot_password_email(self, email: str, username: str, reset_url: str):
        try:
            template = jinja_env.get_template("forgot-password.html")
            html = await template.render_async(username=username, reset_url=reset_url)

            params: resend.Emails.SendParams = {
                "from": f"Pixel Reviews <{self.resend_domain}>",
                "to": [email],
                "subject": "Pixel Reviews password reset",
                "html": html,
            }
            await self.sender_fn(params)
        except Exception as error:
            logger.exception(
                "[Mailer] Error sending the forgot password email. to email: %s", email
            )
            raise MailerError("The email could not be sent") from error

        logger.info(f"[Mailer] Forgot password email sent to {email}")
