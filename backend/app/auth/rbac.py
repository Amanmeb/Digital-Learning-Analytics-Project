from fastapi import Depends, HTTPException, status
from functools import wraps

from app.auth.deps import get_current_user
from app.auth.roles import Roles

def require_roles(*allowed_roles: Roles):
    """
    Dependency-based RBAC guard (production safe)
    """

    async def role_checker(current_user=Depends(get_current_user)):

        user_role = current_user.get("role")

        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )

        if user_role not in [r.value for r in allowed_roles]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return role_checker

# def require_roles(*allowed_roles):
#     def decorator(func):
#         @wraps(func)
#         async def wrapper(*args, current_user=Depends(get_current_user), **kwargs):

#             user_role = current_user.get("role")

#             if user_role not in allowed_roles:
#                 raise HTTPException(
#                     status_code=status.HTTP_403_FORBIDDEN,
#                     detail="Insufficient permissions"
#                 )

#             return await func(*args, current_user=current_user, **kwargs)

#         return wrapper
#     return decorator

