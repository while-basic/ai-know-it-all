# Deployment Guide for AI Know It All

This guide provides instructions for deploying the AI Know It All application in a production environment.

## Prerequisites

- Python 3.9+ installed
- Nginx or another reverse proxy (optional but recommended)
- Systemd for service management (Linux)
- Git

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/ai-know-it-all.git
   cd ai-know-it-all
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```
   FLASK_SECRET_KEY=your-secure-secret-key
   MEMORY_PATH=/path/to/memory/storage
   MODEL_NAME=sushruth/solar-uncensored:latest
   USE_OBSIDIAN=true
   OBSIDIAN_PATH=/path/to/obsidian/vault
   OBSIDIAN_API_URL=127.0.0.1
   OBSIDIAN_API_PORT=27124
   OBSIDIAN_API_TOKEN=your-api-token
   ```

## Running with Gunicorn

For production deployments, we recommend using Gunicorn with the provided configuration:

```bash
gunicorn -c gunicorn_config.py wsgi:application
```

## Setting Up as a Systemd Service

1. Copy the service file to the systemd directory:
   ```bash
   sudo cp ai-know-it-all.service /etc/systemd/system/
   ```

2. Edit the service file to match your installation path:
   ```bash
   sudo nano /etc/systemd/system/ai-know-it-all.service
   ```

3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable ai-know-it-all
   sudo systemctl start ai-know-it-all
   ```

4. Check the service status:
   ```bash
   sudo systemctl status ai-know-it-all
   ```

## Nginx Configuration

For production deployments, we recommend using Nginx as a reverse proxy. Here's a sample configuration:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/ai-know-it-all/static/;
        expires 7d;
    }
}
```

## Environment Variables

The application can be configured using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| FLASK_SECRET_KEY | Secret key for Flask sessions | ai-know-it-all-secret-key |
| MEMORY_PATH | Path to store memory files | ./data/memory |
| MODEL_NAME | Name of the LLM model to use | sushruth/solar-uncensored:latest |
| USE_OBSIDIAN | Whether to use Obsidian integration | true |
| OBSIDIAN_PATH | Path to the Obsidian vault | /Users/chriscelaya/ObsidianVaults |
| OBSIDIAN_API_URL | URL for the Obsidian API | 127.0.0.1 |
| OBSIDIAN_API_PORT | Port for the Obsidian API | 27124 |
| OBSIDIAN_API_TOKEN | Token for the Obsidian API | (none) |
| PORT | Port for the Flask app to listen on | 8080 |
| FLASK_DEBUG | Whether to run Flask in debug mode | false |

## Gunicorn Configuration

The Gunicorn configuration can be adjusted using the following environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| GUNICORN_BIND | Address to bind to | 0.0.0.0:8080 |
| GUNICORN_WORKERS | Number of worker processes | (2 * CPU cores) + 1 |
| GUNICORN_THREADS | Number of threads per worker | 4 |
| GUNICORN_TIMEOUT | Worker timeout in seconds | 120 |
| GUNICORN_MAX_REQUESTS | Max requests per worker before restart | 1000 |
| GUNICORN_WORKER_CLASS | Worker class to use | gevent |
| GUNICORN_PRELOAD_APP | Whether to preload the application | true |

## Health Check

The application provides a health check endpoint at `/health` that returns the current status. This can be used for monitoring and load balancer configuration.

## Troubleshooting

- Check the logs for errors:
  ```bash
  sudo journalctl -u ai-know-it-all
  ```

- Make sure the application has appropriate permissions to read/write to the memory directory.

- If using Obsidian integration, ensure the Obsidian API is accessible from the server. 