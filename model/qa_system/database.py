import model.config.constants as constants
import json
import psycopg2
from model.exceptions.custom_exceptions import DatabaseError


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


def add_unique_constraint(conn, cursor):
    try:
        cursor.execute(constants.ADD_CONSTRAINT_QUERY)
        conn.commit()
    except psycopg2.Error as exception:
        conn.rollback()
        raise DatabaseError(f"Error adding unique constraint: {exception}")


def table_exists(conn, cursor):
    try:
        cursor.execute(constants.TABLE_EMBEDDINGS_EXISTS_QUERY)
        conn.commit()
        return bool(cursor.fetchone())
    except psycopg2.Error as exception:
        raise DatabaseError(f"Error checking table existence: {exception}")


def constraint_exists(conn, cursor):
    try:
        cursor.execute(constants.ADD_CONSTRAINT_QUERY)
        conn.commit()
        return bool(cursor.fetchone())
    except psycopg2.Error as exception:
        raise DatabaseError(f"Error checking constraint existence: {exception}")


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
