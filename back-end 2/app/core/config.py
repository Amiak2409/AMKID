from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    Общая конфигурация проекта.
    Сейчас не используется в существующем коде,
    но готова для дальнейшего расширения.
    """

    # OpenAI
    openai_api_key: str | None = None

    # БД
    db_user: str | None = None
    db_password: str | None = None
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str | None = None

    # R2 / S3
    r2_endpoint_url: str | None = None
    r2_access_key_id: str | None = None
    r2_secret_application_key: str | None = None
    r2_bucket_name: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()
