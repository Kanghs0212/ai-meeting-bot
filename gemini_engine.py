import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from google.generativeai.types import HarmCategory, HarmBlockThreshold

# 환경 변수 로드
load_dotenv()

def load_terminology():
    """terminology.json 파일에서 용어 및 멤버 정보를 읽어와 문자열로 변환합니다."""
    file_path = "terminology.json"
    
    # 파일이 없을 경우 대비한 기본값
    default_term = "- [시스템 알림]: 용어 설정 파일을 찾을 수 없습니다."
    
    if not os.path.exists(file_path):
        print(f"⚠️ 경고: '{file_path}' 파일이 없습니다. 기본 설정으로 진행합니다.")
        return default_term

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # 리스트를 콤마로 연결하여 문자열로 변환
        water_members = ", ".join(data.get("워터라이즈_멤버", []))
        welaser_members = ", ".join(data.get("위레이저_멤버", []))
        key_terms = ", ".join(data.get("핵심_용어", []))

        return f"""
    - [워터라이즈]: {water_members}
    - [위레이저]: {welaser_members}
    - [핵심 용어]: {key_terms}
        """
    except Exception as e:
        print(f"❌ 용어 파일 로드 중 오류: {e}")
        return default_term

def generate_minutes(transcript_text):
    """
    회의 전사 텍스트를 입력받아 Gemini 2.5 Flash로 분석된 마크다운을 반환합니다.
    """

    # [수정] 안전 설정 정의 (모든 카테고리에 대해 차단 안 함 설정)
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("❌ GEMINI_API_KEY가 설정되지 않았습니다.")

    genai.configure(api_key=api_key)
    
    # JSON 파일에서 용어 로드
    term_guide = load_terminology()

    # 시스템 프롬프트 (f-string을 사용하여 term_guide 삽입)
    SYSTEM_PROMPT = f"""
    너는 '워터아이즈'의 전략 기획팀 소속 수석 비즈니스 라이터야. 
    제공되는 '회의 전사 텍스트'를 분석하여, **조직 차원의 논의 맥락과 기술적 상세 내용이 통합된 '고급 비즈니스 회의록'**을 작성해줘.

    결과물은 **Notion 페이지**에 업로드될 것이므로, 노션의 시각적 기능(이모지, 인용구, 콜아웃 스타일)을 적극 활용해 가독성을 극대화해야 해.

    **1. 성함 및 용어 교정 가이드**
    {term_guide}

    **2. 할루시네이션 방지 및 작성 원칙 (최우선 준수)**
    - **사실 기반 서술**: 전사 텍스트에 명시되지 않은 수치나 내용은 절대 추측하여 적지 않는다. 내용이 불분명할 경우 '확인 필요' 또는 'TBD'로 기재한다.
    - **수치 보존**: 텍스트에 언급된 수치(금액, 버전, 날짜 등)가 있다면 정확히 기재하되, 언급되지 않았다면 임의로 생성하지 않는다.
    - **탈 화자 중심**: '누가 말했다'는 표현보다는 '어떤 의견이 제시되었다', '결정되었다' 등 조직 관점에서 서술한다.
    - 영어 약어: [AI, AX, CES, TIPS] 등은 한글 발음(에이아이 등)으로 적혀있어도 영문 약어로 복원해.
    
    **3. Notion 최적화 서식 가이드**
    - **인용구(`> `) 활용**: 각 안건의 '현황' 요약은 반드시 인용구 문법을 사용한다.
    - **소제목 스타일**: 안건 내 '논의 과정', '제안된 의견' 등의 소제목 앞에는 번호(1.)나 불렛(-)을 붙이지 않고, **이모지와 굵은 글씨**만 사용한다.
    - **체크박스(`- [ ]`)**: 차기 회의 준비사항 등에 적극 활용한다.
    - **불필요한 서론 절대 금지**: 제목(# 📝 워터아이즈...) 앞이나 뒤에 'Note', '안내', '인사말', '수석 에디터 의견' 등이 있으면 제거해라.

    **4. 보고서 구조 (엄격히 준수)**

    # 📝 워터아이즈 비대면 미팅 회의록

    ## 1. 회의 개요
    - **목적 및 배경**: (시장 상황과 기업별 역할을 포함해 서술, 참석자 명단과 회의날짜는 적지 말것)
    - **핵심 안건**: (불렛 포인트로 작성)

    ---

    ## 2. 안건별 상세 논의 내용
    *(각 안건마다 아래 포맷을 반복)*

    ### [안건 명]
    > **현황 및 이슈 요약**
    > (이곳에 안건의 배경과 문제점을 핵심만 요약하여 인용구로 작성)

    **논의 과정**
    - (의견 흐름을 인과관계에 따라 서술)
    - (단순 발언 나열이 아닌 논리적 흐름으로 정리)

    **제안된 의견**
    - (구체적인 기술 스택, 수치 등 포함. 단, 원문에 없으면 작성하지 않음)

    **최종 결정사항**
    - (결정된 내용을 명확하게 기술)

    ---

    ## 3. 실행 계획 (Action Plan)
    *(아래 내용을 마크다운 표(Table)로 작성)*
    | 업무 내용 |  마감 기한 | 비고 |
    |---|---|---|
    | (업무) | (YYYY.MM.DD 또는 미정) | (리스크 등) |

    ## 4. 모니터링 및 리스크
    - **리스크 요인**: 
    - **모니터링 지표**: 진척도 점검 방안

    ## 5. 차기 회의 준비사항
    - [ ] (준비해야 할 자료나 안건)
    - [ ] 사전 검토 사항

    ## 6. 참고사항
    - 용어 설명(RFP, 온디바이스 AI 등) 및 특이사항 (회사 소개는 제외)
    """

    
    
    # --- [Step 1] Gemini 3.0 Flash로 초안 작성 (기존 로직 유지) ---
    generation_config = {
        "temperature": 0.0,
        "top_p": 0.8,
        "top_k": 40
    }
    
    flash_model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview', 
        generation_config=generation_config
    )

    print("🚀 [Step 1] Gemini 3.0 flash가 초안을 작성 중입니다...")
    try:
        draft_response = flash_model.generate_content([SYSTEM_PROMPT, f"회의 전사 원문:\n{transcript_text}"])
        draft_content = draft_response.text
    except Exception as e:
        print(f"❌ Step 1 오류: {e}")
        return None

    # --- [Step 2] Gemini 1.5 Pro로 정밀 팩트 체크 (2차 대조) ---
    print("🧐 [Step 2] Gemini가 원문과 대조하여 사실 무결성을 검증합니다...")
    

    # 교정 전용 지침 (인턴님의 기존 프롬프트는 Step 1에서 이미 쓰였으므로, 여기선 대조에만 집중)
    VERIFICATION_PROMPT = f"""
    너는 비즈니스 문서의 사실 관계와 고유명사를 완벽하게 교정하는 '수석 전략 에디터'야.
    제공된 [초안 회의록]을 [원문 STT] 및 [용어 가이드]와 정밀 대조하여 아래 규칙에 따라 최종본을 확인해.
    너는 초안에서 틀린 부분만 수정을 하는것이며 그 외에는 내용을 적을 필요 없어.

    **1. 날짜 및 계획의 맥락 검증 (Contextual Date Check)**
    - 회의록에 기재된 모든 날짜, 마감 기한, 일정은 단순히 숫자만 보지 마라.
    - [원문 STT]에서 해당 일정이 언급된 **앞뒤 문맥을 세밀히 살펴서**, 논리적으로 타당한 날짜인지 검증해라. 
    - 맥락상 날짜가 모순되거나 원문에 근거가 없는 날짜라면 '확인 필요' 또는 'TBD'로 수정해라.

    **2. 고유명사 및 수치 무결성**
    - 기업명, 부서명, 기술 용어는 가이드를 최우선으로 하라.
    - 금액이나 퍼센트(%) 등 수치는 절대로 임의로 생성하지 마라.

    **3. 성함 및 용어 교정 가이드**
    {term_guide}

    **4. 출력 서식 및 금지 사항**
    - **불필요한 서론 절대 금지**: 제목(# 📝 워터아이즈...) 앞이나 뒤에 'Note', '안내', '인사말', '수석 에디터 의견' 등이 있으면 제거해라.
    - 응답의 첫 번째 줄은 반드시 '# 📝 워터아이즈 비대면 미팅 회의록'으로 시작해야 한다.

    수정이 완료된 최종 마크다운 문서만 출력해.
    """

    generation_config = {
        "temperature": 0.0,
        "top_p": 0.8,
        "top_k": 40
    }
    
    flash_model = genai.GenerativeModel(
        model_name='gemini-3-flash-preview', 
        generation_config=generation_config
    )

    try:
        final_response = flash_model.generate_content([
            VERIFICATION_PROMPT, 
            f"원문 STT:\n{transcript_text}",
            f"검토할 초안:\n{draft_content}"
        ])
        print("✅ 2단계 검증 완료 (할루시네이션 제거됨)")
        return final_response.text
    except Exception as e:
        print(f"⚠️ Step 2 검증 실패: {e}. 3.0 초안을 그대로 반환합니다.")
        return draft_content