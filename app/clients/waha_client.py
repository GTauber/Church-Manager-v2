import httpx
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class WAHAClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key

    async def send_message(self, chat_id: str, text: str, session: str = "default") -> bool:
        try:
            async with httpx.AsyncClient() as client:
                headers = {"Content-Type": "application/json"}
                if self.api_key:
                    headers["X-Api-Key"] = self.api_key

                response = await client.post(
                    f"{self.base_url}/api/sendText",
                    json={
                        "session": session,
                        "chatId": chat_id,
                        "text": text
                    },
                    headers=headers,
                    timeout=10.0
                )

                if response.status_code == 200:
                    logger.info(f"Message sent successfully to {chat_id}")
                    return True
                else:
                    logger.warning(
                        f"Failed to send message. Status: {response.status_code}"
                    )
                    return False

        except httpx.TimeoutException:
            logger.error(f"Timeout sending message to {chat_id}")
            return False
        except httpx.RequestError as e:
            logger.error(f"Request error: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return False