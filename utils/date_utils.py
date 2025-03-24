from datetime import datetime

def convert_to_iso(date_str):
    # 불필요한 문자 제거
    date_str = date_str.replace(':', '').strip()

    date_obj = datetime.strptime(date_str, "%Y/%m/%d")
    
    # datetime 객체를 ISO 형식의 문자열로 변환
    iso_date_str = date_obj.isoformat()
    return iso_date_str