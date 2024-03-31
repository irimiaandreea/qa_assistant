# intelligent_qa_assistant

### Build the Docker images from the docker-compose.yaml file:
- `docker-compose build`
- `docker-compose up`
- `docker-compose ps` to check if the containers (fastapi_container and postgres_container) are up and running (Status = 'Up')
- start making API calls to the available endpoints, but take into consideration that the **QAuth2.0 mechanism** is implemented on `/ask-question` endpoint, and a **'token'** parameter is expected for authentication

### Endpoints

#### Register a new user
 - Endpoint: `/register` 
 - Method: POST
 - Body Parameters: `username`, `password`
 - Description: Register a new user by providing a username (unique) and password.
 - Request:
  ```
  POST /register
  Content-Type: application/json
  
  {
      "username": "test_user",
      "password": "test_pass"
  }
```
 - Response:
  ```
  {
      "message": "User registered successfully"
  }
```

#### Obtain an access token for authentication

 - Endpoint: `/token`
 - Method: POST 
 - Body Parameters: `username`, `password`
 - Description: Obtain an access token for QAuth2.0 by providing the registered username and password. The access token expires after 30 minutes, while the refresh token expires after 30 days.
 - Request: 
  ```
  POST /token
    Content-Type: application/x-www-form-urlencoded
    
    {
        "username": "test_user",
        "password": "test_pass"
    }
```
 - Response:
  ```
    {
        "access_token": "a12w3s4s",
        "token_type": "bearer",
        "refresh_token": "6f7t8r9e"
    }
```

#### Use the obtained access token to ask any question 

 - Endpoint: `/ask-question`
 - Method: POST 
 - Header: `Authorization: Bearer <access_token>`
 - Body Parameters: `user_question`
 - Description: A user can ask a question and get an answer either from the local FAQ database or from OpenAI.
 - Request: 
  ```
   POST /ask-question
    Content-Type: application/json
    Authorization: Bearer <valid_access_token>
    
    {
        "user_question": "What is the capital of Romania?"
    }
```
 - Response: 
  ```
    {
        "source": "openai",
        "matched_question": "N/A",
        "answer": "The capital of Romania is Bucharest."
    }
```

 - Request: 
  ```
   POST /ask-question
    Content-Type: application/json
    Authorization: Bearer <valid_access_token>
    
    {
        "user_question": "Can I set up two-factor authentication for my account?"
    }
```
 - Response: 
  ```
    {
        "source": "local",
        "matched_question": "Can I set up two-factor authentication for my account?",
        "answer": "Yes, in the security section of account settings, there's an option for two-factor authentication. Follow the setup instructions provided there."
    }
```

#### Obtain another access token

 - Endpoint: `/refresh-token`
 - Method: POST 
 - Body Parameters: `refresh_token`
 - Description: If the current access token expires (after 30 min) then generate another valid access token by providing the refresh token obtained during authentication.
 - Request: 
  ```
  POST /refresh-token
    Content-Type: application/json
    
    {
        "refresh_token": "6f7t8r9e",
    }
```
 - Response: 
  ```
   {
      "access_token": "0i9p8u7l",
      "token_type": "bearer"
   }
```

### Remaining points to address regarding the project:
- handle the conflict when a **user already exists** in database
- encrypt and store the **access_token** and **refresh_token** in PostgreSQL database in order to retrieve and use them later
- create a model in models, called **Tokens**, to store the information from **tokens table** from database
- add unit tests and integration tests
- create a script which contains the CRUD operations for managing embeddings in the database
- fix and dockerize the app with Docker and optimize dependencies in requirements.txt file
- implement the logic for the question classification in AIRouterBranch using the BERT Transformer with BertForSequenceClassification task on top of it (in order to classify if a given question is IT-related or non-IT-related => binary classification)
- refactor and clean the code that haven't been refactored and structured properly
