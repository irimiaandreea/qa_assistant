from dotenv import load_dotenv

import model.config.constants as constants
import json
import psycopg2
import os
from model.exceptions.custom_exceptions import DatabaseError

load_dotenv(dotenv_path="model/config/.env")

# PostgreSQL
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")


def get_connection():
    try:
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
        raise DatabaseError(f"Error adding unique embeddings constraint: {exception}")


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
            cursor.execute("SELECT question, question_embedding, answer  FROM embeddings")
            conn.commit()
            rows = cursor.fetchall()

            faq_questions = [row[0] for row in rows]  # Assuming the first column is questions
            faq_questions_embeddings = [row[1] for row in rows]  # Assuming the second column is questions_embedding
            faq_answers = [row[2] for row in rows]  # Assuming the second column is answers

        return faq_questions, faq_questions_embeddings, faq_answers

    except psycopg2.Error as exception:
        raise DatabaseError(f"Error retrieving embeddings from database: {exception}")
