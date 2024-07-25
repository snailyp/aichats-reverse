import json
import logging
import os
import uuid
from datetime import datetime
from typing import List, Optional

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import StreamingResponse, Response

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

load_dotenv()
app = FastAPI()
BASE_URL = "https://ai-chats.org"
headers = {
    'accept': 'application/json, text/event-stream',
    'accept-language': 'zh-CN,zh;q=0.9',
    'content-type': 'application/json',
    'origin': BASE_URL,
    'referer': f'{BASE_URL}/chat/',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
}
APP_SECRET = os.getenv("APP_SECRET")
ALLOWED_MODELS = ["gpt-4o", "gpt-4o-2024-05-13"]
# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有源，您可以根据需要限制特定源
    allow_credentials=True,
    allow_methods=["*"],  # 允许所有方法
    allow_headers=["*"],  # 允许所有头
)
security = HTTPBearer()


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    model: str
    messages: List[Message]
    stream: Optional[bool] = False


def simulate_data(content, model):
    return {
        "id": f"chatcmpl-{uuid.uuid4()}",
        "object": "chat.completion.chunk",
        "created": int(datetime.now().timestamp()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "delta": {
                    "content": content,
                    "role": "assistant"
                },
                "finish_reason": None
            }
        ],
        "usage": None
    }


def verify_app_secret(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if credentials.credentials != APP_SECRET:
        raise HTTPException(status_code=403, detail="Invalid APP_SECRET")
    return credentials.credentials


@app.options("/v1/chat/completions")
async def chat_completions_options():
    return Response(
        status_code=200,
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        }
    )


def replace_escaped_newlines(input_string: str) -> str:
    return input_string.replace('\\n', '\n')


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest, app_secret: str = Depends(verify_app_secret)):
    logger.info(f"Received chat completion request for model: {request.model}")

    if request.model not in ALLOWED_MODELS:
        raise HTTPException(status_code=400,
                            detail=f"Model {request.model} is not allowed. Allowed models are: {', '.join(ALLOWED_MODELS)}")

    # 使用 OpenAI API
    json_data = {
        'type': 'chat',
        'messagesHistory': [
            {
                'from': 'you' if msg.role == 'user' else 'chatGPT',
                'content': msg.content
            } for msg in request.messages
        ],
    }
    try:
        response = requests.post(f'{BASE_URL}/chat/send2/', headers=headers, json=json_data, stream=True)
        response.raise_for_status()
        if request.stream:
            logger.info("Streaming response")

            async def generate():
                for line in response.iter_lines():
                    if line:
                        content = line.decode('utf-8')[6:]  # Remove "data: " prefix
                        if content == ' trylimit':
                            continue
                        content = replace_escaped_newlines(content)
                        yield f"data: {json.dumps(simulate_data(content, request.model))}\n\n"
                yield "data: [DONE]\n\n"
                logger.info("Stream completed")

            return StreamingResponse(generate(), media_type="text/event-stream")
        else:
            logger.info("Non-streaming response")
            full_response = ""
            for line in response.iter_lines():
                if line:
                    full_response += line.decode('utf-8')[6:]
                    full_response.replace(" trylimit", "")
                    full_response = replace_escaped_newlines(full_response)
            logger.info("Response generated successfully")
            return {
                "id": f"chatcmpl-{uuid.uuid4()}",
                "object": "chat.completion",
                "created": int(datetime.now().timestamp()),
                "model": request.model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": full_response
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": None
            }
    except requests.RequestException as e:
        logger.error(f"Error communicating with AI-Chats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error communicating with AI-Chats: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
