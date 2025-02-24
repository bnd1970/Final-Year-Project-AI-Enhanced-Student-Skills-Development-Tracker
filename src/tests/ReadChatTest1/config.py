from pathlib import Path

class Config:
    API_ENDPOINT = "https://api.deepseek.com/v1/chat/completions"
    API_KEY = "sk-58d92e234db44ad5904ac10a9a4374e9"
    MODEL_NAME = "deepseek-chat"
    DATA_DIR = Path("user_progress")
    SCHEMA_VERSION = "1.1"
    SCORE_CRITERIA = {
        "grammar": "Grammar Accuracy",
        "coherence": "Logical Coherence",
        "vocabulary": "Vocabulary Appropriateness",
        "structure": "Writing Structure",
        "overall": "Overall Performance"
    }
    SYSTEM_PROMPT = """Professional academic writing assistant..."""  # 保持原有提示词不变

config = Config()