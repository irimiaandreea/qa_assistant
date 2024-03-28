CONTENT_TYPE = "application/json"
EMBEDDING_MODEL = "text-embedding-3-small"
OPENAI_GET_ANSWER_MODEL = "gpt-4-turbo-preview"
OPENAI_API_URL_EMBEDDINGS = "https://api.openai.com/v1/embeddings"
OPENAI_API_URL_COMPLETIONS = "https://api.openai.com/v1/chat/completions"
CREATE_EMBEDDINGS_TABLE_QUERY = "CREATE TABLE IF NOT EXISTS embeddings (" \
                                "id SERIAL PRIMARY KEY," \
                                "question TEXT," \
                                "question_embedding JSONB," \
                                "answer TEXT," \
                                "answer_embedding JSONB)"
CREATE_USERS_TABLE_QUERY = "CREATE TABLE IF NOT EXISTS users (" \
                           " id SERIAL PRIMARY KEY," \
                           " username VARCHAR(100)," \
                           " password VARCHAR(100))"
ADD_EMBEDDINGS_CONSTRAINT = "ALTER TABLE embeddings " \
                            "ADD CONSTRAINT question_unique_constraint UNIQUE (question)"
ADD_USERS_CONSTRAINT = "ALTER TABLE users " \
                       "ADD CONSTRAINT username_unique_constraint UNIQUE (username)"
INSERT_INTO_EMBEDDINGS_TABLE_QUERY = "INSERT INTO embeddings (question, question_embedding, answer, answer_embedding) " \
                                     "VALUES (%s, %s, %s, %s)" \
                                     "ON CONFLICT (question) DO UPDATE " \
                                     "SET question_embedding = EXCLUDED.question_embedding," \
                                     "answer = EXCLUDED.answer," \
                                     "answer_embedding = EXCLUDED.answer_embedding"
TABLE_EMBEDDINGS_EXISTS_QUERY = " SELECT EXISTS ( SELECT 1 FROM information_schema.tables WHERE table_name = 'embeddings') "
CHECK_CONSTRAINT_EMBEDDINGS_QUERY = " SELECT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage WHERE constraint_name = 'embeddings_unique_constraint')"
CHECK_CONSTRAINT_USERS_QUERY = " SELECT EXISTS (SELECT 1 FROM information_schema.constraint_column_usage WHERE constraint_name = 'username_unique_constraint')"
SIMILARITY_THRESHOLD = 0.8
FAQ_DATABASE = [
    {
        "question": "How do I change my profile information?",
        "answer": "Navigate to your profile page, click on 'Edit Profile', and make the desired changes."
    },
    {
        "question": "What steps do I take to reset my password?",
        "answer": "Go to account settings, select 'Change Password', enter your current password and then the new one. Confirm the new password and save the changes."
    },
    {
        "question": "How can I restore my account to its default settings?",
        "answer": "In the account settings, there should be an option labeled 'Restore Default'. Clicking this will revert all custom settings back to their original state."
    },
    {
        "question": "Is it possible to change my registered email address?",
        "answer": "Yes, navigate to account settings, find the 'Change Email' option, enter your new email, and follow the verification process."
    },
    {
        "question": "How can I retrieve lost data from my account?",
        "answer": "Contact our support team with details of the lost data. They'll guide you through the recovery process."
    },
    {
        "question": "Are there any guidelines on setting a strong password?",
        "answer": "Absolutely! Use a combination of uppercase and lowercase letters, numbers, and special characters. Avoid using easily guessable information like birthdays or names."
    },
    {
        "question": "Can I set up two-factor authentication for my account?",
        "answer": "Yes, in the security section of account settings, there's an option for two-factor authentication. Follow the setup instructions provided there."
    },
    {
        "question": "How do I deactivate my account?",
        "answer": "Under account settings, there's a 'Deactivate Account' option. Remember, this action is irreversible."
    },
    {
        "question": "What do I do if my account has been compromised?",
        "answer": "Immediately reset your password and contact our security team for further guidance."
    },
    {
        "question": "Can I customize the notifications I receive?",
        "answer": "Yes, head to the notifications settings in your account and choose which ones you'd like to receive."
    }
]
