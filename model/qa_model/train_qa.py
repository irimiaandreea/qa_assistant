import os
from dotenv import load_dotenv
import requests
import psycopg2
import model.config.constants as constants
import database as db

load_dotenv(dotenv_path="../config/.env")

# PostgreSQL
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# OpenAI
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


def check_if_openai_api_key_exists():
    if os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is ready")
        return True
    else:
        print("OPENAI_API_KEY environment variable not found")
        return False


# STEP 1 - Compute embeddings for FAQ questions & answers
def compute_embeddings(conn, faq_database):
    with conn.cursor() as cursor:
        for faq_entry in faq_database:
            current_question = faq_entry["question"]
            current_answer = faq_entry["answer"]

            # Create payload for the request
            payload = {
                "input": [current_question, current_answer],
                "model": constants.EMBEDDING_MODEL
            }

            # Set headers
            headers = {
                "Content-Type": constants.CONTENT_TYPE_JSON,
                "Authorization": f"Bearer {OPENAI_API_KEY}"
            }

            # Send request to OpenAI API to generate embeddings
            response = requests.post(constants.OPENAI_API_URL_EMBEDDINGS, json=payload, headers=headers)

            if response.status_code == 200:
                embeddings = response.json()["data"]
                current_question_embedding = embeddings[0]["embedding"]
                current_answer_embedding = embeddings[1]["embedding"]

                db.insert_into_embeddings(conn, cursor, current_question, current_answer, current_question_embedding,
                                       current_answer_embedding)

            else:
                raise ValueError(f"Error: {response.status_code}")


if __name__ == "__main__":
    if (check_if_openai_api_key_exists()):  # TRUE
        with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                db.create_embeddings_table(conn, cursor)

        compute_embeddings(conn, constants.FAQ_DATABASE)

        cursor.close()
        conn.close()
