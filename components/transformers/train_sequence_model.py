import os
import shutil

import pandas as pd
import torch
import torch.nn.functional as F
from datasets import Dataset
from sklearn.metrics import precision_score, recall_score, f1_score
from transformers import BertForSequenceClassification, BertTokenizerFast, TrainingArguments, Trainer
import mlflow
from mlflow.tracking import MlflowClient


# TODO
# remove print() statements
class CustomDataCollator:
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer

    def __call__(self, features):
        input_ids = [torch.tensor(item["input_ids"]) for item in features]
        attention_mask = [torch.tensor(item["attention_mask"]) for item in features]
        labels = [torch.tensor(item["labels"]) for item in features]
        token_type_ids = [torch.tensor(item["token_type_ids"]) for item in features]

        input_ids = torch.nn.utils.rnn.pad_sequence(input_ids, batch_first=True,
                                                    padding_value=self.tokenizer.pad_token_id)
        attention_mask = torch.nn.utils.rnn.pad_sequence(attention_mask, batch_first=True, padding_value=0)
        labels = torch.nn.utils.rnn.pad_sequence(labels, batch_first=True, padding_value=-100)
        token_type_ids = torch.nn.utils.rnn.pad_sequence(token_type_ids, batch_first=True,
                                                         padding_value=self.tokenizer.pad_token_type_id)
        return {
            "input_ids": input_ids,
            "attention_mask": attention_mask,
            "labels": labels,
            "token_type_ids": token_type_ids
        }


def clean_up_directories(*directories):
    for directory in directories:
        if os.path.exists(directory):
            shutil.rmtree(directory)
        os.makedirs(directory)


def tokenize_input(example):
    inputs = tokenizer(example['Question'], truncation=True, padding='max_length', max_length=128)
    inputs['labels'] = [[label] for label in example['IT_related']]

    return inputs


def process_data(input_dataset):
    dataframe_obj = pd.read_csv(input_dataset)

    input_hf_dataset = Dataset.from_pandas(dataframe_obj)
    tokenizer = BertTokenizerFast.from_pretrained("bert-base-uncased")
    num_unique_classes = len(input_hf_dataset.unique("IT_related"))

    return input_hf_dataset, tokenizer, num_unique_classes


def train_and_evaluate_model():
    mlflow.set_experiment("binary_classification_experiment")
    with mlflow.start_run():
        bert = BertForSequenceClassification.from_pretrained("bert-base-uncased",
                                                             num_labels=num_classes)

        training_args = TrainingArguments(  # hyperparameters
            output_dir=seq_trained_model_dir,
            evaluation_strategy="epoch",
            logging_dir=None,
            report_to=["none"],
            num_train_epochs=5,
            per_device_train_batch_size=8,
            per_device_eval_batch_size=8,
            learning_rate=5e-5,
            save_strategy="epoch",
            warmup_ratio=0.1,
        )

        def compute_metrics(eval_pred):
            predictions, actual_classes = eval_pred.predictions, eval_pred.label_ids
            predictions = torch.tensor(predictions)
            probabilities = F.softmax(predictions, dim=1)
            actual_classes = torch.tensor(actual_classes).squeeze()

            positive_class_probs = probabilities[:, 1]

            loss = F.binary_cross_entropy(positive_class_probs, actual_classes.float())

            predicted_classes = (positive_class_probs > 0.5).float()  # Convert probabilities to binary predictions

            accuracy = (predicted_classes == actual_classes).float().mean().item()
            precision = precision_score(actual_classes, predicted_classes)
            recall = recall_score(actual_classes, predicted_classes)
            f1 = f1_score(actual_classes, predicted_classes)
            binary_cross_entropy_loss = loss.item()

            mlflow.log_metric("accuracy", accuracy)
            mlflow.log_metric("precision", precision)
            mlflow.log_metric("recall", recall)
            mlflow.log_metric("f1", f1)
            mlflow.log_metric("binary_cross_entropy_loss", binary_cross_entropy_loss)

            return {
                "accuracy": accuracy,
                "precision": precision,
                "recall": recall,
                "f1_score": f1,
                "binary_cross_entropy_loss": binary_cross_entropy_loss
            }

        trainer = Trainer(
            model=bert,
            args=training_args,
            train_dataset=train_dataset,
            eval_dataset=eval_dataset,
            tokenizer=tokenizer,
            data_collator=data_collator,
            compute_metrics=compute_metrics,
        )

        trainer.train()
        testing_results = trainer.evaluate(test_dataset)

        trainer.save_model(seq_trained_model_dir)
        tokenizer.save_pretrained(seq_trained_tokenizer_dir)


if __name__ == "__main__":
    seq_trained_model_dir = "output_seq_model"
    seq_trained_tokenizer_dir = "output_seq_tokenizer"
    input_dataset = "input_dataset_100_questions.csv"

    clean_up_directories(seq_trained_model_dir, seq_trained_tokenizer_dir)

    input_hf_dataset, tokenizer, num_classes = process_data(input_dataset)
    tokenized_dataset = input_hf_dataset.map(tokenize_input, batched=True)

    # the tokenized_dataset will be split into 80% train, 20% (10% test + 10% validation) datasets
    train_test_dataset_dict = tokenized_dataset.train_test_split(train_size=0.8, test_size=0.2)
    test_eval_dataset_dict = train_test_dataset_dict['test'].train_test_split(train_size=0.5, test_size=0.5)

    train_dataset = train_test_dataset_dict['train']
    test_dataset = test_eval_dataset_dict['test']
    eval_dataset = test_eval_dataset_dict['train']

    data_collator = CustomDataCollator(tokenizer=tokenizer)

    train_and_evaluate_model()
