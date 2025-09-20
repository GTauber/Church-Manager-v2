from typing import Any, Dict
from pydantic import BaseModel


class WAHAWebhookPayload(BaseModel):
    event: str | None = None
    session: str | None = None
    payload: Dict[str, Any] = {}

    class Config:
        extra = "allow"


class WebhookResponse(BaseModel):
    ok: bool = True


class HealthResponse(BaseModel):
    status: str = "healthy"
    service: str = "waha-webhook"