# FitBuddy

운동 자세 인식 및 데이터베이스 저장 시스템

## 주요 기능

- 카메라를 통한 실시간 운동 자세 인식
- PostgreSQL 데이터베이스에 운동 데이터 저장
- 사용자 회원가입 및 정보 관리
- REST API 제공 (프론트엔드 연동 가능)

## 설치

### 1. 가상환경 설정
```bash
python -m venv new_venv
source new_venv/bin/activate  # Mac/Linux
# 또는
new_venv\Scripts\activate  # Windows
```

### 2. 패키지 설치
```bash
pip install -r requirements.txt
```

### 3. 데이터베이스 설정
```bash
# PostgreSQL 데이터베이스 생성
createdb fitbuddy_db

# 테이블 생성
python -m FitBuddy.create_db
```

### 4. 환경 변수 설정 (선택)
```bash
# .env.example을 복사해서 .env 파일 생성
cp FitBuddy/.env.example FitBuddy/.env
# .env 파일을 열어서 실제 DB 정보 입력
```

## 사용 방법

### 카메라 앱 실행
```bash
python -m FitBuddy.app
```
- `S` 키: 운동 세션 시작/종료
- `Q` 키: 종료

### API 서버 실행
```bash
python -m FitBuddy.api
# 또는
uvicorn FitBuddy.api:app --reload
```

API 문서: http://localhost:8000/docs

### 사용자 관리
```bash
# 회원가입
python -m FitBuddy.user_manager create \
  --email "user@example.com" \
  --name "홍길동" \
  --password "비밀번호" \
  --password-confirm "비밀번호"

# 사용자 정보 업데이트
python -m FitBuddy.user_manager update-info \
  --user-id 1 \
  --height 175 \
  --weight 70.5 \
  --gender male \
  --goal "체중 감량"
```

## 데이터베이스 구조

- `users`: 사용자 정보 (이메일, 이름, 키, 몸무게, 성별, 운동목적)
- `workouts`: 운동 세션 정보
- `workout_frames`: 프레임별 상세 데이터

## API 엔드포인트

- `POST /api/auth/register` - 회원가입
- `POST /api/auth/login` - 로그인
- `GET /api/user/me` - 현재 사용자 정보
- `PUT /api/user/info` - 사용자 정보 업데이트
- `GET /api/workouts` - 운동 세션 목록
- `POST /api/workouts` - 새 운동 세션 생성

## 깃허브 업로드 전 확인사항

1. `.gitignore` 파일 확인
2. `.env` 파일은 업로드하지 않음 (`.env.example`만 업로드)
3. 민감한 정보(DB 비밀번호 등)는 환경 변수로 관리

