# ----------------------------------------------------------------------------
#  File:        gunicorn_config.py
#  Project:     Celaya Solutions AI Know It All
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Gunicorn configuration for production deployment
#  Version:     1.0.0
#  License:     MIT (SPDX-Identifier: MIT)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

import multiprocessing
import os

# Bind to 0.0.0.0:8080 by default, can be overridden with environment variables
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8080")

# Use 2-4 workers per CPU core
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))

# Use threads for concurrent requests within each worker
threads = int(os.getenv("GUNICORN_THREADS", 4))

# Timeout for worker processes (in seconds)
timeout = int(os.getenv("GUNICORN_TIMEOUT", 120))

# Maximum number of requests a worker will process before restarting
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", 1000))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", 50))

# Worker class (use gevent for async I/O)
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "gevent")

# Access log format
accesslog = os.getenv("GUNICORN_ACCESS_LOG", "-")  # "-" means stdout
errorlog = os.getenv("GUNICORN_ERROR_LOG", "-")    # "-" means stderr
loglevel = os.getenv("GUNICORN_LOG_LEVEL", "info")

# Preload application to save memory
preload_app = os.getenv("GUNICORN_PRELOAD_APP", "true").lower() == "true"

# Daemon mode (run in background)
daemon = os.getenv("GUNICORN_DAEMON", "false").lower() == "true" 