import model.config.constants as constants
import json


def insert_into_embeddings(conn, cursor, current_question, current_answer, current_question_embedding,
                           current_answer_embedding):
    cursor.execute(constants.INSERT_INTO_EMBEDDINGS_TABLE_QUERY,
                   (current_question, json.dumps(current_question_embedding), current_answer,
                    json.dumps(current_answer_embedding)))
    conn.commit()


def create_embeddings_table(conn, cursor):
    cursor.execute(constants.CREATE_EMBEDDINGS_TABLE_QUERY)
    conn.commit()


def add_unique_constraint(conn, cursor):
    cursor.execute(constants.ADD_CONSTRAINT_QUERY)
    conn.commit()


def table_exists(conn, cursor):
    cursor.execute(constants.TABLE_EMBEDDINGS_EXISTS_QUERY)
    conn.commit()
    return cursor.fetchone()[0]


def constraint_exists(conn, cursor):
    cursor.execute(constants.ADD_CONSTRAINT_QUERY)
    conn.commit()
    return cursor.fetchone()[0]


def retrieve_embeddings_from_database(conn):
    with conn.cursor() as cursor:
        cursor.execute("SELECT question, question_embedding, answer  FROM embeddings")
        conn.commit()
        rows = cursor.fetchall()

        faq_questions = [row[0] for row in rows]  # Assuming the first column is questions
        faq_questions_embeddings = [row[1] for row in rows]  # Assuming the second column is questions_embedding
        faq_answers = [row[2] for row in rows]  # Assuming the second column is answers

    return faq_questions, faq_questions_embeddings, faq_answers
