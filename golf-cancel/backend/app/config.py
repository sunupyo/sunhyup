from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    KAKAO_REST_API_KEY: str = ""
    KAKAO_CLIENT_SECRET: str = ""
    KAKAO_REDIRECT_URI: str = "http://localhost:8000/api/kakao/callback"

    DATABASE_URL: str = "sqlite:///./golf.db"
    POLL_INTERVAL_SECONDS: int = 60
    FRONTEND_BASE_URL: str = "http://localhost:5173"
    ENABLE_DEMO_CRAWLER: bool = True

    # XGOLF 인증 (브라우저 DevTools → Network → 잔여조회 요청 → cURL Cookie 헤더 그대로)
    XGOLF_COOKIE: str = ""
    XGOLF_AGENT_CODE: str = "77"
    XGOLF_LOOKAHEAD_DAYS: int = 21


settings = Settings()
