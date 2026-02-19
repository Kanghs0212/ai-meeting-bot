import os
import json
import requests
import time
import re
from dotenv import load_dotenv

load_dotenv()

# 주요 기술 용어 발음 사전 (VITO 인식률 극대화용)
PRONUNCIATION_MAP = {
    "AI": "에이아이", "AX": "에이엑스", "DX": "디엑스",
    "CES": "씨이에스", "TIPS": "팁스", "RFP": "알에프피",
    "IPO": "아이피오", "VC": "브이씨", "M&A": "엠엔에이",
    "CEO": "씨이오", "DB": "디비", "B2B": "비투비", "B2G": "비투지"
}

def get_access_token():
    client_id = os.getenv("VITO_CLIENT_ID")
    client_secret = os.getenv("VITO_CLIENT_SECRET")
    resp = requests.post(
        'https://openapi.vito.ai/v1/authenticate',
        data={'client_id': client_id, 'client_secret': client_secret}
    )
    resp.raise_for_status()
    return resp.json()['access_token']

def get_boosting_keywords():
    """terminology.json의 단어들을 VITO가 좋아하는 '한글'로 변환합니다."""
    file_path = "terminology.json"
    if not os.path.exists(file_path): return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        raw_terms = data.get("워터라이즈_멤버", []) + \
                    data.get("위레이저_멤버", []) + \
                    data.get("핵심_용어", [])
        
        processed_keywords = []
        for term in raw_terms:
            if not term: continue
            
            # 1. 이미 한글인 경우 -> 그대로 사용
            if re.fullmatch(r'[가-힣]+', term):
                processed_keywords.append(term)
            
            # 2. 영어인 경우 -> 발음 사전에서 매핑 (사전에 없으면 무시)
            elif term.upper() in PRONUNCIATION_MAP:
                processed_keywords.append(PRONUNCIATION_MAP[term.upper()])
        
        # 중복 제거 및 리스트 반환
        final_list = list(set(processed_keywords))
        print(f"🎯 VITO 부스팅 단어 ({len(final_list)}개): {final_list[:10]}...")
        return final_list[:500]

    except Exception as e:
        print(f"⚠️ 키워드 변환 중 오류: {e}")
        return []

def transcribe_audio_vito(file_path):
    token = get_access_token()
    headers = {'Authorization': f'bearer {token}'}
    
    # 설정: 화자 분리 + 숫자 변환 + 키워드 부스팅
    config = {
        "use_diarization": True,
        "diarization": {"spk_cnt": 0}, 
        "use_itn": True, 
        "use_disfluency_filter": True, # [추가] "음, 어, 그" 같은 간투어 자동 제거
        "use_paragraph_splitter": True, # [추가] 문단 나누기 (Gemini가 읽기 편해짐)
        "keywords": get_boosting_keywords()
    }
    
    print(f"🎙️ VITO 분석 시작 (영어 발음 매핑 적용): {os.path.basename(file_path)}")
    
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://openapi.vito.ai/v1/transcribe',
            headers=headers,
            files={'file': f},
            data={'config': json.dumps(config)}
        )
    
    if resp.status_code != 200:
        print(f"❌ VITO 요청 실패: {resp.text}")
        return None
        
    task_id = resp.json()['id']
    
    # 대기 (Polling)
    while True:
        resp = requests.get(f'https://openapi.vito.ai/v1/transcribe/{task_id}', headers=headers)
        status = resp.json()['status']
        if status == 'completed': break
        if status == 'failed': return None
        time.sleep(5)

    # 결과 포맷팅
    utterances = resp.json()['results']['utterances']
    return "\n".join([f"[참석자 {u['spk']}]: {u['msg']}" for u in utterances])