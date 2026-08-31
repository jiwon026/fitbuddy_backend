# FitBuddy Backend

FitBuddy 안드로이드 앱이 사용하는 백엔드입니다. MediaPipe로 운동 자세를 분석하고, 로컬 LLM 챗봇을 제공하며, 공공데이터 기반으로 주변 체육시설을 검색합니다. 운동 기록은 PostgreSQL(PostGIS)에 저장합니다.

안드로이드 클라이언트: [jiwon026/fitbuddy](https://github.com/jiwon026/fitbuddy)

## 구성

이 저장소에는 **FastAPI 앱이 두 개** 있습니다. 혼동하기 쉬우니 주의하세요.

| 파일 | 용도 | 상태 |
|---|---|---|
| [`backend_api.py`](FitBuddy/backend_api.py) | **안드로이드 앱이 실제로 호출하는 서버.** 자세 분석·챗봇·시설 검색 포함 | 사용 중 |
| [`api.py`](FitBuddy/api.py) | `/api/auth/*`, `/api/workouts` 형태의 별도 REST API | 앱에서 사용하지 않음 |

앱을 띄우려면 `backend_api.py` 쪽을 실행하세요.

그 밖에 [`app.py`](FitBuddy/app.py)는 서버가 아니라 **PC 카메라로 직접 자세를 인식해 DB에 기록하는 데스크톱 스크립트**입니다.

## 요구 사항

- Python 3.10 (`venv310` 기준)
- PostgreSQL + **PostGIS 확장** (`workout_frames`, `sports_facilities`가 `geometry` 컬럼을 씁니다)
- 최초 실행 시 Hugging Face에서 `Qwen/Qwen2.5-1.5B-Instruct` (약 3GB)를 내려받습니다

## 설치

```bash
python -m venv venv310
venv310\Scripts\activate        # Windows
# source venv310/bin/activate   # macOS / Linux

pip install -r FitBuddy/requirements.txt
```

DB를 만들고 PostGIS를 활성화한 뒤 테이블을 생성합니다.

```bash
createdb fitbuddy
psql -d fitbuddy -c "CREATE EXTENSION IF NOT EXISTS postgis;"

cd FitBuddy
python create_db.py
```

아래 스크립트는 전부 `FitBuddy` 디렉터리 안에서 실행합니다. 모듈들이 `from database import ...` 처럼 절대 import를 쓰는데 `FitBuddy/`에 `__init__.py`가 없어서, 저장소 루트에서 `python -m FitBuddy.<모듈>` 로 실행하면 import에 실패합니다.

접속 정보는 [`FitBuddy/database.py`](FitBuddy/database.py)의 `DATABASE_URL` 상수에 직접 적혀 있습니다. 환경이 다르면 이 값을 고치세요.

## 실행

서버도 `FitBuddy` 디렉터리 안에서 실행합니다.

```bash
cd FitBuddy
uvicorn backend_api:app --reload --port 8000
```

API 문서: <http://localhost:8000/docs>

기동할 때 LLM을 먼저 메모리에 올리므로 첫 요청 전까지 시간이 좀 걸립니다.

### 안드로이드 앱에서 접속하기

앱의 `BASE_URL`은 현재 배포 서버(`http://54.206.28.172:8000`)를 가리킵니다. 로컬 서버에 붙이려면 에뮬레이터는 `http://10.0.2.2:8000`, 실기기는 PC의 LAN IP를 쓰면 됩니다.

## API

앱이 사용하는 엔드포인트 전체입니다.

| 메서드 | 경로 | 요청 | 응답 |
|---|---|---|---|
| `GET` | `/` | — | `{message}` |
| `POST` | `/signup` | `email, password, name` | `success, message` |
| `POST` | `/login` | `email, password` | `success, message` |
| `POST` | `/user/info` | `email, height_cm, weight_kg, gender, workout_goal` | `success, message` |
| `POST` | `/pose/analyze` | `image_base64` | `knee_angle, hip_angle, torso_tilt, feedback, keypoints[]` |
| `POST` | `/facility/nearby` | `user_lat, user_lon, radius_km, category?` | `[{name, address, lat, lon, distance_km}]` |
| `POST` | `/api/chat` | `message` | `reply` |

`keypoints[]`의 원소는 `{id, x, y, score}`이고 좌표는 0~1로 정규화돼 있습니다. 신뢰도 `score`가 0.3 미만인 관절은 응답에서 제외됩니다.

> **필드 이름은 안드로이드 `FacilityDto`와 1:1로 맞춰져 있습니다.** 시설 응답의 좌표 키를 `latitude`/`longitude`로 바꾸면 앱이 좌표를 `0.0`으로 파싱해 지도 마커가 전부 깨집니다. 마찬가지로 챗봇 라우터의 `prefix="/api"`를 빼면 앱이 호출하는 `/api/chat`이 404가 됩니다.

## 체육시설 데이터 적재

`/facility/nearby`는 `sports_facilities` 테이블을 조회합니다. 공공데이터포털의 체육시설 CSV를 먼저 넣어야 합니다.

원본 CSV는 합계 약 300MB로 GitHub의 100MB 파일 제한을 넘어 저장소에 포함하지 않았습니다(`.gitignore` 처리). 직접 받아 `FitBuddy/data/`에 두고 실행하세요.

```bash
cd FitBuddy
python load_facilities.py
```

검색 방식은 위경도 bounding box로 후보를 좁힌 뒤([`facility_router.py`](FitBuddy/facility_router.py)), haversine으로 실제 거리를 계산해 반경 안의 결과만 거리순으로 돌려줍니다.

## 데이터베이스

| 테이블 | 내용 |
|---|---|
| `users` | 이메일·이름·비밀번호 해시, 키·몸무게·성별·운동 목적 |
| `workouts` | 운동 세션 (종류, 시작/종료, 지속 시간, 거리) |
| `workout_frames` | 프레임별 무릎/고관절/상체 각도, 키포인트 JSON, 관절 위치(PostGIS Point) |
| `sports_facilities` | 체육시설 정보와 위경도, 인근 대중교통 |
| `chat_logs` | 챗봇 대화 로그 |

## 그 밖의 스크립트

전부 `FitBuddy` 디렉터리 안에서 실행합니다.

```bash
python app.py                 # PC 카메라로 자세 인식 + DB 기록 (S: 세션 시작/종료, Q: 종료)
python monitor_db.py          # DB 적재 상황 실시간 모니터링
python -m FitBuddy.user_manager create --email a@b.com --name 홍길동 \
    --password pw --password-confirm pw      # 저장소 루트에서 실행
```

자세 분류 모델 학습 파이프라인도 함께 들어 있습니다. `extract_from_images.py`(이미지 → 피처) → `features_agg.py`(rep 단위 집계) → `train_baseline.py`(RandomForest 학습) → `score_live.py`(실시간 채점). 운동 종류와 임계값은 [`config.py`](FitBuddy/config.py)에 정의돼 있습니다.

## 알려진 제약

- **인증이 구현돼 있지 않습니다.** [`Chatbot_main/auth.py`](FitBuddy/Chatbot_main/auth.py)의 `get_current_user`는 토큰과 무관하게 항상 `user_id=1`을 반환합니다. 따라서 챗봇 대화 로그가 전부 1번 사용자에게 쌓입니다.
- 비밀번호를 **솔트 없는 SHA-256**으로 저장합니다. 레인보우 테이블에 취약하므로 실제 서비스에는 bcrypt/argon2를 써야 합니다.
- DB 접속 정보가 소스에 하드코딩돼 있습니다.
- CORS가 `allow_origins=["*"]`로 열려 있습니다.
- `/pose/analyze`는 요청마다 `PoseDetector`를 새로 만듭니다. 프레임을 자주 보내면 병목이 됩니다.
- LLM을 `float16`으로 고정 로딩합니다. CUDA가 없는 환경에서는 CPU가 fp16을 에뮬레이션하므로 fp32보다 오히려 느릴 수 있습니다.
