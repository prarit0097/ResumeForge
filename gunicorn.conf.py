"""Gunicorn config for ResumeForge.

PDF/PNG export uses a per-thread headless Chromium that is kept warm for the life
of the worker, so we run a small number of THREADED sync workers (not many
processes) to share those browsers and keep memory sane. Bind to a loopback port;
your nginx reverse-proxy forwards to it.
"""
import multiprocessing
import os

bind = os.environ.get("GUNICORN_BIND", "127.0.0.1:8001")
# Few processes, several threads each — good for our I/O-bound LLM + browser work.
workers = int(os.environ.get("WEB_CONCURRENCY", min(3, multiprocessing.cpu_count())))
threads = int(os.environ.get("GUNICORN_THREADS", 4))
worker_class = "gthread"
timeout = 120          # AI calls + PDF render can take a while
graceful_timeout = 30
keepalive = 5
max_requests = 1000    # recycle workers to bound any leaks (incl. Chromium)
max_requests_jitter = 100
accesslog = "-"
errorlog = "-"
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")
