import time
import datetime
import os
import sys

# 기존 모듈 가져오기
import drive_loader
import main

# ==========================================
# [설정] 감시할 폴더 및 주기
# ==========================================
WATCH_FOLDER_NAME = "회의록"   # 구글 드라이브 내 폴더명
CHECK_INTERVAL = 20          # 감시 주기 
# ==========================================

def get_folder_id(service, folder_name):
    """폴더 이름으로 ID를 찾습니다"""
    query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None

def watch_drive():
    service = drive_loader.get_drive_service()
    if not service:
        print("❌ 드라이브 서비스 연결 실패: credentials.json을 확인해주세요.")
        return

    # 1. 감시할 폴더 ID 찾기
    folder_id = get_folder_id(service, WATCH_FOLDER_NAME)
    if not folder_id:
        print(f"❌ 구글 드라이브에서 '{WATCH_FOLDER_NAME}' 폴더를 찾을 수 없습니다.")
        print(f"   -> 구글 드라이브 최상위에 '{WATCH_FOLDER_NAME}' 폴더를 만들어주세요.")
        return

    print(f"===================================================")
    print(f"👀 '{WATCH_FOLDER_NAME}' 폴더 감시를 시작합니다... (주기: {CHECK_INTERVAL}초)")
    print(f"   [Ctrl + C]를 누르면 종료됩니다.")
    print(f"===================================================")

    # 2. 감시 시작 시간 설정 (UTC 기준)
    # 프로그램 실행 시점 이후에 올라온 파일만 처리합니다.
    last_check_time = datetime.datetime.utcnow().isoformat() + "Z"

    # 이미 처리한 파일 ID 저장소 (중복 실행 방지)
    processed_files = set()

    try:
        while True:
            # 3. 새로운 파일 검색 (오디오 파일 형식 추가)
            # m4a는 보통 'audio/mp4' 또는 'audio/x-m4a'로 인식됩니다.
            query = (
                f"'{folder_id}' in parents and "
                f"trashed = false and "
                f"(mimeType = 'text/plain' or "
                f"mimeType = 'application/vnd.google-apps.document' or "
                f"mimeType = 'audio/mp4' or "
                f"mimeType = 'audio/mpeg' or "
                f"mimeType = 'audio/x-m4a' or "
                f"mimeType = 'audio/wav' or "
                f"mimeType = 'audio/aac') and "
                f"createdTime > '{last_check_time}'"
            )

            # API 호출
            try:
                results = service.files().list(
                    q=query,
                    fields="files(id, name, createdTime, mimeType)", # mimeType 필드 추가 권장
                    orderBy="createdTime desc"
                ).execute()
            except Exception as e:
                print(f"⚠️ API 호출 중 일시적 오류 발생 (다음 주기에 재시도): {e}")
                time.sleep(CHECK_INTERVAL)
                continue

            items = results.get('files', [])

            # 4. 새 파일 발견 시 처리
            if items:
                # 발견된 파일 중 가장 최근 시간으로 기준점 갱신
                # (주의: 파일 처리 시간 동안 또 다른 파일이 들어올 수 있으므로, 처리 전 미리 시간 갱신은 신중해야 함.
                #  여기서는 간단하게 가장 최신 파일의 생성 시간을 다음 기준점으로 삼습니다.)
                new_last_check_time = items[0]['createdTime']
                
                for item in items:
                    file_id = item['id']
                    file_name = item['name']

                    # 이미 처리했거나, 기준 시간보다 같거나 이전이면 패스 (안전장치)
                    if file_id in processed_files:
                        continue
                    
                    # 파일 처리 시작
                    print(f"\n🔔 [새 파일 감지] {file_name}")
                    print(f"   --> 🚀 자동 처리를 시작합니다...")
                    
                    try:
                        # main.py의 핵심 로직 실행 (파일 이름만 넘김)
                        main.main(file_name)
                        print(f"   ✅ {file_name} 처리 완료! 다시 대기 모드로 돌아갑니다.\n")
                    except Exception as e:
                        print(f"   ❌ 처리 중 오류 발생: {e}")

                    # 처리 완료 목록에 추가
                    processed_files.add(file_id)
                
                # 기준 시간 업데이트
                last_check_time = new_last_check_time

            # 5. 대기 
            time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        print("\n🛑 사용자 요청으로 감시를 종료합니다.")

if __name__ == "__main__":
    watch_drive()