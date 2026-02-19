import os
import notion_uploader
from dotenv import load_dotenv

load_dotenv()

def test_upload(file_path):
    # 1. 파일 존재 여부 확인
    if not os.path.exists(file_path):
        print(f"❌ 테스트 실패: '{file_path}' 파일이 없습니다.")
        return

    # 2. 파일 읽기
    print(f"테스트 파일 읽기: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        markdown_content = f.read()

    # 3. 제목 설정 (파일명에서 확장자 제거)
    # 예: "회의록/0107회의.md" -> "0107회의"
    page_title = os.path.splitext(os.path.basename(file_path))[0]

    # 4. 업로드 실행
    print("---------------------------------------------------")
    print(f"'{page_title}' 제목으로 업로드 테스트 시작...")
    
    try:
        notion_uploader.upload_page(page_title, markdown_content)
        print("---------------------------------------------------")
        print("✅ 테스트 성공! 노션 페이지를 확인해보세요.")
    except Exception as e:
        print("---------------------------------------------------")
        print(f"❌ 테스트 중 에러 발생: {e}")

if __name__ == "__main__":
    target_file = "회의록/0107회의.md"
    test_upload(target_file)