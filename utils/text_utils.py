import re

def remove_whitespace_patterns(text):
   
    cleaned_text = re.sub(r'[\n\r\t\xa0\u200b\u202f\u3000]', ' ', text)
    cleaned_text = re.sub(r'[ ]+', ' ', cleaned_text)  # 다중 공백을 하나로 축소
    return cleaned_text.strip()