class Embedding:
    def __init__(self, id: int, question: str, question_embedding: str, answer: str):
        self.id = id
        self.question = question
        self.question_embedding = question_embedding
        self.answer = answer
