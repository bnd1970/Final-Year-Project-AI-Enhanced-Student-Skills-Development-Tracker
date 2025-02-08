from openai import OpenAI

# Configuration
API_KEY = "sk-58d92e234db44ad5904ac10a9a4374e9"
MODEL_NAME = "deepseek-chat"

# System role setting
SYSTEM_PROMPT = """You are a professional academic skills development assistant, specializing in helping students improve academic writing and language learning abilities. Please analyze based on the following principles:
1. Grammar checking and correction suggestions
2. Academic writing structure analysis
3. Logical coherence evaluation
4. Vocabulary usage appropriateness
5. Providing improvement suggestions and alternative expressions
6. Identifying language learning points
Please provide feedback in a friendly and encouraging tone, focusing on actionable improvement suggestions."""

# Initialize client
client = OpenAI(
    api_key=API_KEY,
    base_url="https://api.deepseek.com",
)

def analyze_content(user_input):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.7,
            stream=False
        )
        return response.choices[0].message.content
    
    except Exception as e:
        print(f"API call failed: {str(e)}")
        return None

def main():
    print("Academic Writing & Language Learning Assistant\nEnter your text for analysis (type 'exit' to quit)")
    
    while True:
        user_input = input("\nStudent Input: ").strip()
        if user_input.lower() == 'exit':
            break
            
        if not user_input:
            print("Please enter valid content")
            continue
            
        print("\nAnalyzing...")
        feedback = analyze_content(user_input)
        
        if feedback:
            print("\nFeedback:")
            print(feedback)
        else:
            print("Failed to get valid feedback")

if __name__ == "__main__":H
    main()