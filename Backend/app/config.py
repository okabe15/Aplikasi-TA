from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    openrouter_api_key: str
    comfyui_url: str = "http://127.0.0.1:8188"
    ai_model: str = "deepseek/deepseek-r1-distill-llama-70b:free"
    
    # ========== Authentication Settings (NEW) ==========
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    # ===================================================
    
    class Config:
        env_file = ".env"

settings = Settings()