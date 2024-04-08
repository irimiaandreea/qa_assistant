from fastapi import HTTPException, Depends, status, APIRouter, Request
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel

from components.exceptions.custom_exceptions import NoOpenAIKeyError, RequestError
from components.qa_system.database_operations import *
from components.qa_system.faq_search import compute_embeddings, process_user_query
from transformers import BertTokenizerFast, BertForSequenceClassification, pipeline
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()


class UserQuestion(BaseModel):
    user_question: str


class AnswerResponse(BaseModel):
    source: str
    matched_question: str
    answer: str


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


def check_if_openai_api_key_exists():
    if os.getenv("OPENAI_API_KEY"):
        return True
    else:
        return False


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

#TODO
# separate the logic , Middleware from enpdoints ?
async def classify_it_related_question(request: Request, user_question: UserQuestion):
    try:
        binary_classifier = load_model_and_tokenizer("/output_seq_model",
                                                     "/output_seq_tokenizer")
        is_it_related = perform_binary_text_classification(user_question.user_question, binary_classifier)

        request.state.is_it_related = is_it_related

    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))


# STEP 4 - Design FastAPI Endpoint to post user's question
@router.post("/ask-question")
async def ask_question(user_question: UserQuestion, request: Request, token: str = Depends(oauth2_scheme)):
    try:
        payload = jwt.decode(token, constants.JWT_SECRET_KEY, algorithms=[constants.JWT_ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

        if not check_if_openai_api_key_exists():  # TRUE
            raise NoOpenAIKeyError("No OpenAI API key found")

        conn = get_connection()

        compute_embeddings(conn, constants.FAQ_DATABASE)

        source, question, answer = process_user_query(conn, user_question.user_question, constants.SIMILARITY_THRESHOLD)
        # await classify_it_related_question(request, user_question)

        # is_it_related = request.state.is_it_related
        # TODO
        # save the model in hub, and process the logic regarding the is_it_related boolean, in db or smth
        # clean up the requirements.txt in order to build the docker image faster
        
        # logger.info(is_it_related)

        conn.close()

        return AnswerResponse(source=source, matched_question=question, answer=answer)

    except NoOpenAIKeyError as exception:
        raise HTTPException(status_code=500, detail=str(exception))
    except psycopg2.Error as exception:
        raise DatabaseError("Database error: " + str(exception))
    except RequestError as exception:
        raise HTTPException(status_code=500, detail=str(exception))
    except Exception as exception:
        raise HTTPException(status_code=500, detail=str(exception))
