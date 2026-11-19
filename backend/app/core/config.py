from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str
    supabase_url: str
    supabase_anon_key: str
    supabase_jwt_secret: str
    frontend_origin: str = "http://localhost:5173"
    environment: str = "development"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
