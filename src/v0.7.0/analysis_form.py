#Score according to the quality of the conversation
import pandas as pd
import json
import re
import os
import argparse
from datetime import datetime
from pathlib import Path
from ollama import chat
from auth import get_connection
import traceback
LOG_DIR = Path("chat_logs")

# Configuration
MODEL_NAME = "deepseek-r1:8b"
DATA_DIR = Path("user_progress")
SCHEMA_VERSION = "0.7.0"
INPUT_FILE = "output_form/cleaned_chat.xlsx"

COLLAB_CRITERIA = {
    "participation": "Discussion participation frequency",
    "initiative": "Unsolicited contribution proposal",
    "problem_solving": "Problem solving ability",
    "coordination": "Team coordination ability", 
    "responsiveness": "Response timeliness"
}

SYSTEM_PROMPT = f"""As a team collaboration analyst, evaluate the chat history based on the following dimensions:

1. Detailed feedback with improvement suggestions
2. Skill scores (0-5) in these dimensions:
{json.dumps(COLLAB_CRITERIA, indent=4, ensure_ascii=False)}

Scoring rules:
1. Analyze message content, not quantity
2. Focus on constructive contributions
3. Pay attention to coordinating organizational behavior
4. Evaluate the effectiveness of problem solving

Return valid JSON format:
{{
    "feedback": "detail analysis...",
    "scores": {{
        "participation": 0-5,
        "initiative": 0-5,
        "problem_solving": 0-5,
        "coordination": 0-5,
        "responsiveness": 0-5
    }},
    "mentions": ["userA", "userB"], 
    "version": "{SCHEMA_VERSION}"
}}
Rules:
1. Output only JSON. No markdown, explanations, or extra text.
2. Use numeric scores (0-5) only.
3. Do not include any comments or additional formatting.
"""

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Team collaboration analysis tool')
    parser.add_argument('--input', 
                        default='output_form/cleaned_chat.xlsx',
                        help='Input file path (default: output_form/cleaned_chat.xlsx)')
    return parser.parse_args()

def init_environment():
    """Initialize environment"""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f"{INPUT_FILE} does not exist")
    except Exception as e:
        print(f"Initialization error: {str(e)}")
        exit(1)

def load_chat_data():
    """加载和预处理聊天数据（修复数据结构问题）"""
    df = pd.read_excel(INPUT_FILE, sheet_name="Sheet1")
    df = df[df['type_name'] == '文本']   # 只分析文本消息
    
    # 确保转换为字典列表
    return df.groupby('talker').apply(
        lambda x: x[['CreateTime', 'msg']].to_dict('records')
    ).to_dict()

def log_chat_interaction(talker: str, 
                        request: dict, 
                        response: str, 
                        attempt: int = 0,
                        error: str = ""):
    """记录完整的AI对话交互日志"""
    try:
        LOG_DIR.mkdir(exist_ok=True)
        
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "talker": talker,
            "model": MODEL_NAME,
            "attempt": attempt,
            "request": request,
            "response": response,
            "error": error
        }
        
        filename = LOG_DIR / f"{talker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(log_data, f, 
                     ensure_ascii=False, 
                     indent=2)
            
    except Exception as e:
        print(f"日志记录失败: {str(e)}")
        traceback.print_exc()

def parse_llm_response(response: str) -> dict:
    try:
        response = response.encode('utf-8', 'ignore').decode('utf-8')

        # Extract the JSON part
        json_str = re.search(r'\{[\s\S]*\}', response)
        if not json_str:
            return {
                "error": "No valid JSON found in response",
                "raw_response": response[:500]
            }
        json_str = json_str.group(0)

        # Fix common format issues
        json_str = (
            json_str
            .replace("'", '"')
            .replace("：", ":")
            .replace("，", ",")
            .replace("‘", "'")
            .replace("’", "'")
            .replace("“", "\"")
            .replace("”", "\"")
        )
        
        parsed = json.loads(json_str, strict=False)
        
        # Merge the default value with the actual return value
        required_scores = {
            "participation": 0,
            "initiative": 0,
            "problem_solving": 0,
            "coordination": 0,
            "responsiveness": 0
        }
        
        merged_scores = {k: float(parsed.get("scores", {}).get(k, 0)) for k in required_scores}
        for k, v in parsed.get("scores", {}).items():
            merged_scores[k] = min(5, max(0, float(v)))

        result = {
            "feedback": parsed.get("feedback", "No feedback content"),
            "scores": {**required_scores, **parsed.get("scores", {})},
            "mentions": parsed.get("mentions", []),
            "version": parsed.get("version", SCHEMA_VERSION)
        }
        return result
        
    except Exception as e:
        print(f"Parsing error:{str(e)}")
        return {"error": str(e)}
    
