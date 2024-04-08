from transformers import BertTokenizerFast, BertForSequenceClassification, pipeline


def load_model_and_tokenizer(model_dir):
    tokenizer = BertTokenizerFast.from_pretrained(model_dir)
    bert = BertForSequenceClassification.from_pretrained(model_dir)
    binary_classifier = pipeline("text-classification", model=bert, tokenizer=tokenizer)
    return binary_classifier


def perform_binary_text_classification(input_file, output_file, binary_classifier):
    label_mapping = {"LABEL_0": 0, "LABEL_1": 1}

    with open(input_file, "r") as input_file:
        next(input_file)

        with open(output_file, "w") as output_file:
            for line in input_file:
                binary_classifier_results = binary_classifier(line.strip())

                for binary_classifier_result in binary_classifier_results:
                    output_file.write(f"Question: {line}")
                    output_file.write(f"Predicted label: {label_mapping[binary_classifier_result['label']]}\n")
                    output_file.write(f"Confidence: {binary_classifier_result['score']}\n\n")


if __name__ == "__main__":
    seq_trained_model_dir = "output_seq_model"

    input_file = "../datasets/inference_questions.csv"
    output_file = "../datasets/predictions.txt"

    binary_classifier = load_model_and_tokenizer(seq_trained_model_dir)
    perform_binary_text_classification(input_file, output_file, binary_classifier)
