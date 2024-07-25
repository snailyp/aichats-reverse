
# AI Chat API

[English](README.md) | [中文](README-CH.md)

This project provides an API interface for AI chat functionality, utilizing the ai-chats.org service. It's built with FastAPI and can be deployed as a standalone application, a Docker container, or on Vercel.

## Features

- Chat completion API endpoint compatible with OpenAI's API format
- Streaming and non-streaming response options
- Cross-Origin Resource Sharing (CORS) support
- Logging for better debugging and monitoring
- Support for `gpt-4o/gpt-4o-2024-05-13` model

## Setup and Installation

1. Clone the repository
2. Install dependencies:

   ```sh
   pip install -r requirements.txt
   ```

3. Set up your environment variables:
   - Create a `.env` file in the root directory
   - Add your APP_SECRET: `APP_SECRET=your_secret_here`
4. Run the API:

   ```sh
   python api/main.py
   ```

## Building

You can build a standalone executable for your platform using the `build.py` script:

```sh
python build.py
```

This will create an executable file named `aichat` in the `dist` directory.

## Docker

To build and run the Docker container:

```sh
docker build -t ai-chat-api .
docker run -p 8001:8001 -e APP_SECRET=your_secret_here ai-chat-api
```

## Deployment

This project includes a `vercel.json` configuration file for easy deployment on Vercel. Make sure to set your APP_SECRET as an environment variable in your Vercel project settings.

## Quick Deploy

[![Deploy with Vercel](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/snailyp/aichats-reverse)

## Cloudflare Workers

```js
const BASE_URL = "https://ai-chats.org";
const APP_SECRET = "sk-123456"; // 在实际使用时，请使用更安全的方式存储和访问密钥
const ALLOWED_MODELS = ["gpt-4o", "gpt-4o-2024-05-13"];
addEventListener('fetch', event => {
  event.respondWith(handleRequest(event.request))
})
async function handleRequest(request) {
  if (request.method === "OPTIONS") {
    return handleCORS();
  }
  if (request.method === "POST" && new URL(request.url).pathname === "/v1/chat/completions") {
    return handleChatCompletions(request);
  }
  return new Response("Not Found", { status: 404 });
}
function handleCORS() {
  return new Response(null, {
    status: 200,
    headers: {
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "POST, OPTIONS",
      "Access-Control-Allow-Headers": "Content-Type, Authorization",
    },
  });
}
async function handleChatCompletions(request) {
  const authHeader = request.headers.get("Authorization");
  if (!authHeader || !authHeader.startsWith("Bearer ") || authHeader.split(" ")[1] !== APP_SECRET) {
    return new Response("Unauthorized", { status: 401 });
  }
  const requestData = await request.json();
  if (!ALLOWED_MODELS.includes(requestData.model)) {
    return new Response(`Model ${requestData.model} is not allowed. Allowed models are: ${ALLOWED_MODELS.join(", ")}`, { status: 400 });
  }
  const jsonData = {
    type: 'chat',
    messagesHistory: requestData.messages.map(msg => ({
      from: msg.role === 'user' ? 'you' : 'chatGPT',
      content: msg.content
    })),
  };
  const aiChatsResponse = await fetch(`${BASE_URL}/chat/send2/`, {
    method: 'POST',
    headers: {
      'accept': 'application/json, text/event-stream',
      'accept-language': 'zh-CN,zh;q=0.9',
      'content-type': 'application/json',
      'origin': BASE_URL,
      'referer': `${BASE_URL}/chat/`,
      'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
    },
    body: JSON.stringify(jsonData),
  });
  if (!aiChatsResponse.ok) {
    return new Response(`Error communicating with AI-Chats: ${aiChatsResponse.statusText}`, { status: 500 });
  }
  if (requestData.stream) {
    return handleStreamResponse(aiChatsResponse, requestData.model);
  } else {
    return handleNonStreamResponse(aiChatsResponse, requestData.model);
  }
}
function handleStreamResponse(response, model) {
  const { readable, writable } = new TransformStream();
  const writer = writable.getWriter();
  const encoder = new TextEncoder();
  const reader = response.body.getReader();
  readStream(reader, writer, encoder, model);
  return new Response(readable, {
    headers: { 'Content-Type': 'text/event-stream' },
  });
}
async function readStream(reader, writer, encoder, model) {
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const text = new TextDecoder().decode(value);
      const lines = text.split('\n');
      
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const content = line.slice(6).replace(' trylimit', '').replace(/\\n/g, '\n');
          const simulatedData = simulateData(content, model);
          await writer.write(encoder.encode(`data: ${JSON.stringify(simulatedData)}\n\n`));
        }
      }
    }
    await writer.write(encoder.encode("data: [DONE]\n\n"));
  } catch (error) {
    console.error('Stream reading error:', error);
  } finally {
    await writer.close();
  }
}
async function handleNonStreamResponse(response, model) {
  let fullResponse = "";
  const reader = response.body.getReader();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    fullResponse += new TextDecoder().decode(value);
  }
  fullResponse = fullResponse.replace(/^data: /gm, '').replace(/ trylimit/g, '').replace(/\\n/g, '\n');
  const responseData = {
    id: `chatcmpl-${crypto.randomUUID()}`,
    object: "chat.completion",
    created: Date.now(),
    model: model,
    choices: [
      {
        index: 0,
        message: {
          role: "assistant",
          content: fullResponse
        },
        finish_reason: "stop"
      }
    ],
    usage: null
  };
  return new Response(JSON.stringify(responseData), {
    headers: { 'Content-Type': 'application/json' },
  });
}
function simulateData(content, model) {
  return {
    id: `chatcmpl-${crypto.randomUUID()}`,
    object: "chat.completion.chunk",
    created: Date.now(),
    model: model,
    choices: [
      {
        index: 0,
        delta: {
          content: content,
          role: "assistant"
        },
        finish_reason: null
      }
    ],
    usage: null
  };
}

```

## Usage

Send POST requests to `/v1/chat/completions` with a JSON body containing the chat messages and model specification. Include your APP_SECRET in the Authorization header.
Example:

```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "Hello, how are you?"}
  ],
  "stream": false
}
```

## Supported Models

Currently, the API supports the following models:

- gpt-4o
- gpt-4o-2024-05-13

## Security

This API uses an APP_SECRET for authentication. Make sure to keep your APP_SECRET secure and not expose it in your client-side code.

## Disclaimer

This project is for educational purposes only. It is not affiliated with, authorized, maintained, sponsored or endorsed by ai-chats.org or any of its affiliates or subsidiaries. This software should not be used for any illegal activities or to violate the terms of service of ai-chats.org or any other service provider.
The authors and contributors of this project are not responsible for any misuse of this software or for any violation of terms of service of any third-party services used by this software. Users are solely responsible for ensuring their use of this software complies with all applicable laws and terms of service.
Use of this software is at your own risk. The authors and contributors provide no warranty or guarantee of any kind, express or implied.
