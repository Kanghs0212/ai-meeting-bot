import os
import sys
from dotenv import load_dotenv

# 모듈 임포트
import gemini_engine
import notion_uploader
import drive_loader  # 새로 추가된 모듈
import vito_speech

load_dotenv()

def main(target_filename):
    print("===================================================")
    print(f"자동 회의록 생성 에이전트 시작 (Target: {target_filename})")
    print("===================================================")

    # 확장자 확인
    ext = os.path.splitext(target_filename)[1].lower()
    
    # 1. 파일 다운로드 (drive_loader에 audio 다운로드 함수가 있다고 가정)
    # 텍스트 파일이면 기존 로직, 음성이면 클로바 호출
    if ext in ['.txt', '']:
        transcript = drive_loader.download_text_file(target_filename)
    elif ext in ['.m4a', '.mp3', '.wav']:
        audio_path = drive_loader.download_binary_file(target_filename)
        transcript = vito_speech.transcribe_audio_vito(audio_path)
    else:
        print(f"❌ 지원하지 않는 파일 형식입니다: {ext}")
        return

    
    #if not transcript:
    #    print("❌ 회의록 원본을 가져오지 못해 종료합니다.")
    #    return
    
    # 2. Gemini 엔진 호출 (분석)
    markdown_result = gemini_engine.generate_minutes(transcript)
    if not markdown_result:
        print("❌ 분석 결과가 비어있어 종료합니다.")
        return

    # 3. 결과 로컬 백업 (선택 사항)
    output_folder = "회의록"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
        
    # 확장자 제거 후 .md로 저장
    file_base_name = os.path.splitext(target_filename)[0]
    backup_path = os.path.join(output_folder, f"{file_base_name}.md")
    
    with open(backup_path, "w", encoding="utf-8") as f:
        f.write(markdown_result)
    print(f"로컬 백업 완료: {backup_path}")

    # 4. Notion 업로드
    # 제목은 파일명 그대로 사용
    page_title = file_base_name
    notion_uploader.upload_page(page_title, markdown_result)

if __name__ == "__main__":
    # 구글 드라이브에 올려둔 파일명 입력
    # (예: "0107회의.txt" 또는 구글 독스 파일명 "0107회의")
    target_file = "0107회의.txt"
    
    if len(sys.argv) > 1:
        target_file = sys.argv[1]
        
    main(target_file)