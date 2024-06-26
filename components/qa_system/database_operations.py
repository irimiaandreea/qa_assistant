import json
import os

import psycopg2

import components.config.constants as constants
from components.exceptions.custom_exceptions import DatabaseError
from components.models.Embedding import Embedding
from components.models.User import User

# PostgreSQL
POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")


def get_connection():
    try:
        conn = psycopg2.connect(dbname=POSTGRES_DB, user=POSTGRES_USER, password=POSTGRES_PASSWORD, host=POSTGRES_HOST,
                                port=POSTGRES_PORT)
        return conn
    except psycopg2.OperationalError as exception:
        raise DatabaseError(f"Error connection to database: {exception}")


def insert_into_embeddings(conn, cursor, current_question, current_answer, current_question_embedding,
                           current_answer_embedding):
    try:
        cursor.execute(constants.INSERT_INTO_EMBEDDINGS_TABLE_QUERY,
                       (current_question, json.dumps(current_question_embedding), current_answer,
                        json.dumps(current_answer_embedding)))
        conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error inserting data into database: {exception}")


def insert_into_users(username, hashed_password):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(constants.INSERT_INTO_USERS_TABLE_QUERY, (username, hashed_password))
                conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error insert user in users: {exception}")


def get_user_by_username(username: str):
    try:
        with get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute(constants.GET_USER_QUERY, (username,))
                user_data = cursor.fetchone()
                if user_data:
                    return User(id=user_data[0], username=user_data[1], password=user_data[2])
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error get user by username from users: {exception}")


def retrieve_embeddings_from_database(conn):
    try:
        with conn.cursor() as cursor:
            cursor.execute(constants.GET_EMBEDDINGS_QUERY)
            conn.commit()
            rows = cursor.fetchall()

            embeddings = []

            for row in rows:
                embedding = Embedding(id=row[0], question=row[1], question_embedding=row[2], answer=row[3])
                embeddings.append(embedding)

        return embeddings
    except psycopg2.Error as exception:
        raise DatabaseError(f"Error retrieving embeddings from database: {exception}")
