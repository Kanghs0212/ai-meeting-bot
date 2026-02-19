import datetime
import os
import drive_loader
import main

WATCH_FOLDER_NAME = "회의록"

def get_folder_id(service, folder_name):
    query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None

def run_once():
    service = drive_loader.get_drive_service()
    if not service:
        print("❌ 드라이브 서비스 연결 실패")
        return

    folder_id = get_folder_id(service, WATCH_FOLDER_NAME)
    if not folder_id:
        print(f"❌ 구글 드라이브에서 '{WATCH_FOLDER_NAME}' 폴더를 찾을 수 없습니다.")
        return

    # 최근 6분 이내에 생성된 대상 파일만 검색
    time_threshold = (datetime.datetime.utcnow() - datetime.timedelta(minutes=6)).isoformat() + "Z"

    query = (
        f"'{folder_id}' in parents and trashed = false and "
        f"(mimeType = 'text/plain' or mimeType = 'application/vnd.google-apps.document' or "
        f"mimeType = 'audio/mp4' or mimeType = 'audio/mpeg' or mimeType = 'audio/x-m4a' or "
        f"mimeType = 'audio/wav' or mimeType = 'audio/aac') and "
        f"createdTime > '{time_threshold}'"
    )

    results = service.files().list(q=query, fields="files(id, name, createdTime, mimeType)", orderBy="createdTime desc").execute()
    items = results.get('files', [])

    if not items:
        print("최근 6분 내에 새로 추가된 파일이 없습니다.")
        return

    for item in items:
        file_name = item['name']
        print(f"\n[새 파일 감지] {file_name} -> 자동 처리를 시작합니다...")
        try:
            main.main(file_name)
            print(f"   {file_name} 처리 완료!")
        except Exception as e:
            print(f"   처리 중 오류 발생: {e}")

if __name__ == "__main__":
    print("Cron Watcher 실행 중...")
    run_once()