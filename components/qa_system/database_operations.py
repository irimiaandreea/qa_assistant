import json
import os

import psycopg2
# from dotenv import load_dotenv

import components.config.constants as constants
from components.exceptions.custom_exceptions import DatabaseError
from components.models.Embedding import Embedding
from components.models.User import User
import logging  # Import the logging module

# load_dotenv(dotenv_path="qa_assistent/../.env")

# PostgreSQL
DB_NAME = os.getenv("POSTGRES_DB")
DB_USER = os.getenv("POSTGRES_USER")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD")
DB_HOST = os.getenv("POSTGRES_HOST")
DB_PORT = os.getenv("POSTGRES_PORT")

logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG


def get_connection():
    try:
        logging.debug(f"Connecting to PostgreSQL: dbname={DB_NAME}, user={DB_USER}, password={DB_PASSWORD}, host={DB_HOST}, port={DB_PORT}")

        conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)
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


def create_embeddings_table(conn, cursor):
    try:
        cursor.execute(constants.CREATE_EMBEDDINGS_TABLE_QUERY)
        conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error creating 'embeddings' table: {exception}")


def create_user_table(conn, cursor):
    try:
        cursor.execute(constants.CREATE_USERS_TABLE_QUERY)
        conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error creating 'users' table: {exception}")


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


def add_embeddings_constraint(conn, cursor):
    try:
        cursor.execute(constants.ADD_EMBEDDINGS_CONSTRAINT)
        conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error adding unique embeddings constraint: {exception}")


def add_users_constraint(conn, cursor):
    try:
        cursor.execute(constants.ADD_USERS_CONSTRAINT)
        conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error adding unique users constraint: {exception}")


def embeddings_constraint_exists(conn, cursor):
    try:
        cursor.execute(constants.CHECK_CONSTRAINT_EMBEDDINGS_QUERY)
        conn.commit()
        return bool(cursor.fetchone())
    except psycopg2.Error as exception:
        raise DatabaseError(f"Error checking embeddings constraint existence: {exception}")


def users_constraint_exists(conn, cursor):
    try:
        cursor.execute(constants.CHECK_CONSTRAINT_USERS_QUERY)
        conn.commit()
        return bool(cursor.fetchone())
    except psycopg2.Error as exception:
        raise DatabaseError(f"Error checking users constraint existence: {exception}")


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
