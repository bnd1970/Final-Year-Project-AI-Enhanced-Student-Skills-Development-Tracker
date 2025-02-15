#Instead of using the API, use the local model by ollama. 
from ollama import chat

# Configuration
MODEL_NAME = "deepseek-r1:14b"

# System role setting
SYSTEM_PROMPT = """You are a professional academic skills development assistant, specializing in helping students improve academic writing and language learning abilities. Please analyze based on the following principles:
1. Grammar checking and correction suggestions
2. Academic writing structure analysis
3. Logical coherence evaluation
4. Vocabulary usage appropriateness
5. Providing improvement suggestions and alternative expressions
6. Identifying language learning points
Please provide feedback in a friendly and encouraging tone, focusing on actionable improvement suggestions."""

def analyze_content(user_input):
    try:
        response = chat(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            options={
                "temperature": 0.7,
                #"num_ctx": 4096
            }
        )
        return response['message']['content']
    
    except Exception as e:
        print(f"API Error: {str(e)}")
        return None

def main():
    print("Academic Writing Assistant\nEnter text (type 'exit' to quit)")
    
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
            print("No feedback received")

if __name__ == "__main__":
    main()