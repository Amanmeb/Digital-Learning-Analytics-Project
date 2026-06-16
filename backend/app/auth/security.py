from typing import Optional
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from jose import jwt, JWTError



# -------------------------
# CONFIG
# -------------------------

SECRET_KEY = "super-secret-change-me"
ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------
# PASSWORD HASHING
# -------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -------------------------
# JWT TOKEN
# -------------------------
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()

    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=60)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

# import os
# from datetime import datetime, timedelta, timezone

# from jose import jwt, JWTError
# from passlib.context import CryptContext
# from fastapi import HTTPException, status



# SECRET_KEY = os.getenv("SECRET_KEY", "dev-insecure-key")

# if SECRET_KEY == "dev-insecure-key":
#     print("WARNING: Using insecure default SECRET_KEY")

# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# def verify_password(plain: str, hashed: str) -> bool:
#     return pwd_context.verify(plain, hashed)




#     expire = datetime.now(timezone.utc) + (
#         expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )

#     to_encode.update({"exp": expire})

#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def decode_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

#         if "sub" not in payload:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token payload",
#             )

#         return {
#             "user_id": payload["sub"],
#             "role": payload.get("role", "student"),
#         }

#     except JWTError:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid or expired token",
#         )
    

# from datetime import datetime, timedelta, timezone
# from jose import jwt, JWTError
# from passlib.context import CryptContext
# from fastapi import HTTPException, status

# # SECRET_KEY = "CHANGE_THIS"
# SECRET_KEY = os.getenv("SECRET_KEY")
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# def verify_password(plain: str, hashed: str) -> bool:
#     return pwd_context.verify(plain, hashed)


# def create_access_token(data: dict, expires_delta: timedelta | None = None):
#     to_encode = data.copy()

#     expire = datetime.now(timezone.utc) + (
#         expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     )

#     to_encode.update({"exp": expire})

#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def decode_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

#         if "sub" not in payload:
#             raise HTTPException(
#                 status_code=status.HTTP_401_UNAUTHORIZED,
#                 detail="Invalid token",
#             )

#         return {
#             "user_id": payload["sub"],
#             "role": payload.get("role", "student"),
#         }

#     except JWTError:
#         raise HTTPException(
#             status_code=401,
#             detail="Invalid or expired token",
#         )


# def decode_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload
#     except JWTError:
#         return None
    

    
# from datetime import datetime, timedelta
# from jose import jwt, JWTError
# from passlib.context import CryptContext

# SECRET_KEY = "CHANGE_THIS_TO_ENV_SECRET"
# ALGORITHM = "HS256"
# ACCESS_TOKEN_EXPIRE_MINUTES = 60

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# def hash_password(password: str) -> str:
#     return pwd_context.hash(password)


# def verify_password(plain: str, hashed: str) -> bool:
#     return pwd_context.verify(plain, hashed)


# def create_access_token(data: dict):
#     to_encode = data.copy()
#     expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
#     to_encode.update({"exp": expire})
#     return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# def decode_token(token: str):
#     try:
#         return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#     except JWTError:
#         return None