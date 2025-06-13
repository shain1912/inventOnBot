# InventOnBot - Discord Q&A Bot for Programming Support

프로그래밍 개발 관련 질의응답을 위한 Discord 봇입니다. 사용자가 `/질문` 명령어로 질문을 등록하면 관리자만 볼 수 있는 프라이빗 스레드가 생성되어 개인화된 지원을 제공합니다.

## 주요 기능

### 🔐 프라이빗 질의응답 시스템

- 질문자와 관리자만 접근 가능한 프라이빗 스레드 자동 생성
- 다른 사용자는 타인의 질문을 볼 수 없음
- 관리자는 모든 질문에 접근 가능

### 📷 이미지 첨부 시스템

- 질문자와 관리자 모두 이미지 첨부 가능
- 스크린샷, 에러 화면, 코드 예시 이미지 지원
- 자동 이미지 감지 및 확인 메시지
- 드래그&드롭 또는 파일 선택으로 간편 업로드
- PNG, JPG, JPEG, GIF, BMP, WebP 형식 지원

### 📝 구조화된 질문 폼

**필수 필드:**

- 운영체제 (OS)
- 프로그래밍 언어
- 에러 메시지
- 원래 하려던 목적

**선택 필드:**

- 코드 스니펫
- 로그 파일
- 스크린샷 설명
- 이미 시도해본 조치들

### 📚 FAQ 시스템

- 관리자가 자주 묻는 질문 등록 및 관리
- 키워드 기반 FAQ 검색 기능
- 자동 FAQ 추천 시스템 (질문 내용 분석)
- FAQ 추가, 수정, 삭제 기능
- 사용자 친화적인 검색 및 목록 기능

### 🎯 관리자 기능

- 질문 상태 관리 (open, in_progress, solved, closed)
- 답변 등록 및 해결책 표시
- 질문 검색 및 통계 조회
- 사용자 알림 시스템

### 🚀 추가 기능

- 코드 문법 하이라이팅
- FAQ 시스템 (구현 예정)
- 통계 및 로그 관리 (구현 예정)
- 자동 알림 시스템

## 설치 및 설정

### 1. 환경 설정

```bash
# 가상환경 생성
conda create -n discord python=3.13

# 가상환경 활성화 (Windows)
conda activate discord

# 패키지 설치
pip install -r requirements.txt
```

### 2. Discord 봇 설정

