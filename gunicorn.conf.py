import os

bind = "0.0.0.0:" + os.environ.get("PORT", "10000")
workers = 2
timeout = 120
keepalive = 5
accesslog = "-"
errorlog = "-"
loglevel = info
