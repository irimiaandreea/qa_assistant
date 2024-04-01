from fastapi import HTTPException, Depends, status, APIRouter
from fastapi.security import OAuth2PasswordBearer
from jose import jwt
from pydantic import BaseModel

from components.exceptions.custom_exceptions import NoOpenAIKeyError, RequestError
from components.qa_system.database_operations import *
from components.qa_system.faq_search import compute_embeddings, process_user_query

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


# STEP 4 - Design FastAPI Endpoint to post user's question
@router.post("/ask-question")
async def ask_question(user_question: UserQuestion, token: str = Depends(oauth2_scheme)):
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
