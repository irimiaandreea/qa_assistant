import os

import numpy as np
import requests
from dotenv import load_dotenv
from openai import OpenAIError
from scipy.spatial.distance import cosine

import components.config.constants as constants
import components.qa_system.database_operations as db
from components.exceptions.custom_exceptions import *

load_dotenv(dotenv_path="../config/.env")
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')


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
                raise EmbeddingError(f"Error computing embeddings: {response.status_code}")


def process_embeddings_for_user(user_question):
    response = get_embeddings(user_question)

    if response.status_code == 200:
        data = response.json()["data"]
        user_question_embeddings = data[0]["embedding"]
        return user_question_embeddings
    else:
        raise EmbeddingError(f"Error computing embeddings: {response.status_code}")


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

    try:
        response = requests.post(constants.OPENAI_API_URL_EMBEDDINGS, json=payload, headers=headers)
        return response
    except requests.exceptions.RequestException as exception:
        raise RequestError(f"Error occurred during HTTP request: {exception}")
    except OpenAIError as exception:
        raise OpenAIError(f"Error occurred during OpenAI API request: {exception}")


# STEP 2 - Similarity Search
# finds the most similar question and  compute the similarity between a user's query and the questions in the FAQ database
def similarity_search(user_query_embedding, faq_questions, faq_questions_embeddings, faq_answers,
                      similarity_threshold):
    similarities = [1 - cosine(user_query_embedding, faq_question_embedding) for faq_question_embedding in
                    faq_questions_embeddings]

    # Check if any similarity scores are above the similarity_threshold
    valid_similarity_scores = [similarity for similarity in similarities if similarity >= similarity_threshold]

    if valid_similarity_scores:
        max_similarity_index = np.argmax(similarities)
        max_similarity_score = similarities[max_similarity_index]
        return faq_answers[max_similarity_index], faq_questions[max_similarity_index], max_similarity_score
    else:
        return None, None, None


# STEP 3 - Interacting with OpenAI API
def decide_use_openai(similarity_score, similarity_threshold):
    if similarity_score is None or similarity_score < similarity_threshold:
        return True  # Use OpenAI API
    else:
        return False  # Use local FAQ database


# Function to interact with OpenAI API to get an answer
def get_answer_from_openai(user_query):
    payload = {
        "model": constants.OPENAI_GET_ANSWER_MODEL,
        "messages": [
            {
                "role": "user",
                "content": user_query
            }
        ]
    }
    headers = {
        "Content-Type": constants.CONTENT_TYPE,
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }

    try:
        response = requests.post(constants.OPENAI_API_URL_COMPLETIONS, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()

            if data.get("choices"):
                return data["choices"][0]["message"]["content"]
            else:
                return "There is no response from OpenAI API."
    except requests.exceptions.RequestException as exception:
        raise RequestError(f"Error occurred during HTTP request: {exception}")
    except OpenAIError as exception:
        raise OpenAIError(f"Error occurred during OpenAI API request: {exception}")


def process_user_query(conn, user_question, similarity_threshold):
    user_question_embedding = process_embeddings_for_user(user_question)

    embeddings = db.retrieve_embeddings_from_database(conn)

    faq_questions = [embedding.question for embedding in embeddings]
    faq_questions_embeddings = [embedding.question_embedding for embedding in embeddings]
    faq_answers = [embedding.answer for embedding in embeddings]

    answer_from_local_faq, question_from_local_faq, similarity_score = similarity_search(user_question_embedding,
                                                                                         faq_questions,
                                                                                         faq_questions_embeddings,
                                                                                         faq_answers,
                                                                                         similarity_threshold)

    use_openai = decide_use_openai(similarity_score, similarity_threshold)

    if use_openai:
        answer_from_openai = get_answer_from_openai(user_question)
        return "openai", "N/A", answer_from_openai
    else:
        return "local", question_from_local_faq, answer_from_local_faq
