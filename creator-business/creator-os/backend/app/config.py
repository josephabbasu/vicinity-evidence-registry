import os


class Settings:
    """Environment-driven configuration. Sensible defaults for local dev."""

    def __init__(self) -> None:
        self.database_url: str = os.environ.get("DATABASE_URL", "sqlite:///./creatoros.db")
        self.secret_key: str = os.environ.get("SECRET_KEY", "dev-only-change-me-to-a-32+byte-random-secret")
        self.access_token_minutes: int = int(os.environ.get("ACCESS_TOKEN_MINUTES", "1440"))
        self.anthropic_api_key: str = os.environ.get("ANTHROPIC_API_KEY", "")
        self.anthropic_model: str = os.environ.get("ANTHROPIC_MODEL", "claude-opus-4-8")
        self.cors_origins: list[str] = [
            o.strip()
            for o in os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
            if o.strip()
        ]
        self.seed_demo_data: bool = os.environ.get("SEED_DEMO_DATA", "1") == "1"


settings = Settings()
