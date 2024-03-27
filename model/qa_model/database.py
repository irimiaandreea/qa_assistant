import model.config.constants as constants

def insert_into_embeddings(conn, cursor, current_question, current_answer, current_question_embedding,
                           current_answer_embedding):
    cursor.execute(constants.INSERT_INTO_EMBEDDINGS_TABLE,
                   (current_question, current_question_embedding, current_answer, current_answer_embedding))
    conn.commit()


def create_embeddings_table(conn, cursor):
    cursor.execute(constants.CREATE_EMBEDDINGS_TABLE_QUERY)
    conn.commit()