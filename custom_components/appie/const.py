"""Constants for the Albert Heijn boodschappenlijst integration."""

DOMAIN = "appie"

CONF_SCAN_INTERVAL = "scan_interval"
DEFAULT_SCAN_INTERVAL = 60  # seconds

# Token/session fields stored in the config entry.
CONF_ACCESS_TOKEN = "access_token"
CONF_REFRESH_TOKEN = "refresh_token"
CONF_MEMBER_ID = "member_id"
CONF_EXPIRES_AT = "expires_at"

SERVICE_ADD_ITEM = "add_item"
SERVICE_CHECKOUT = "checkout"
SERVICE_CLEAR_LIST = "clear_list"

ATTR_NAME = "name"
ATTR_QUANTITY = "quantity"
ATTR_FREE_TEXT = "free_text"
