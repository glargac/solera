from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "sqlite+aiosqlite:///./solora.db"
    supabase_url: str = ""
    supabase_service_key: str = ""
    supabase_storage_bucket: str = "cleaning-photos"
    cors_origins: str = "http://localhost:5173"
    ical_sync_minutes: int = 30
    anthropic_api_key: str = ""


settings = Settings()
