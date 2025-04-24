#Score according to the quality of the conversation
import pandas as pd
import json
import re
import os
import argparse
from datetime import datetime
from pathlib import Path
from ollama import chat

# Configuration
MODEL_NAME = "deepseek-r1:8b"
DATA_DIR = Path("user_progress")
SCHEMA_VERSION = "0.4.0"
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
    "feedback": "详细分析...",
    "scores": {{
        "participation": 0-5,
        "initiative": 0-5,
        "problem_solving": 0-5,
        "coordination": 0-5,
        "responsiveness": 0-5
    }},
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
    """Load and preprocess chat data"""
    df = pd.read_excel(INPUT_FILE, sheet_name="Sheet1")
    df = df[df['type_name'] == '文本']   # Only analyze text messages
    return df.groupby('talker')['msg'].apply(list).to_dict()

def parse_llm_response(response: str) -> dict:
    """Load and preprocess chat data"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", response)
        return json.loads(json_match.group()) if json_match else {"error": "Parsing failed"}

def analyze_collaboration(messages: list) -> dict:
    """Analyze individual member's collaboration ability"""
    context = "\n".join([f"消息{i+1}: {msg}" for i, msg in enumerate(messages)])
    
    try:
        response = chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": context}
            ],
            options={"temperature": 0.3}
        )
        return parse_llm_response(response['message']['content'])
    except Exception as e:
        return {"error": str(e)}

def save_results(talker: str, analysis: dict):
    """Save analysis results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"{talker}_{timestamp}.json"
    
    record = {
        "talker": talker,
        "timestamp": datetime.now().isoformat(),
        "messages_count": len(analysis.get('context', [])),
        "analysis": analysis,
        "schema_version": SCHEMA_VERSION
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Save failed: {str(e)}")

def get_id_mapping():
    try:
        mapping_df = pd.read_excel("user_inform/user_mapping.xlsx", engine='openpyxl')
        return mapping_df.set_index('original_id')['system_id'].to_dict()
    except FileNotFoundError:
        return {}

def generate_report(results: dict):
    """生成分析报告"""
    # 加载映射数据
    try:
        mapping_df = pd.read_excel("user_inform/user_mapping.xlsx", engine='openpyxl')
        id_map = dict(zip(
            zip(mapping_df['group'], mapping_df['original_id']),
            mapping_df['system_id']
        ))
    except FileNotFoundError:
        id_map = {}

    group_name = parse_group_from_filename(INPUT_FILE)
    
    print("\n=== 协作能力分析报告 ===")
    for talker, data in results.items():
        # 获取群组信息（假设每个talker属于一个群组）
        group = get_talker_group(talker)  # 需要实现该函数
        
        # 优先显示映射ID
        display_name = id_map.get((group, talker), talker)
        
        print(f"\n成员: {display_name}")
        if 'error' in data:
            print(f"  错误: {data['error']}")
            continue
        
        print("详细反馈:")
        print(data.get('feedback', '无可用反馈'))
        
        print("\n技能评分:")
        for criterion, score in data.get('scores', {}).items():
            print(f"  {COLLAB_CRITERIA[criterion]}: {score}/5")

def get_talker_group(talker_id: str) -> str:
    """获取用户所属群组（需根据实际数据结构实现）"""
    with get_connection() as conn:
        group = conn.execute(
            "SELECT group_name FROM users WHERE username=?",
            (talker_id,)
        ).fetchone()
    return group[0] if group else "default_group"

def parse_group_from_filename(file_path):
    """从文件名解析群组信息"""
    try:
        # 示例：文件名格式 group1_202305.xlsx
        return Path(file_path).stem.split('_')[0]
    except:
        return "default_group"

def main():
    args = parse_args()
    INPUT_FILE = args.input
    init_environment()
    chat_data = load_chat_data()
    results = {}

    print(f"Starting analysis of {len(chat_data)} members' collaboration abilities...")
    
    for talker, messages in chat_data.items():
        print(f"\nAnalyzing: {talker} ({len(messages)} messages)")
        analysis = analyze_collaboration(messages)
        results[talker] = analysis
        save_results(talker, analysis)
    
    generate_report(results)
    print("\nAnalysis complete! Results saved to", DATA_DIR)

if __name__ == "__main__":
    main()