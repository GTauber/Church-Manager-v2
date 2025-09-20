from typing import Any, Dict
import logging
from fastapi import APIRouter, BackgroundTasks, HTTPException
from app.schemas.waha import WAHAWebhookPayload, WebhookResponse, HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["waha"])


async def process_webhook_message(payload: Dict[str, Any]) -> None:
    try:
        logger.info(f"Processing webhook payload: {payload}")

        event_type = payload.get("event", "unknown")
        session_id = payload.get("session", "unknown")

        logger.info(f"Event: {event_type}, Session: {session_id}")

        if "payload" in payload:
            message_data = payload["payload"]
            logger.info(f"Message data: {message_data}")

    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")


@router.post("/webhook", response_model=WebhookResponse)
async def webhook_handler(
    payload: WAHAWebhookPayload,
    background_tasks: BackgroundTasks
) -> WebhookResponse:
    try:
        payload_dict = payload.model_dump()

        background_tasks.add_task(
            process_webhook_message,
            payload_dict
        )

        return WebhookResponse(ok=True)

    except Exception as e:
        logger.error(f"Webhook handler error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="healthy",
        service="waha-webhook"
    )