import os
from dotenv import load_dotenv
import requests
import psycopg2
import model.config.constants as constants
import database as db
import numpy as np
from scipy.spatial.distance import cosine

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
        print("OPENAI_API_KEY is ready")  # todo delete all prints
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

            response = get_embeddings([current_question, current_answer])

            if response.status_code == 200:
                embeddings = response.json()["data"]
                current_question_embedding = embeddings[0]["embedding"]
                current_answer_embedding = embeddings[1]["embedding"]

                db.insert_into_embeddings(conn, cursor, current_question, current_answer, current_question_embedding,
                                          current_answer_embedding)

            else:
                raise ValueError(f"Error: {response.status_code}")


def process_embeddings_for_user(user_query):
    response = get_embeddings(user_query)

    if response.status_code == 200:
        data = response.json()["data"]
        user_query_embeddings = data[0]["embedding"]
        return user_query_embeddings
    else:
        raise ValueError(f"Error: {response.status_code}")


# Function to compute embeddings for a given input data using OpenAI API
def get_embeddings(input_data):
    payload = {
        "input": input_data,
        "model": constants.EMBEDDING_MODEL
    }
    headers = {
        "Content-Type": constants.CONTENT_TYPE,
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    response = requests.post(constants.OPENAI_API_URL_EMBEDDINGS, json=payload, headers=headers)
    return response


# STEP 2 - Similarity Search
# finds the most similar question and  compute the similarity between a user's query and the questions in the FAQ database
def similarity_search(user_query_embedding, faq_questions_embeddings, faq_questions, faq_answers,
                      similarity_threshold):
    similarities = [1 - cosine(user_query_embedding, faq_question_embedding) for faq_question_embedding in
                    faq_questions_embeddings]

    # Check if any similarity scores are above the similarity_threshold
    valid_similarity_scores = [similarity for similarity in similarities if similarity >= similarity_threshold]

    if valid_similarity_scores:
        max_similarity_index = np.argmax(similarities)
        max_similarity_score = similarities[max_similarity_index]
        return faq_questions[max_similarity_index], faq_answers[max_similarity_index], max_similarity_score
    else:
        return None, None, None


def decide_use_openai(similarity_score, similarity_threshold):
    if similarity_score is None or similarity_score < similarity_threshold:
        return True  # Use OpenAI API
    else:
        return False  # Use local FAQ database


# Function to interact with OpenAI API to get an answer
def get_answer_from_openai(query):
    payload = {
        "prompt": query,
        "max_tokens": 100,
        "model": "gpt-3.5-turbo-instruct"
    }
    headers = {
        "Content-Type": constants.CONTENT_TYPE,
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    response = requests.post(constants.OPENAI_API_URL_COMPLETIONS, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["text"]
    else:
        raise ValueError(f"Error: {response.status_code}")


def process_query(conn, user_query, similarity_threshold):
    user_query_embedding = process_embeddings_for_user(user_query)

    faq_questions, faq_questions_embeddings, faq_answers = db.retrieve_embeddings_from_database(conn)

    best_match_question, best_match_answer, similarity_score = similarity_search(user_query_embedding,
                                                                                 faq_questions_embeddings,
                                                                                 faq_questions, faq_answers,
                                                                                 similarity_threshold)

    use_openai = decide_use_openai(similarity_score, similarity_threshold)

    if use_openai:
        answer_from_openai = get_answer_from_openai(user_query)
        return answer_from_openai
    else:
        return best_match_answer


if __name__ == "__main__":
    if (check_if_openai_api_key_exists()):  # TRUE
        with psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT) as conn:
            with conn.cursor() as cursor:
                if not db.table_exists(conn, cursor):
                    db.create_embeddings_table(conn, cursor)
                    if not db.constraint_exists(conn, cursor):
                        db.add_unique_constraint(conn, cursor)

        compute_embeddings(conn, constants.FAQ_DATABASE)

        user_query = "What fruits have blue color?"
        answer = process_query(conn, user_query, constants.SIMILARITY_THRESHOLD)
        print("Question: ", user_query)
        print("Answer:", answer)

        cursor.close()
        conn.close()
