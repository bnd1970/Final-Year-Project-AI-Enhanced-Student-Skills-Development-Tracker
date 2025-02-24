import csv
import openpyxl
from pathlib import Path
from typing import List, Dict

class FileReader:
    @staticmethod
    def detect_format(file_path: Path) -> str:
        if file_path.suffix.lower() == '.csv':
            return 'csv'
        elif file_path.suffix.lower() in ('.xls', '.xlsx'):
            return 'excel'
        else:
            return 'text'

    @staticmethod
    def read_content(file_path: Path) -> List[Dict]:
        file_type = FileReader.detect_format(file_path)
        
        try:
            if file_type == 'csv':
                return FileReader._read_csv(file_path)
            elif file_type == 'excel':
                return FileReader._read_excel(file_path)
            else:
                return FileReader._read_text(file_path)
        except Exception as e:
            raise ValueError(f"Error reading {file_path}: {str(e)}")

    @staticmethod
    def _read_csv(file_path: Path) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            return [row for row in reader]

    @staticmethod
    def _read_excel(file_path: Path) -> List[Dict]:
        wb = openpyxl.load_workbook(file_path)
        sheet = wb.active
        headers = [cell.value for cell in sheet[1]]
        
        records = []
        for row in sheet.iter_rows(min_row=2):
            record = {headers[i]: cell.value for i, cell in enumerate(row)}
            records.append(record)
        return records

    @staticmethod
    def _read_text(file_path: Path) -> List[Dict]:
        with open(file_path, 'r', encoding='utf-8') as f:
            return [{"content": line.strip()} for line in f if line.strip()]