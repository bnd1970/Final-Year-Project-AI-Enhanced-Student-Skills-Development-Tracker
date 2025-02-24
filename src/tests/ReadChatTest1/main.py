import argparse
from pathlib import Path
from typing import List
from file_reader import FileReader
from analysis import ConversationAnalyzer
from utils import ProgressManager
from config import config

class WeChatAnalyzer:
    def __init__(self):
        self.reader = FileReader()
        self.analyzer = ConversationAnalyzer()
        self.progress = ProgressManager()

    def process_file(self, file_path: Path):
        try:
            print(f"\nProcessing {file_path.name}...")
            records = self.reader.read_content(file_path)
            for record in records:
                content = record.get('content', '') or record.get('消息内容', '')
                if not content:
                    continue
                
                print(f"Analyzing: {content[:50]}...")
                analysis = self.analyzer.analyze_conversation(content)
                self._display_analysis(analysis)
                self.progress.save_analysis(str(file_path), content, analysis)
        except Exception as e:
            print(f"Error processing {file_path}: {str(e)}")

    def _display_analysis(self, analysis: dict):
        if "error" in analysis:
            print(f"Error: {analysis['error']}")
            return

        print("\n--- Analysis Report ---")
        print(analysis.get('feedback', 'No feedback available'))
        
        if "scores" in analysis:
            print("\nSkill Assessment:")
            for criterion, score in analysis["scores"].items():
                print(f"- {config.SCORE_CRITERIA.get(criterion, criterion)}: {score}/5")

def main():
    parser = argparse.ArgumentParser(description="WeChat Conversation Analyzer")
    parser.add_argument("path", help="File or directory path to analyze")
    args = parser.parse_args()

    analyzer = WeChatAnalyzer()
    path = Path(args.path)

    if path.is_file():
        analyzer.process_file(path)
    elif path.is_dir():
        for file_path in path.glob("*"):
            if file_path.suffix.lower() in ('.txt', '.csv', '.xlsx'):
                analyzer.process_file(file_path)
    else:
        print(f"Path not found: {args.path}")

if __name__ == "__main__":
    main()