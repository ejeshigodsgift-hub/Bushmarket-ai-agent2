# =========================================
# APP
# =========================================
APP_NAME=BushmarketBackend
ENV=development

# =========================================
# DATABASE
# =========================================
DATABASE_URL=postgresql+asyncpg://postgres_user:postgres_password@localhost:5432/bushmarket_db

# =========================================
# REDIS
# =========================================
REDIS_URL=redis://localhost:6379/0

# =========================================
# KAFKA
# =========================================
KAFKA_BOOTSTRAP_SERVERS=localhost:9092
KAFKA_CLIENT_ID=bushmarket-event-bus

KAFKA_AGENT_TASK_TOPIC=agent.task.created
KAFKA_AGENT_UPDATE_TOPIC=agent.task.updated

# =========================================
# SECURITY
# =========================================
SECRET_KEY=CHANGE_THIS_IN_PRODUCTION

JWT_ALGORITHM=HS256

ACCESS_TOKEN_EXPIRE_MINUTES=60
REFRESH_TOKEN_EXPIRE_DAYS=7
INTERNAL_JWT_EXPIRE_MINUTES=30

# =========================================
# SESSION
# =========================================
SESSION_EXPIRE_SECONDS=86400

COOKIE_NAME=bushmarket_session
COOKIE_SECURE=false
COOKIE_SAMESITE=lax
COOKIE_DOMAIN=localhost

# =========================================
# CSRF
# =========================================
CSRF_COOKIE_NAME=csrf_token
CSRF_HEADER_NAME=x-csrf-token

# =========================================
# RATE LIMITING
# =========================================
LOGIN_RATE_LIMIT=5
LOGIN_RATE_LIMIT_WINDOW=60