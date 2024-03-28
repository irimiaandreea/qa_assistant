import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, Header, APIRouter
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

from model.exceptions.custom_exceptions import NoOpenAIKeyError, RequestError
from model.qa_system.database import *
from model.qa_system.main_model import compute_embeddings, process_user_query

load_dotenv(dotenv_path="model/config/.env")

app = FastAPI()
router = APIRouter()

# todo rename the package model , qa_system and main_model.py

# PostgreSQL
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


class UserQuestion(BaseModel):
    user_question: str


class AnswerResponse(BaseModel):
    source: str
    matched_question: str
    answer: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@app.post("/token")
async def token(form_data: OAuth2PasswordRequestForm = Depends()):
    return {"access_token": form_data.username + "token"}


@app.get("/")
async def index(token: str = Depends(oauth2_scheme)):
    return {"token": token}


def check_if_openai_api_key_exists():
    if os.getenv("OPENAI_API_KEY"):
        return True
    else:
        return False


# Define a dependency to get the access token from the request headers
def get_token(authorization: str = Header(None)):
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is missing")

    # Assuming the token is in the format "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid authentication scheme")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    return token


# STEP 4 - Design FastAPI Endpoint
@app.post("/ask-question")
async def ask_question(user_question: UserQuestion):
    try:
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
