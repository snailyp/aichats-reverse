# AI 聊天 API

[English](README.md) | [中文](README-CH.md)

本项目提供了一个 AI 聊天功能的 API 接口，利用 ai-chats.org 服务。它使用 FastAPI 构建，可以作为独立应用程序、Docker 容器或在 Vercel 上部署。

## 功能特点

- 兼容 OpenAI API 格式的聊天完成 API 端点
- 支持流式和非流式响应选项
- 支持跨源资源共享（CORS）
- 提供日志记录，便于调试和监控
- 支持 `gpt-4o/gpt-4o-2024-05-13` 模型

## 设置和安装

1. 克隆仓库
2. 安装依赖：

   ```sh
   pip install -r requirements.txt
   ```

3. 设置环境变量：
   - 在根目录创建 `.env` 文件
   - 添加你的 APP_SECRET：`APP_SECRET=你的密钥`
4. 运行 API：

   ```sh
   python api/main.py
   ```

## 构建

你可以使用 `build.py` 脚本为你的平台构建独立可执行文件：

```sh
python build.py
```

这将在 `dist` 目录中创建一个名为 `aichat` 的可执行文件。

## Docker

构建和运行 Docker 容器：

```sh
docker build -t ai-chat-api .
docker run -p 8001:8001 -e APP_SECRET=你的密钥 ai-chat-api
```

## 部署

本项目包含一个 `vercel.json` 配置文件，便于在 Vercel 上部署。确保在 Vercel 项目设置中将 APP_SECRET 设置为环境变量。

## 快速部署

[![使用 Vercel 部署](https://vercel.com/button)](https://vercel.com/new/clone?repository-url=https://github.com/snailyp/aichats-reverse)

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

## 使用方法

向 `/v1/chat/completions` 发送 POST 请求，请求体中包含聊天消息和模型规格的 JSON。在 Authorization 头中包含你的 APP_SECRET。
示例：

```json
{
  "model": "gpt-4o",
  "messages": [
    {"role": "user", "content": "你好，你好吗？"}
  ],
  "stream": false
}
```

## 支持的模型

目前，API 支持以下模型：

- gpt-4o
- gpt-4o-2024-05-13

## 安全性

此 API 使用 APP_SECRET 进行身份验证。确保保管好你的 APP_SECRET，不要在客户端代码中暴露它。

## 免责声明

本项目仅用于教育目的。它不隶属于 ai-chats.org 或其任何附属机构或子公司，也未经其授权、维护、赞助或认可。本软件不应用于任何非法活动或违反 ai-chats.org 或任何其他服务提供商的服务条款。
本项目的作者和贡献者不对本软件的任何滥用或违反任何第三方服务条款的行为负责。用户应自行负责确保其使用本软件符合所有适用法律和服务条款。
使用本软件风险自负。作者和贡献者不提供任何形式的明示或暗示的保证或担保。
