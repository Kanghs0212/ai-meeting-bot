import os
import json
import glob
import google.generativeai as genai
from pypdf import PdfReader
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# API 키 설정
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY가 설정되지 않았습니다.")
genai.configure(api_key=api_key)

# 설정
JSON_FILE_PATH = "terminology.json"
PDF_FOLDER_NAME = "주간업무pdf"  # 👈 PDF를 넣어둘 폴더 이름

def get_latest_pdf(folder_name):
    """지정된 폴더에서 가장 최신 PDF 파일을 찾아 경로를 반환합니다."""
    
    # 폴더가 없으면 생성하고 안내
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"📁 '{folder_name}' 폴더가 없어 새로 생성했습니다. 이곳에 PDF 파일을 넣어주세요.")
        return None

    # 폴더 내의 모든 .pdf 파일 패턴 검색
    search_path = os.path.join(folder_name, "*.pdf")
    list_of_files = glob.glob(search_path)

    if not list_of_files:
        print(f"📭 '{folder_name}' 폴더 내에 PDF 파일이 없습니다.")
        return None

    # 가장 최근에 수정된 파일 찾기 (key=os.path.getmtime)
    latest_file = max(list_of_files, key=os.path.getmtime)
    return latest_file

def load_existing_json():
    """기존 terminology.json 파일을 로드합니다."""
    if not os.path.exists(JSON_FILE_PATH):
        print("⚠️ 기존 JSON 파일이 없어 새로 생성합니다.")
        return {
            "워터라이즈_멤버": [],
            "위레이저_멤버": [],
            "수자원공사_멤버": [],
            "핵심_용어": []
        }
    
    with open(JSON_FILE_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_text_from_pdf(pdf_path):
    """PDF에서 텍스트를 추출합니다."""
    try:
        reader = PdfReader(pdf_path)
        text = ""
        # 전체 페이지 텍스트 추출
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"❌ PDF 읽기 실패: {e}")
        return None

def extract_terms_with_gemini(text, current_json):
    """Gemini를 이용해 텍스트에서 용어를 추출하고 JSON 형태로 반환받습니다."""
    
    # 3.0 Flash Preview 사용 (없으면 gemini-1.5-flash로 변경)
    model = genai.GenerativeModel('gemini-3-flash-preview') 

    prompt = f"""
    너는 '데이터 마이닝 전문가'야. 아래 제공되는 [문서 텍스트]를 분석해서 인명(멤버), 회사명, 핵심 기술 용어를 추출해줘.
    
    **작업 목표:**
    1. 텍스트에 등장하는 사람 이름과 소속을 파악하여 적절한 그룹(워터라이즈, 위레이저 등)에 분류해.
    2. 소속이 명확하지 않은 사람은 '핵심_용어'나 기존 키에 억지로 넣지 말고 무시해.
    3. 기술적 용어, 프로젝트명, 약어(영어 포함)는 '핵심_용어'에 추가해.
    4. 반드시 아래 JSON 스키마(Schema) 형태를 지켜서 출력해.
    
    **출력 포맷 (JSON Only):**
    {{
      "워터라이즈_멤버": ["이름", "이름"],
      "위레이저_멤버": ["이름"],
      "수자원공사_멤버": ["이름"],
      "핵심_용어": ["용어1", "용어2"]
    }}
    
    **주의사항:**
    - 불필요한 마크다운(```json 등) 없이 순수한 JSON 텍스트만 출력해.
    - 문서 내용을 충실히 반영하되, 기존 데이터와의 중복 여부는 신경 쓰지 마 (내가 처리함).

    [문서 텍스트]:
    {text[:30000]} 
    """

    try:
        response = model.generate_content(prompt)
        response_text = response.text.replace("```json", "").replace("```", "").strip()
        return json.loads(response_text)
    except Exception as e:
        print(f"❌ Gemini 추출 실패: {e}")
        return None

def update_json_file(new_data, current_data):
    """새로 추출된 데이터를 기존 데이터와 병합하고 파일에 저장합니다 (중복 제거)."""
    
    updated_count = 0
    
    for category, items in new_data.items():
        if category not in current_data:
            current_data[category] = []
        
        for item in items:
            clean_item = item.strip()
            if clean_item not in current_data[category]:
                current_data[category].append(clean_item)
                print(f"   ➕ 추가됨 [{category}]: {clean_item}")
                updated_count += 1
    
    if updated_count > 0:
        with open(JSON_FILE_PATH, 'w', encoding='utf-8') as f:
            json.dump(current_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 총 {updated_count}개의 새로운 용어가 저장되었습니다.")
    else:
        print("\n💨 새로 추가할 용어가 없습니다.")

def main():
    print("🔎 최신 PDF 파일을 검색 중입니다...")
    
    # 1. 최신 PDF 파일 경로 가져오기
    target_pdf_path = get_latest_pdf(PDF_FOLDER_NAME)
    
    if not target_pdf_path:
        return

    print(f"📂 분석 대상 파일: '{target_pdf_path}'")
    
    # 2. PDF 텍스트 추출
    pdf_text = extract_text_from_pdf(target_pdf_path)
    if not pdf_text:
        return

    # 3. 기존 JSON 로드
    current_data = load_existing_json()

    # 4. Gemini에게 추출 요청
    print("🤖 Gemini가 문서를 분석하고 용어를 추출 중입니다...")
    extracted_data = extract_terms_with_gemini(pdf_text, current_data)

    if extracted_data:
        # 5. 병합 및 저장
        update_json_file(extracted_data, current_data)

if __name__ == "__main__":
    main()