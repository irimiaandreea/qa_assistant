import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from model.exceptions.custom_exceptions import NoOpenAIKeyError, RequestError
from model.qa_system.database import *
from model.qa_system.main_model import compute_embeddings, process_user_query

app = FastAPI()
load_dotenv(dotenv_path="model/config/.env")

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


def check_if_openai_api_key_exists():
    if os.getenv("OPENAI_API_KEY"):
        return True
    else:
        return False


# STEP 4 - Design FastAPI Endpoint
@app.post("/ask-question")
async def ask_question(user_question: UserQuestion):
    try:
        if not check_if_openai_api_key_exists():  # TRUE
            raise NoOpenAIKeyError("No OpenAI API key found")

        with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST,
                              port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                if not table_exists(conn, cursor):
                    create_embeddings_table(conn, cursor)
                    if not constraint_exists(conn, cursor):
                        add_unique_constraint(conn, cursor)

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
