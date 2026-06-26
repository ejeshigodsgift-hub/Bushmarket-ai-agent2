import logging
import sys

=====================================================

LOG FORMAT

=====================================================

LOG_FORMAT = (
"%(asctime)s | "
"%(levelname)s | "
"%(name)s | "
"%(filename)s:%(lineno)d | "
"%(message)s"
)

=====================================================

CONFIGURE LOGGING

=====================================================

def configure_logging():

root_logger = logging.getLogger()

# Prevent duplicate handlers on reload
if root_logger.handlers:
    return

root_logger.setLevel(logging.INFO)

console_handler = logging.StreamHandler(sys.stdout)

console_handler.setLevel(logging.INFO)

console_handler.setFormatter(
    logging.Formatter(LOG_FORMAT)
)

root_logger.addHandler(console_handler)

# Reduce noisy libraries
logging.getLogger("httpx").setLevel(
    logging.WARNING
)

logging.getLogger("openai").setLevel(
    logging.INFO
)

logging.getLogger("uvicorn").setLevel(
    logging.INFO
)

logging.getLogger("uvicorn.access").setLevel(
    logging.INFO
)

logging.getLogger("sqlalchemy.engine").setLevel(
    logging.WARNING
)

=====================================================

INITIALIZE LOGGING

=====================================================

configure_logging()

=====================================================

APPLICATION LOGGER

=====================================================

logger = logging.getLogger("bushmarket")

=====================================================

OPTIONAL HELPERS

=====================================================

def log_ai_request(user_id: str, message: str):

logger.info(
    f"AI request | user={user_id} | "
    f"message={message}"
)

def log_ai_intent(
user_id: str,
intent: str
):

logger.info(
    f"AI intent | user={user_id} | "
    f"intent={intent}"
)

def log_payment_event(
reference: str,
status: str
):

logger.info(
    f"Payment event | "
    f"reference={reference} | "
    f"status={status}"
)

def log_listing_event(
listing_id: str,
action: str
):

logger.info(
    f"Listing event | "
    f"listing={listing_id} | "
    f"action={action}"
)

def log_cooperative_event(
cooperative_id: str,
action: str
):

logger.info(
    f"Cooperative event | "
    f"cooperative={cooperative_id} | "
    f"action={action}"
)