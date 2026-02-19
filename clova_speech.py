import os
import json
import requests
import time
from dotenv import load_dotenv

load_dotenv()

def get_boosting_keywords():
    """terminology.json의 모든 고유명사를 추출하여 클로바 부스팅용 리스트로 만듭니다."""
    file_path = "terminology.json"
    if not os.path.exists(file_path):
        return []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 모든 멤버 이름과 핵심 용어를 하나의 리스트로 통합
        all_terms = data.get("워터라이즈_멤버", []) + \
                    data.get("위레이저_멤버", []) + \
                    data.get("핵심_용어", [])
        
        # 클로바 API 규격에 맞게 변환 (객체 리스트)
        return [{"words": term} for term in all_terms if term]
    except Exception as e:
        print(f"⚠️ 부스팅 키워드 로드 실패: {e}")
        return []

def transcribe_audio(file_path):
    """로컬 음성 파일을 CLOVA Speech API로 전달하여 화자 분리된 텍스트를 반환합니다."""
    invoke_url = os.getenv("CLOVA_SPEECH_INVOKE_URL")
    secret_key = os.getenv("CLOVA_SPEECH_SECRET_KEY")

    if not invoke_url or not secret_key:
        raise ValueError("❌ CLOVA_SPEECH 설정이 .env에 없습니다.")

    # 1. 요청 파라미터 설정 (화자 분리 및 부스팅 포함)
    request_params = {
        "language": "ko-KR",
        "completion": "sync", # 실시간 동기 방식
        "diarization": {"enable": True, "speakerCountMin": 2, "speakerCountMax": 5},
        "boostings": get_boosting_keywords(),
        "wordAlignment": True,
        "fullText": True
    }

    headers = {
        "X-CLOVASPEECH-API-KEY": secret_key
    }

    # 2. 파일 전송 (Multipart/form-data)
    print(f"🎙️ CLOVA Speech에 분석 요청 중: {os.path.basename(file_path)}")
    
    files = {
        "media": open(file_path, "rb"),
        "params": (None, json.dumps(request_params), "application/json")
    }

    try:
        response = requests.post(
            f"{invoke_url}/recognizer/upload",
            headers=headers,
            files=files
        )
        response.raise_for_status()
        result = response.json()

        # 3. 화자 분리된 결과 포맷팅
        formatted_transcript = []
        for segment in result.get("segments", []):
            speaker_name = f"참석자 {segment['speaker']['label']}"
            text = segment["text"]
            formatted_transcript.append(f"[{speaker_name}]: {text}")

        return "\n".join(formatted_transcript)

    except Exception as e:
        print(f"❌ STT 변환 중 오류 발생: {e}")
        return None
    finally:
        files["media"].close()