1. [Discord Developer Portal](https://discord.com/developers/applications)에서 새 애플리케이션 생성
2. Bot 섹션에서 봇 토큰 생성
3. OAuth2 > URL Generator에서 다음 권한 설정:
   - Scopes: `bot`, `applications.commands`
   - Bot Permissions:
     - Send Messages
     - Use Slash Commands
     - Create Private Threads
     - Manage Threads
     - Embed Links
     - Attach Files
     - Read Message History

### 3. 환경변수 설정

```bash
# .env 파일 생성 (.env.example 참고)
cp .env.example .env
```

`.env` 파일 편집:

```env
DISCORD_TOKEN=your_discord_bot_token_here
ADMIN_ROLE_ID=your_admin_role_id_here
BOT_PREFIX=!
DATABASE_PATH=database/bot.db
LOG_LEVEL=INFO
LOG_FILE=logs/bot.log
```

### 4. 봇 실행

```bash
python main.py
```

## 프로젝트 구조

```
inventOnBot/
├── main.py                 # 봇 메인 실행 파일
├── requirements.txt        # Python 패키지 의존성
├── .env.example           # 환경변수 템플릿
├── bot/                   # 봇 관련 코드
│   ├── cogs/             # Discord.py Cogs
│   │   ├── question_handler.py    # 질문 처리
│   │   ├── admin_commands.py      # 관리자 명령어
│   │   ├── image_handler.py       # 이미지 업로드 처리
│   │   └── faq_system.py          # FAQ 시스템 (새로 추가!)
│   └── __init__.py
├── config/                # 설정 파일
│   ├── config.py         # 봇 설정
│   └── __init__.py
├── database/              # 데이터베이스 관련
│   ├── database_manager.py   # DB 매니저
│   ├── bot.db            # SQLite 데이터베이스 (자동 생성)
│   └── __init__.py
├── utils/                 # 유틸리티 함수
│   ├── logger.py         # 로깅 설정
│   └── __init__.py
├── logs/                  # 로그 파일 (자동 생성)
└── tasks/                 # TaskMaster 작업 관리
    └── tasks.json        # 프로젝트 작업 정의
```

## 사용법

### 사용자 명령어

- `/질문`: 새로운 프로그래밍 질문 등록
- `/내질문`: 내가 등록한 질문 목록 확인
- `/faq검색 <키워드>`: FAQ 검색
- `/faq목록`: 전체 FAQ 목록 확인

**이미지 첨부 방법:**

1. 질문 등록 후 생성된 스레드로 이동
2. 스크린샷이나 에러 화면을 드래그&드롭 또는 파일 선택
3. 이미지에 대한 설명 메시지 추가 작성
4. 봇이 자동으로 이미지 업로드를 확인하고 ✅ 리액션 추가

### 관리자 명령어

- `/질문상태 <질문ID> <상태>`: 질문 상태 변경
- `/답변 <질문ID> <답변내용>`: 질문에 답변 등록
- `/이미지답변 <질문ID> <답변내용>`: 이미지와 함께 답변 등록
- `/질문목록`: 모든 질문 목록 확인
- `/질문검색 <키워드>`: 질문 검색
- `/통계`: 봇 사용 통계 확인
- `/faq추가 <질문> <답변> [키워드]`: FAQ 추가
- `/faq수정 <FAQ_ID> [질문] [답변] [키워드]`: FAQ 수정
- `/faq삭제 <FAQ_ID>`: FAQ 삭제

**관리자 이미지 첨부 방법:**

1. `/이미지답변` 명령어로 답변 등록
2. 봇이 이미지 업로드 안내 메시지 표시
3. 해당 스레드에 설명용 이미지 드래그&드롭
4. 필요시 이미지 설명 메시지 추가

## 데이터베이스 스키마

### users 테이블

- `user_id`: Discord 사용자 ID (Primary Key)
- `username`: 사용자명
- `display_name`: 표시명
- `is_admin`: 관리자 여부
- `created_at`: 생성일시

### questions 테이블

- `id`: 질문 ID (Auto Increment)
- `user_id`: 질문자 ID
- `thread_id`: Discord 스레드 ID
- `title`: 질문 제목
- `os`: 운영체제
- `programming_language`: 프로그래밍 언어
- `error_message`: 에러 메시지
- `purpose`: 목적
- `code_snippet`: 코드 (선택)
- `log_files`: 로그 파일 (선택)
- `screenshot_url`: 스크린샷 URL (선택)
- `attempted_solutions`: 시도한 해결책 (선택)
- `status`: 상태 (open, in_progress, solved, closed)
- `created_at`: 생성일시
- `updated_at`: 수정일시

### answers 테이블

- `id`: 답변 ID (Auto Increment)
- `question_id`: 질문 ID
- `admin_id`: 답변자 ID
- `answer_text`: 답변 내용
- `is_solution`: 해결책 여부
- `created_at`: 생성일시

## 개발 진행 상황

현재 구현된 기능:

- ✅ 기본 프로젝트 구조
- ✅ 데이터베이스 스키마 및 매니저
- ✅ Discord 봇 기본 설정
- ✅ 질문 등록 슬래시 커맨드
- ✅ 구조화된 질문 모달 폼
- ✅ 프라이빗 스레드 생성
- ✅ 관리자 명령어 기본 구조
- ✅ 로깅 시스템
- ✅ **이미지 첨부 기능 (새로 추가!)**
  - 질문자와 관리자 모두 이미지 업로드 가능
  - 자동 이미지 감지 및 확인 시스템
  - 다양한 이미지 형식 지원 (PNG, JPG, GIF 등)
  - `/이미지답변` 관리자 전용 명령어

개발 예정 기능:

- ❌ FAQ 시스템 (완료!)
- 🔄 고급 검색 기능
- 🔄 상세 통계 대시보드
- 🔄 자동 코드 리뷰 기능
- 🔄 디버그 세션 스케줄링

## 추천 추가 기능

1. **스마트 태깅 시스템**: 질문 내용을 분석하여 자동으로 태그 부여
2. **솔루션 레이팅**: 답변에 대한 평가 시스템
3. **전문가 멘션**: 특정 분야 전문가 자동 호출
4. **코드 실행 환경**: 안전한 샌드박스에서 코드 테스트
5. **AI 기반 초기 진단**: 질문 등록 시 AI가 1차 분석 제공
6. **학습 리소스 추천**: 질문 주제에 맞는 학습 자료 추천
7. **진행 상황 추적**: 장기간 진행되는 문제의 진행 상황 시각화

## 라이선스

이 프로젝트는 MIT 라이선스 하에 배포됩니다.

## 기여

프로젝트 개선을 위한 기여를 환영합니다! Issue나 Pull Request를 통해 참여해주세요.

## 지원

문제가 발생하거나 기능 제안이 있으시면 GitHub Issues를 통해 알려주세요.
