import os
from dotenv import load_dotenv
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException
from model.qa_system.main_model import compute_embeddings, process_user_query
from model.exceptions.custom_exceptions import NoOpenAIKeyError
from model.qa_system.database import *

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


def check_if_openai_api_key_exists():
    print("OPENAI_API_KEY ", OPENAI_API_KEY)
    if os.getenv("OPENAI_API_KEY"):
        return True
    else:
        return False


# Define endpoint for asking questions
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

        answer = process_user_query(conn, user_question.user_question, constants.SIMILARITY_THRESHOLD)
        cursor.close()
        conn.close()

        return answer

    except NoOpenAIKeyError:
        raise HTTPException(status_code=500, detail="No OpenAI API key found")
    except psycopg2.OperationalError as exception:
        raise DatabaseError("Database error: " + str(exception))
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))
