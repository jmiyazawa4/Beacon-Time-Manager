"""Production entry point behind a managed HTTPS reverse proxy."""
import os
bind = '0.0.0.0:' + str(int(os.environ.get('PORT', '8000')))
# One process preserves the shared cache and the athletics crawl budget.
workers = 1
worker_class = 'gthread'
threads = 8
timeout = 120
graceful_timeout = 30
keepalive = 3
limit_request_line = 2048
limit_request_fields = 50
limit_request_field_size = 8190
max_requests = 1000
max_requests_jitter = 100
accesslog = None
errorlog = '-'
loglevel = 'warning'
capture_output = False
