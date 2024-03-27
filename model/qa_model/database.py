import model.config.constants as constants
import json

def insert_into_embeddings(conn, cursor, current_question, current_answer, current_question_embedding,
                           current_answer_embedding):
    cursor.execute(constants.INSERT_INTO_EMBEDDINGS_TABLE_QUERY,
                   (current_question, json.dumps(current_question_embedding), current_answer, json.dumps(current_answer_embedding)))
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

