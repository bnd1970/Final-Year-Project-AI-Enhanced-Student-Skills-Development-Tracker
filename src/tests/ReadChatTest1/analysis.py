import json
import re
import requests
from typing import Dict
from config import config

class ConversationAnalyzer:
    def __init__(self):
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.API_KEY}"
        }
        self.system_prompt = self._build_system_prompt()

    def _build_system_prompt(self) -> str:
        # 保持原有提示词构建逻辑不变
        return f"""{config.SYSTEM_PROMPT}
        Dimensions:
        {json.dumps(config.SCORE_CRITERIA, indent=4)}
        Return valid JSON with these keys:
        {{
            "feedback": "analysis...",
            "scores": {{...}},
            "version": "{config.SCHEMA_VERSION}"
        }}"""

    def analyze_conversation(self, content: str) -> Dict:
        try:
            payload = {
                "model": config.MODEL_NAME,
                "messages": [
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": content}
                ],
                "temperature": 0.5
            }

            response = requests.post(
                config.API_ENDPOINT,
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                return {"error": f"API Error: {response.status_code} - {response.text}"}

            response_data = response.json()
            if "choices" not in response_data:
                return {"error": "Invalid API response format"}

            return self._parse_response(response_data["choices"][0]["message"]["content"])
            
        except requests.exceptions.RequestException as e:
            return {"error": f"API Connection Error: {str(e)}"}
        except Exception as e:
            return {"error": str(e)}

    @staticmethod
    def _parse_response(response: str) -> Dict:
        # 保持原有解析逻辑不变
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
        return {"error": "Failed to parse response"}