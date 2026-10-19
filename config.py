from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict
)


# ============================================================
# APPLICATION SETTINGS
# ============================================================

class Settings(BaseSettings):

    # --------------------------------------------------------
    # MongoDB
    # --------------------------------------------------------

    mongodb_url: str = (
        "mongodb://127.0.0.1:27017"
    )

    database_name: str = (
        "fake_news_detection"
    )

    # --------------------------------------------------------
    # Frontend
    # --------------------------------------------------------

    frontend_url: str = (
        "http://localhost:5173"
    )

    # --------------------------------------------------------
    # JWT Authentication
    # --------------------------------------------------------

    jwt_secret_key: str = (
        "change-this-secret-key"
    )

    model_config = SettingsConfigDict(

        env_file=".env",

        env_file_encoding="utf-8",

        extra="ignore"

    )


# ============================================================
# SETTINGS INSTANCE
# ============================================================

settings = Settings()