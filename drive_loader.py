import os.path
import io
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# 권한 설정 (읽기 전용)
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """구글 드라이브 API 서비스 객체를 생성하고 인증을 처리합니다."""
    creds = None
    # 이전에 로그인한 토큰이 있으면 로드
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 토큰이 없거나 유효하지 않으면 새로 로그인
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # credentials.json이 반드시 필요함
            if not os.path.exists('credentials.json'):
                print("❌ 'credentials.json' 파일을 찾을 수 없습니다. Google Cloud Console에서 다운로드해주세요.")
                return None
                
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # 다음 실행을 위해 토큰 저장
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)
    
def download_text_file(file_name):
    """
    구글 드라이브에서 파일명으로 검색하여 텍스트 내용을 다운로드합니다.
    (.txt 파일이나 Google Docs 문서를 지원하도록 구성)
    """
    service = get_drive_service()
    if not service:
        return None

    print(f"구글 드라이브에서 '{file_name}' 검색 중...")
    
    # 파일명으로 검색 (삭제되지 않은 파일만)
    results = service.files().list(
        q=f"name = '{file_name}' and trashed = false",
        pageSize=1,
        fields="nextPageToken, files(id, name, mimeType)"
    ).execute()
    
    items = results.get('files', [])

    if not items:
        print(f"❌ 드라이브에서 파일을 찾을 수 없습니다: {file_name}")
        return None

    file_id = items[0]['id']
    mime_type = items[0]['mimeType']
    print(f"파일 발견! ID: {file_id}, Type: {mime_type}")

    try:
        content = ""
        # 1. 구글 문서(Docs)인 경우 -> 텍스트로 변환(Export) 필요
        if mime_type == 'application/vnd.google-apps.document':
            request = service.files().export_media(fileId=file_id, mimeType='text/plain')
            content = request.execute().decode('utf-8')
            
        # 2. 일반 텍스트 파일(.txt)인 경우 -> 그대로 다운로드
        else:
            request = service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                # print(f"다운로드 중... {int(status.progress() * 100)}%")
            
            fh.seek(0)
            content = fh.read().decode('utf-8')

        return content

    except Exception as e:
        print(f"❌ 파일 다운로드 중 오류 발생: {e}")
        return None

def download_binary_file(file_name):
    """음성 파일을 다운로드하여 로컬에 저장하고 그 경로를 반환합니다."""
    service = get_drive_service()
    results = service.files().list(
        q=f"name = '{file_name}' and trashed = false",
        pageSize=1, fields="files(id, name)"
    ).execute()
    
    items = results.get('files', [])
    if not items: return None

    file_id = items[0]['id']
    request = service.files().get_media(fileId=file_id)
    
    # 'downloads' 폴더에 저장
    if not os.path.exists("downloads"): os.makedirs("downloads")
    file_path = os.path.join("downloads", file_name)
    
    with io.FileIO(file_path, 'wb') as fh:
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
            
    return file_path


if __name__ == "__main__":
    # 테스트
    text = download_text_file("0107회의.txt")
    if text:
        print(f"✅ 다운로드 성공! (길이: {len(text)}자)")
        print(text[:200] + "...")