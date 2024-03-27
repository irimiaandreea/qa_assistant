class CustomError(Exception):
    """Base class for custom exceptions."""

    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class RequestError(CustomError):
    """Custom exception for errors related to HTTP requests."""


class OpenAIError(CustomError):
    """Custom exception for errors specific to the OpenAI API."""


class EmbeddingError(CustomError):
    """Custom exception for errors related to computing embeddings."""


class DatabaseError(CustomError):
    """Custom exception for errors related to inserting data into the database."""


class NoOpenAIKeyError(CustomError):
    """Exception raised when no API key for OpenAI is found."""
