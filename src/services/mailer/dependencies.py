from typing import Annotated

from fastapi import Depends

from src.core.settings import settings
from src.services.mailer.client import MailerService


def get_mailer_service() -> MailerService:
    return MailerService(api_key=settings.RESEND_API_KEY, resend_domain=settings.RESEND_DOMAIN)


MailerServiceDep = Annotated[MailerService, Depends(get_mailer_service)]
