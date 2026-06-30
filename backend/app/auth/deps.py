from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.security import decode_token

auth_scheme = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
):
    token = credentials.credentials
    return decode_token(token)



# from fastapi import Depends, HTTPException, status
# from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
# from app.auth.security import decode_token

# auth_scheme = HTTPBearer()

# async def get_current_user(
#     credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
# ):
#     token = credentials.credentials
#     payload = decode_token(token)

#     if not payload:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid or expired token",
#         )

#     return {
#         "user_id": payload["user_id"],
#         "role": payload.get("role", "student"),
#     }



# auth_scheme = HTTPBearer()

# async def get_current_user(authorization: str = Header(None)):
#     if not authorization:
#         raise HTTPException(status_code=401, detail="Missing token")

#     if authorization != "Bearer test-token":
#         raise HTTPException(status_code=403, detail="Invalid token")

# def get_current_user(token=Depends(auth_scheme)):
#     payload = decode_token(token.credentials)

#     if payload is None:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid or expired token"
#         )
    

#     user_id = payload.get("user_id")

#     if not user_id:
#         raise HTTPException(
#             status_code=401,
#             detail="Token missing user_id"
#         )

#     return {
#         "user_id": user_id,
#         "role": "tester"
#     }

 

# from fastapi import Depends, HTTPException
# from fastapi.security import HTTPBearer
# from jose import JWTError
# from app.auth.security import decode_token

# auth_scheme = HTTPBearer()

# def get_current_user(token=Depends(auth_scheme)):
#     payload = decode_token(token.credentials)

#     if not payload:
#         raise HTTPException(status_code=401, detail="Invalid token")

#     return payload