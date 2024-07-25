
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
