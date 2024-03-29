# intelligent_qa_assistant challenge

### Remaining points to address regarding the project:
- handle the conflict when a **user already exists** in database
- encrypt and store the **access_token** and **refresh_token** in PostgreSQL database in order to retrieve and use them later
- create a model in models, called **Tokens**, to store the information from **tokens table** from database
- add unit tests and integration tests
- create a script which contains the CRUD operations for managing embeddings in the database
- fix and dockerize the app with Docker and optimize dependencies in requirements.txt file
- implement the logic for the question classification in AIRouterBranch using the BERT Transformer with BertForSequenceClassification task on top of it (in order to classify if a given question is IT-related or non-IT-related => binary classification)
- refactor and clean the code that haven't been refactored and structured properly

### Run the Docker image using the following commands:
- `docker-compose build`
- `docker-compose up`
- check if the container is up and running
- if the FastAPI application along with the PostgreSQL database are up, start making API calls to the endpoints
