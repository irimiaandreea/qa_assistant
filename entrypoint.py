import base64
import secrets
from datetime import datetime, timedelta

from cryptography.fernet import Fernet
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from components.exceptions.custom_exceptions import NoOpenAIKeyError, RequestError
from components.qa_system.database_operations import *
from components.qa_system.faq_search import compute_embeddings, process_user_query

load_dotenv(dotenv_path="components/config/.env")

jwt_secret_key = secrets.token_urlsafe(32)
fernet_secret_key = Fernet.generate_key()
encoded_fernet_secret_key = base64.urlsafe_b64encode(fernet_secret_key).decode('utf-8')
os.environ['JWT_SECRET_KEY'] = jwt_secret_key
os.environ['FERNET_SECRET_KEY'] = encoded_fernet_secret_key

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
ALGORITHM = constants.JWT_ALGORITHM

app = FastAPI()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class UserQuestion(BaseModel):
    user_question: str


class UserDetails(BaseModel):
    username: str
    password: str


class AnswerResponse(BaseModel):
    source: str
    matched_question: str
    answer: str


class Token(BaseModel):
    refresh_token: str


def check_if_openai_api_key_exists():
    if os.getenv("OPENAI_API_KEY"):
        return True
    else:
        return False


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
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@app.post("/register")
async def register(user: UserDetails):
    hashed_password = pwd_context.hash(user.password)
    insert_into_users(user.username, hashed_password)
    return {"message": "User registered successfully"}


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_token(data={"sub": user.username}, expires_delta=access_token_expires)

    refresh_token_expires = timedelta(days=constants.REFRESH_TOKEN_EXPIRE_DAYS)
    refresh_token = create_token(data={"sub": user.username}, expires_delta=refresh_token_expires)

    return {"access_token": access_token, "token_type": "bearer", "refresh_token": refresh_token}


@app.post("/refresh-token")
async def refresh_token(token: Token):
    try:
        payload = jwt.decode(token.refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        access_token_expires = timedelta(minutes=constants.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_token(data={"sub": username}, expires_delta=access_token_expires)

        return {"access_token": access_token, "token_type": "bearer"}

    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")


# STEP 4 - Design FastAPI Endpoint to post user's question
@app.post("/ask-question")
async def ask_question(user_question: UserQuestion, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        if not check_if_openai_api_key_exists():  # TRUE
            raise NoOpenAIKeyError("No OpenAI API key found")

        conn = get_connection()

        if conn:
            with conn.cursor() as cursor:
                create_embeddings_table(conn, cursor)
                create_user_table(conn, cursor)
                if not embeddings_constraint_exists(conn, cursor):
                    add_embeddings_constraint(conn, cursor)
                    if not users_constraint_exists(conn, cursor):
                        add_users_constraint(conn, cursor)

        compute_embeddings(conn, constants.FAQ_DATABASE)

        source, question, answer = process_user_query(conn, user_question.user_question, constants.SIMILARITY_THRESHOLD)
        cursor.close()
        conn.close()

        return AnswerResponse(source=source, matched_question=question, answer=answer)

    except NoOpenAIKeyError as exception:
        raise HTTPException(status_code=500, detail=str(exception))
    except psycopg2.Error as exception:
        raise DatabaseError("Database error: " + str(exception))
    except RequestError as exception:
        raise HTTPException(status_code=500, detail=str(exception))
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))