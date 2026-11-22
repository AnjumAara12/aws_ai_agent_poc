from typing import Literal

from pydantic import BaseModel, Field

from app.config import get_settings


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)


class ChatRequest(BaseModel):
    messages: list[ChatMessage] = Field(min_length=1, max_length=50)
    max_tokens: int = Field(default=1024, ge=1, le=4096)

    def validate_prompt_size(self) -> None:
        total_chars = sum(len(message.content) for message in self.messages)
        if total_chars > get_settings().max_prompt_length:
            raise ValueError(
                f"Combined message content must not exceed "
                f"{get_settings().max_prompt_length} characters"
            )


class ChatResponse(BaseModel):
    response: str
    model_id: str
