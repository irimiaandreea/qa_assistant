import secrets
from datetime import datetime, timedelta

from fastapi import HTTPException, Depends, status, APIRouter
from fastapi.security import OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from components.qa_system.database_operations import *

router = APIRouter()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserDetails(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    refresh_token: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password: str):
    user = get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.password):
        return False
    return user


def create_token(data: dict, expires_delta: timedelta):
    to_encode = data.copy()
    expire = datetime.utcnow() + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, constants.JWT_SECRET_KEY, algorithm=constants.JWT_ALGORITHM)
    return encoded_jwt


@router.post("/register")
async def register(user: UserDetails):
    hashed_password = pwd_context.hash(user.password)
    insert_into_users(user.username, hashed_password)
    return {"message": "User registered successfully"}


@router.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(data={"sub": user.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=constants.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@router.post("/refresh-token")
async def refresh_token(token: Token):
    try:
        payload = jwt.decode(token.refresh_token, constants.JWT_SECRET_KEY, algorithms=[constants.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(data={"sub": username}, expires_delta=access_token_expires)

        return {"access_token": access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")
