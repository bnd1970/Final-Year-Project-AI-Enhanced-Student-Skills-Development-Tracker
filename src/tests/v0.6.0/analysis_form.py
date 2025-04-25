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

# Configuration
MODEL_NAME = "deepseek-r1:8b"
DATA_DIR = Path("user_progress")
SCHEMA_VERSION = "0.5.0"
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
    """Load and preprocess chat data"""
    df = pd.read_excel(INPUT_FILE, sheet_name="Sheet1")
    df = df[df['type_name'] == '文本']   # Only analyze text messages
    return df.groupby('talker')['msg'].apply(list).to_dict()

def parse_llm_response(response: str) -> dict:
    try:
        # 移除可能的非JSON前缀/后缀
        cleaned = re.sub(r'^[^{]*', '', response, flags=re.DOTALL)
        cleaned = re.sub(r'[^}]*$', '', cleaned, flags=re.DOTALL)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {"error": "Parsing failed"}

def analyze_collaboration(messages: list) -> dict:
    """Analyze individual member's collaboration ability"""
    context = "\n".join([f"消息{i+1}: {msg}" for i, msg in enumerate(messages)])
    
    for _ in range(3):
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

def get_id_mapping(input_file: str) -> dict:
    """从数据库获取当前文件的群组映射"""
    try:
        # 解析文件名中的群组信息
        group_name = Path(input_file).stem.split('_')[0]
        
        with get_connection() as conn:
            df = pd.read_sql('''
                SELECT original_id, system_id 
                FROM id_mappings 
                WHERE group_name = ?
            ''', conn, params=(group_name,))
            return dict(zip(df['original_id'], df['system_id']))
    except Exception as e:
        print(f"映射加载失败: {str(e)}")
        return {}

def generate_report(results: dict, input_file: str):
    """生成分析报告（使用数据库映射）"""
    # 加载数据库映射
    id_mapping = get_id_mapping(input_file)  # 调用优化后的函数
    
    print("\n=== 协作能力分析报告 ===")
    for talker, data in results.items():
        # 显示映射后的系统ID（若存在）
        display_name = id_mapping.get(talker, talker)
        
        print(f"\n成员: {display_name}")
        if 'error' in data:
            print(f"  错误: {data['error']}")
            continue
        
        print("详细反馈:")
        print(data.get('feedback', '无可用反馈'))
        
        print("\n技能评分:")
        for criterion, score in data.get('scores', {}).items():
            print(f"  {COLLAB_CRITERIA[criterion]}: {score}/5")

    group_name = parse_group_from_filename(INPUT_FILE)
    
    print("\n=== 协作能力分析报告 ===")
    for talker, data in results.items():
        # 获取群组信息（假设每个talker属于一个群组）
        group = get_talker_group(talker)  # 需要实现该函数
        
        # 优先显示映射ID
        display_name = id_mapping.get(talker, talker)
        
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

def save_results(talker: str, analysis: dict):
    """保存分析结果（增加类型验证）"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = DATA_DIR / f"{talker}_{timestamp}.json"
    
    def validate_scores(scores: dict) -> dict:
        """强制转换评分值为浮点数"""
        validated = {}
        for criterion in COLLAB_CRITERIA.keys():
            try:
                value = scores.get(criterion, 0)
                validated[criterion] = float(value)
            except (TypeError, ValueError):
                print(f"警告：字段 {criterion} 的值 {value} 无效，已设为0分")
                validated[criterion] = 0.0
        return validated

    if "scores" in analysis:
        analysis["scores"] = validate_scores(analysis["scores"])

    record = {
        "talker": talker,
        "timestamp": datetime.now().isoformat(),
        "messages_count": len(analysis.get('context', [])),
        "analysis": analysis,
        "schema_version": SCHEMA_VERSION,
        "group": parse_group_from_filename(INPUT_FILE),
        "original_id": talker
    }

    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"保存失败: {str(e)}")

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
    
    generate_report(results, INPUT_FILE) 
    print("\nAnalysis complete! Results saved to", DATA_DIR)

if __name__ == "__main__":
    main()