# 📝 EyeNote: AI 기반 회의록 자동화 및 관리 파이프라인

<p>
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white">
  <img src="https://img.shields.io/badge/Google_Gemini-8E75B2?style=for-the-badge&logo=google-gemini&logoColor=white">
  <img src="https://img.shields.io/badge/Notion_API-000000?style=for-the-badge&logo=notion&logoColor=white">
  <img src="https://img.shields.io/badge/Google_Drive-4285F4?style=for-the-badge&logo=googledrive&logoColor=white">
</p>

## 📌 프로젝트 개요 (Overview)
**EyeNote**는 회의 음성 파일이 업로드되는 순간부터 최종 회의록이 사내 위키(Notion)에 정리되기까지의 전 과정을 자동화한 파이프라인입니다. 
단순한 AI 요약을 넘어, 사내 고유 명사(Context)를 주입하고 2차 교차 검증 로직을 도입하여 **LLM의 고질적인 문제인 할루시네이션(환각)을 최소화**한 것이 특징입니다.

## 회의록 예시 이미지
※ 보안 규정 준수를 위해 일부 민감한 데이터(회의 내용 등)는 블라인드 처리하였습니다. 양해부탁드립니다.

<p align="center">
  <img align="center" width="49%"  height="652" alt="제목 없는 디자인 (4)" src="https://github.com/user-attachments/assets/e9b5df87-5c61-4311-a64e-88ae1530f7fc" />
  <img align="center" width="49%" height="700" alt="제목 없는 디자인 (2)" src="https://github.com/user-attachments/assets/04dc9023-a781-4165-be83-283967bc74f1" />
</p>

## ✨ 주요 기능 (Key Features)
* **자동화된 워크플로우 (Watcher & Drive Loader)**
  * Google Drive의 특정 폴더를 모니터링하여 새로운 회의 음성 파일이나 텍스트 전사본이 업로드되면 자동으로 다운로드하고 프로세스를 시작합니다.
* **고성능 STT (Speech-to-Text) 변환**
  * `vito_speech.py`: ReturnZero의 VITO API를 활용하여 한국어 회의 음성을 높은 정확도의 텍스트로 전사합니다.
* **할루시네이션이 통제된 AI 요약 (Gemini Engine)**
  * `gemini_engine.py` & `update_term.py`: 사내 내부 정보 및 전문 용어(Terminology) 컨텍스트를 프롬프트에 주입하여 AI가 없는 내용을 지어내는 현상을 방지합니다.
  * 2차 재검증 로직을 통해 출력 결과물의 신뢰성을 높입니다.
* **Notion 자동 연동 및 아카이빙**
  * `notion_uploader.py`: 생성된 회의록 구조(주요 안건, 결정 사항, To-Do List 등)를 Notion API를 통해 사내 데이터베이스에 자동 업로드합니다.

## ⚙️ 시스템 동작 원리 (Architecture)
1. **Trigger**: 회의 종료 후 녹음 파일을 지정된 Google Drive 폴더에 업로드.
2. **Fetch**: `watcher.py`와 `drive_loader.py`가 이를 감지하고 로컬 환경으로 가져옴.
3. **STT**: `vito_speech.py`가 음성 파일을 텍스트(전사본)로 변환.
4. **Context Injection**: `update_term.py`를 통해 사내 도메인 지식 매핑.
5. **Summarize**: `gemini_engine.py`가 텍스트와 컨텍스트를 바탕으로 회의록 형식으로 요약 및 검증.
6. **Deploy**: `notion_uploader.py`가 최종 결과물을 Notion 페이지에 퍼블리싱.

## 🛠 사전 준비 및 설치 (Prerequisites & Setup)

### 1. 환경 변수 설정 (`.env`)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하고 아래의 API 키들을 입력해야 합니다.
```env
# Google API (Drive & Gemini)
GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-file.json"
GEMINI_API_KEY="your_gemini_api_key"

# VITO API (ReturnZero STT)
VITO_CLIENT_ID="your_vito_client_id"
VITO_CLIENT_SECRET="your_vito_client_secret"

# Notion API
NOTION_TOKEN="your_notion_integration_token"
NOTION_DATABASE_ID="your_target_database_id"

### 2. 패키지 설치

Python 3.8 이상 환경을 권장합니다.

```bash
pip install -r requirements.txt

```

## 🚀 사용법 (Usage)

### 백그라운드 모니터링 실행 (Watch Mode)

자동화 파이프라인을 켜두려면 메인 스크립트를 실행합니다.

```bash
python main.py --mode watch

```

### 특정 파일 수동 처리 (Manual Process)

단일 파일에 대해 회의록 생성을 테스트하거나 즉시 실행하고 싶을 때 사용합니다.

```bash
python main.py --file "sample_meeting.m4a"

```

### 사내 용어사전 업데이트

LLM의 컨텍스트를 강화하기 위해 고유명사나 약어를 업데이트합니다.

```bash
python update_term.py --add "신규단어:의미"

```