def analyze_collaboration(messages: list) -> dict:
    context_lines = []
    for i, rec in enumerate(messages):
        ts = rec.get("CreateTime")
        text = rec.get("msg", "").replace("\n", " ")
        context_lines.append(f"Article{i+1}, time：{ts}， Content: “{text}”")
    context = "\n".join(context_lines)

    max_retries = 5
    valid_result = None
    
    for attempt in range(max_retries):
        try:
            # Parameter passing
            response = chat(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                options={"temperature": min(0.3 + attempt*0.15, 0.7)} 
            )
            
            # Add type checking
            if isinstance(messages, list) and len(messages) > 0:
                talker = messages[0].get('talker', 'unknown') if isinstance(messages[0], dict) else 'unknown'
            else:
                talker = 'unknown'
            
            # Keep a log
            log_chat_interaction(
                talker=talker,
                request={
                    "model": MODEL_NAME,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": context}
                    ],
                    "options": {"temperature": min(0.3 + attempt*0.15, 0.7)}
                },
                response=response['message']['content'],
                attempt=attempt+1
            )
            
            result = parse_llm_response(response['message']['content'])
            
            if is_valid_analysis(result):
                valid_result = result
                break
                
            print(f"The {attempt+1} retry: Obtained an invalid result")
            
        except Exception as e:
            error_msg = f"{type(e).__name__}: {str(e)}"
            print(f"An anomaly occurred during the analysis:{error_msg}")
            result = {"error": error_msg}
    
    return valid_result or result

def is_valid_analysis(analysis: dict) -> bool:
    """Verify the validity of the analysis results"""
    if 'error' in analysis:
        return False
    scores = analysis.get('scores', {})
    # Check for non-zero scores and valid feedback
    has_non_zero = any(v > 0 for v in scores.values())
    has_feedback = bool(analysis.get('feedback', '').strip())
    return has_non_zero and has_feedback

def get_id_mapping(input_file: str) -> dict:
    """Obtain the complete ID mapping of the current file"""
    try:
        group_name = parse_group_from_filename(input_file)
        with get_connection() as conn:
            df = pd.read_sql('''
                SELECT m.original_id, m.system_id 
                FROM id_mappings m
                JOIN groups g ON m.group_name = g.group_name
                WHERE m.group_name = ?
            ''', conn, params=(group_name,))
            return dict(zip(df['original_id'], df['system_id']))
    except Exception as e:
        print(f"Mapping loading failed: {str(e)}")
        return {}

def generate_report(results: dict, input_file: str):
    import sys
    import io
    
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

    print("\n=== Collaborative Ability Analysis Report ===")
    for talker, data in results.items():
        try:
            feedback = data.get('feedback', 'No available feedback')
            safe_feedback = feedback.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
            
            print(f"\nMember: {talker}")
            if 'error' in data:
                print(f"  error: {data['error']}")
                continue
            
            print("Detailed feedback:")
            print(safe_feedback)
            
            print("\nSkill Score:")
            for criterion, score in data.get('scores', {}).items():
                safe_criterion = COLLAB_CRITERIA[criterion].encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
                print(f"  {safe_criterion}: {score}/5")
                
        except UnicodeEncodeError as e:
            print(f"\nMember: {talker}（Complete information cannot be displayed - Encoding error）")
            print(f"Error Details：{str(e)}")

def get_talker_group(talker_id: str) -> str:
    """从数据库获取用户所属群组"""
    try:
        with get_connection() as conn:
            group = conn.execute('''
                SELECT group_name FROM users 
                WHERE username = ?
            ''', (talker_id,)).fetchone()
            return group[0] if group else "default_group"
    except Exception as e:
        print(f"群组查询失败: {str(e)}")
        return "default_group"

def parse_group_from_filename(file_path):
    try:
        # 统一处理路径分隔符
        normalized = str(file_path).replace('\\', '/')
        filename = normalized.split('/')[-1]  # 获取文件名
        return filename.split('_')[0]
    except:
        return "default_group"

def save_results(talker: str, analysis: dict, id_mapping: dict):
    # Verify the validity of the score
    validated_scores = {}
    for criterion in COLLAB_CRITERIA.keys():
        try:
            value = analysis.get("scores", {}).get(criterion, 0)
            validated_scores[criterion] = min(5, max(0, float(value)))
        except (TypeError, ValueError):
            validated_scores[criterion] = 0.0
    
    record = {
        "talker": talker,
        "timestamp": datetime.now().isoformat(),
        "analysis": {
            **analysis,
            "scores": validated_scores
        },
        "schema_version": SCHEMA_VERSION,
        "group": parse_group_from_filename(INPUT_FILE)
    }

    filename = DATA_DIR / f"{talker}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Save failed: {str(e)}")

def main():
    args = parse_args()
    INPUT_FILE = args.input
    init_environment()
    chat_data = load_chat_data()
    id_mapping = get_id_mapping(INPUT_FILE)
    
    results = {}
    for talker, messages in chat_data.items():
        analysis = analyze_collaboration(messages)
        save_results(talker, analysis, id_mapping) 
        results[talker] = analysis
    
    generate_report(results, INPUT_FILE)

if __name__ == "__main__":
    main()