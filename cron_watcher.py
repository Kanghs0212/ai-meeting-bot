import datetime
import os
import drive_loader
import main

WATCH_FOLDER_NAME = "회의록"
PROCESSED_FILE = "processed_history.txt"

def load_processed_files():
    """기존에 처리했던 파일 ID 목록을 불러옵니다."""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, "r") as f:
        return set(line.strip() for line in f if line.strip())

def save_processed_file(file_id):
    """처리 완료한 파일 ID를 메모장에 추가합니다."""
    with open(PROCESSED_FILE, "a") as f:
        f.write(file_id + "\n")

def get_folder_id(service, folder_name):
    query = f"mimeType = 'application/vnd.google-apps.folder' and name = '{folder_name}' and trashed = false"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    items = results.get('files', [])
    return items[0]['id'] if items else None

def run_once():
    service = drive_loader.get_drive_service()
    if not service: return

    folder_id = get_folder_id(service, WATCH_FOLDER_NAME)
    if not folder_id: return

    # 1. 처리했던 기록 불러오기
    processed_ids = load_processed_files()

    # 2. 딜레이를 대비해 넉넉하게 '최근 24시간' 내의 파일 검색
    time_threshold = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).isoformat() + "Z"

    query = (
        f"'{folder_id}' in parents and trashed = false and "
        f"(mimeType = 'text/plain' or mimeType = 'application/vnd.google-apps.document' or "
        f"mimeType = 'audio/mp4' or mimeType = 'audio/mpeg' or mimeType = 'audio/x-m4a' or "
        f"mimeType = 'audio/wav' or mimeType = 'audio/aac') and "
        f"createdTime > '{time_threshold}'"
    )

    # 과거 파일부터 순서대로 처리하기 위해 asc 정렬
    results = service.files().list(q=query, fields="files(id, name, createdTime, mimeType)", orderBy="createdTime asc").execute()
    items = results.get('files', [])

    new_files_processed = False
    for item in items:
        file_id = item['id']
        file_name = item['name']

        # 3. 이미 메모장에 있는 파일이면 무시하고 넘어감
        if file_id in processed_ids:
            continue 

        print(f"\n🔔 [새 파일 감지] {file_name} -> 🚀 자동 처리를 시작합니다...")
        try:
            main.main(file_name)
            print(f"   ✅ {file_name} 처리 완료!")
            
            # 4. 처리가 무사히 끝났으면 메모장에 ID 적기
            save_processed_file(file_id)
            new_files_processed = True
        except Exception as e:
            print(f"   ❌ 처리 중 오류 발생: {e}")

    if not new_files_processed:
        print("📭 새로 처리할 파일이 없습니다.")

if __name__ == "__main__":
    print("👀 Cron Watcher 실행 중...")
    run_once()