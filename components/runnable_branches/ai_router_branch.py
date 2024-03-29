from langchain import RunnableBranch


class AIRouterBranch(RunnableBranch):
    def run(self, conn, user_question, similarity_threshold):
        is_it_related = is_it_related_question(user_question)

        if is_it_related:
            response = "This question is IT-related. Routing to IT support."
        else:
            response = "This is not really what I was trained for, therefore I cannot answer. Try again."


def is_it_related_question(user_question):
    # TODO Implement the logic for classify a question
    # TODO Use BERT Transformer with BertForSequenceClassification task on top of it,
    #  since represents an excellent solution for binary or multi-class problems.
    #  input: question
    #  output: IT-related or NON-IT-related (2 classes -> binary classification)

    return None
