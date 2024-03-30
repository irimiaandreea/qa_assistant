CREATE TABLE users
(
    id       SERIAL PRIMARY KEY,
    username VARCHAR(100) NOT NULL,
    password VARCHAR(100) NOT NULL
);

CREATE TABLE embeddings
(
    id                 SERIAL PRIMARY KEY,
    question           TEXT,
    question_embedding JSONB,
    answer             TEXT,
    answer_embedding   JSONB
);

CREATE TABLE tokens
(
    id            SERIAL PRIMARY KEY,
    user_id       INTEGER REFERENCES users (id) ON DELETE CASCADE,
    access_token  TEXT NOT NULL,
    refresh_token TEXT NOT NULL,
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

ALTER TABLE users
    ADD CONSTRAINT username_unique_constraint UNIQUE (username);

ALTER TABLE embeddings
    ADD CONSTRAINT question_unique_constraint UNIQUE (question);