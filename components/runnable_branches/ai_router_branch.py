from langchain import RunnableBranch
from transformers import BertTokenizerFast, BertForSequenceClassification, pipeline

#TODO
# DELETE THIS ENTIRE FILE
class AIRouterBranch(RunnableBranch):
    def run(self, conn, user_question, similarity_threshold):

        is_it_related = perform_binary_text_classification(user_question, load_model_and_tokenizer(
            "../transformers/bert/output_seq_model", "../transformers/bert/output_seq_tokenizer"))

        if is_it_related:
            response = "This question is IT-related. Routing to IT support."
        else:
            response = "This is not really what I was trained for, therefore I cannot answer. Try again."

        return response


def load_model_and_tokenizer(model_dir, tokenizer_dir):
    tokenizer = BertTokenizerFast.from_pretrained(tokenizer_dir)
    bert = BertForSequenceClassification.from_pretrained(model_dir)
    binary_classifier = pipeline("text-classification", model=bert, tokenizer=tokenizer)
    return binary_classifier


def perform_binary_text_classification(user_question, binary_classifier):
    label_mapping = {"LABEL_0": 0, "LABEL_1": 1}

    binary_classifier_result = binary_classifier(user_question.strip())

    is_it_related = label_mapping[binary_classifier_result[0]["label"]] == 1

    return is_it_related
