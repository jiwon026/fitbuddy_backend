#!/bin/bash
# FitBuddy 백엔드 서버 실행 스크립트

# 프로젝트 루트로 이동
cd "$(dirname "$0")/.."

# 가상환경 활성화
source new_venv/bin/activate

# FitBuddy 디렉토리로 이동
cd FitBuddy

# 서버 실행
echo "🚀 FitBuddy 백엔드 서버를 시작합니다..."
echo "📍 서버 주소: http://localhost:8000"
echo "📚 API 문서: http://localhost:8000/docs"
echo ""
echo "서버를 종료하려면 Ctrl+C를 누르세요."
echo ""

uvicorn backend_api:app --reload --port 8000


