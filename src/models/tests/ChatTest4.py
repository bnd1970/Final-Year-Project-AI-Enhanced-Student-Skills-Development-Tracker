#Score according to the quality of the conversation
import pandas as pd
import json
import re
import os
from datetime import datetime
from pathlib import Path
from ollama import chat

# Configuration
MODEL_NAME = "deepseek-r1:14b"
DATA_DIR = Path("user_progress")
SCHEMA_VERSION = "0.2.0"
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

def init_environment():
    """初始化环境"""
    try:
        DATA_DIR.mkdir(exist_ok=True)
        if not os.path.exists(INPUT_FILE):
            raise FileNotFoundError(f"{INPUT_FILE} 不存在")
    except Exception as e:
        print(f"初始化错误: {str(e)}")
        exit(1)

def load_chat_data():
    """加载并预处理聊天数据"""
    df = pd.read_excel(INPUT_FILE, sheet_name="Sheet1")
    df = df[df['type_name'] == '文本']  # 仅分析文本消息
    return df.groupby('talker')['msg'].apply(list).to_dict()

def parse_llm_response(response: str) -> dict:
    """解析LLM响应"""
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        json_match = re.search(r"\{[\s\S]*\}", response)
        return json.loads(json_match.group()) if json_match else {"error": "解析失败"}

def analyze_collaboration(messages: list) -> dict:
    """分析单个成员的协作能力"""
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
    """保存分析结果"""
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
        print(f"保存失败: {str(e)}")

def generate_report(results: dict):
    """生成汇总报告"""
    print("\n=== 协作能力分析报告 ===")
    for talker, data in results.items():
        print(f"\n成员: {talker}")
        if 'error' in data:
            print(f"  错误: {data['error']}")
            continue
        
        print("详细反馈:")
        print(data.get('feedback', '无反馈'))
        
        print("\n能力评分:")
        for criterion, score in data.get('scores', {}).items():
            print(f"  {COLLAB_CRITERIA[criterion]}: {score}/5")

def main():
    init_environment()
    chat_data = load_chat_data()
    results = {}

    print(f"开始分析{len(chat_data)}位成员的协作能力...")
    
    for talker, messages in chat_data.items():
        print(f"\n正在分析: {talker} ({len(messages)}条消息)")
        analysis = analyze_collaboration(messages)
        results[talker] = analysis
        save_results(talker, analysis)
    
    generate_report(results)
    print("\n分析完成！结果已保存至", DATA_DIR)

if __name__ == "__main__":
    main()