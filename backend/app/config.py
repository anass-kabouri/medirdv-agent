from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    anthropic_api_key: str
    database_url: str
    app_env: str = "development"
    claude_model: str = "claude-sonnet-5"
    smtp_host: str = "smtp.gmail.com"
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    smtp_from: str = ""
    jwt_secret_key: str = "changez-moi-en-production-svp"
    clinic_name: str = "MediRDV"
    clinic_logo_path: str = ""

    class Config:
        env_file = ".env"


settings = Settings()