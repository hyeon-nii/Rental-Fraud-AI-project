# classifier/prompt_utils.py
import os

def load_prompt(file_name: str) -> str:
    """prompts 폴더에서 파일 이름에 해당하는 프롬프트를 읽어옵니다."""
    try:
        current_dir = os.path.dirname(__file__)
        file_path = os.path.join(current_dir, 'prompts', file_name)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return "오류: 프롬프트 파일을 찾을 수 없습니다. prompts/system_prompt.txt 파일이 있는지 확인하세요."