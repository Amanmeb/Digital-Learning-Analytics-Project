from app.services.audit import log_event


async def log_rbac_event(db, user, action, request, allowed, status):
    await log_event(
        db=db,
        user_id=user.get("user_id"),
        event="rbac_check",
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        metadata={
            "action": action,
            "allowed": allowed,
            "status": status,
            "role": user.get("role"),
        },
    )