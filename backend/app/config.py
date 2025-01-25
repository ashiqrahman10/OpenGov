from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GROQ_API_KEY: str
    FIREBASE_STORAGE_BUCKET: str
    FIREBASE_CREDENTIALS_PATH: str

    class Config:
        env_file = ".env"

settings = Settings()