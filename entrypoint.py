from fastapi import FastAPI
from components.api.auth_endpoints import router as auth_router
from components.api.question_endpoints import router as question_router

app = FastAPI()

app.include_router(auth_router, prefix="/auth")
app.include_router(question_router, prefix="/questions")
