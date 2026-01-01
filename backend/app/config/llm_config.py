from app.config.settings import settings


class LLMConfig:
    """OpenAI API configuration"""
    
    # OpenAI Configuration
    OPENAI_MODEL = "gpt-4o-mini"  # Updated to current model
    OPENAI_TEMPERATURE = 0.7
    OPENAI_MAX_TOKENS = 500
    
    @staticmethod
    def get_api_key():
        """Get OpenAI API key"""
        return settings.OPENAI_API_KEY


llm_config = LLMConfig()
