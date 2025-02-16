#Score according to the quality of the conversation
import json
import re
import os
from datetime import datetime
from pathlib import Path
from ollama import chat

# Configuration
MODEL_NAME = "deepseek-r1:14b"
DATA_DIR = Path("user_progress")
SCHEMA_VERSION = "1.1"

SCORE_CRITERIA = {
    "grammar": "Grammar Accuracy",
    "coherence": "Logical Coherence", 
    "vocabulary": "Vocabulary Appropriateness",
    "structure": "Writing Structure",
    "overall": "Overall Performance"
}

SYSTEM_PROMPT = f"""You are a professional academic writing assistant. Analyze user input and provide:

1. Detailed feedback with improvement suggestions
2. Skill scores (0-5) in these dimensions:
{json.dumps(SCORE_CRITERIA, indent=4)}

Return valid JSON format:
{{
    "feedback": "detailed analysis...",
    "scores": {{
        "grammar": 0-5,
        "coherence": 0-5,
        "vocabulary": 0-5,
        "structure": 0-5,
        "overall": 0-5
    }},
    "version": "{SCHEMA_VERSION}"
}}

Ensure:
- Scores reflect actual skill level
- Avoid score inflation
- Maintain strict JSON syntax
- No additional text outside JSON
"""

def init_environment():
    """Initialize data directory for Windows"""
    try:
        DATA_DIR.mkdir(exist_ok=True)
    except PermissionError:
        print(f"Error: Cannot create directory {DATA_DIR}. Check permissions.")
        exit(1)

def parse_llm_response(response: str) -> dict:
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

def save_progress(user_input: str, analysis: dict):
    if "scores" not in analysis:
        return

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"session_{timestamp}.json"

    record = {
        "timestamp": datetime.now().isoformat(),
        "input": user_input,
        "feedback": analysis.get("feedback", ""),
        "scores": analysis["scores"],
        "schema_version": SCHEMA_VERSION
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Save failed: {str(e)}")

def analyze_content(user_input: str) -> dict:
    try:
        response = chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            options={"temperature": 0.5}
        )
        return parse_llm_response(response['message']['content'])
    except Exception as e:
        return {"error": str(e)}

def display_results(analysis: dict):
    if "error" in analysis:
        print(f"Error: {analysis['error']}")
        return

    print("\n--- Analysis Report ---")
    print(analysis.get('feedback', 'No feedback available'))
    
    if "scores" in analysis:
        print("\nSkill Assessment:")
        for criterion, score in analysis["scores"].items():
            print(f"- {SCORE_CRITERIA.get(criterion, criterion)}: {score}/5")

def main():
    init_environment()
    print("Academic Writing Assistant\nType 'exit' to quit")
    
    while True:
        try:
            user_input = input("\nYour Text: ").strip()
            if user_input.lower() == 'exit':
                break
            if not user_input:
                print("Please enter valid text")
                continue

            print("Analyzing...")
            analysis = analyze_content(user_input)
            display_results(analysis)
            
            if "scores" in analysis:
                save_progress(user_input, analysis)

        except KeyboardInterrupt:
            print("\nOperation cancelled")
            break
        except Exception as e:
            print(f"Unexpected error: {str(e)}")

if __name__ == "__main__":
    main()