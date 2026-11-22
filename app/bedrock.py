import logging
from functools import lru_cache

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError
from fastapi import HTTPException, status

from app.config import get_settings
from app.schemas import ChatRequest

logger = logging.getLogger(__name__)


@lru_cache
def _client():
    settings = get_settings()
    return boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
        config=Config(
            connect_timeout=5,
            read_timeout=60,
            retries={"max_attempts": 3, "mode": "standard"},
        ),
    )


def generate_response(request: ChatRequest) -> str:
    settings = get_settings()
    try:
        result = _client().converse(
            modelId=settings.bedrock_model_id,
            messages=[
                {
                    "role": message.role,
                    "content": [{"text": message.content}],
                }
                for message in request.messages
            ],
            inferenceConfig={"maxTokens": min(request.max_tokens, settings.max_output_tokens)},
        )
        return "".join(
            block["text"]
            for block in result["output"]["message"]["content"]
            if "text" in block
        )
    except (BotoCoreError, ClientError, KeyError) as exc:
        logger.exception("Bedrock model invocation failed")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="The model service could not complete the request",
        ) from exc
