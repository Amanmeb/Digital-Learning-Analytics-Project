class AuditEvent:
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"

    REGISTER = "user_registered"

    PASSWORD_CHANGED = "password_changed"
    PASSWORD_RESET_REQUESTED = "password_reset_requested"
    PASSWORD_RESET_COMPLETED = "password_reset_completed"

    REFRESH_TOKEN = "refresh_token_used"
    LOGOUT = "logout"
    LOGOUT_ALL = "logout_all"

    ACCOUNT_LOCKED = "account_locked"