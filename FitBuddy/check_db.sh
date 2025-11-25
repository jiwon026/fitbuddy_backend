#!/bin/bash
# PostgreSQL 데이터베이스 확인 스크립트

echo "=========================================="
echo "FitBuddy 데이터베이스 확인"
echo "=========================================="
echo ""

# 데이터베이스 접속 정보
DB_NAME="fitbuddy_db"
DB_USER="fitbuddy_user"
DB_HOST="localhost"

echo "1. 데이터베이스 목록 확인:"
psql -U $DB_USER -h $DB_HOST -d postgres -c "\l" 2>/dev/null || echo "접속 실패: 데이터베이스가 존재하지 않거나 권한이 없습니다."
echo ""

echo "2. fitbuddy_db 데이터베이스의 테이블 목록:"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "\dt" 2>/dev/null || echo "접속 실패"
echo ""

echo "3. users 테이블 구조:"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "\d users" 2>/dev/null || echo "테이블이 존재하지 않습니다."
echo ""

echo "4. users 테이블 데이터 확인 (최대 10개):"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "SELECT * FROM users LIMIT 10;" 2>/dev/null || echo "데이터가 없거나 테이블이 존재하지 않습니다."
echo ""

echo "5. workouts 테이블 데이터 확인 (최대 10개):"
psql -U $DB_USER -h $DB_HOST -d $DB_NAME -c "SELECT * FROM workouts LIMIT 10;" 2>/dev/null || echo "데이터가 없거나 테이블이 존재하지 않습니다."
echo ""

echo "=========================================="
echo "완료!"
echo ""
echo "직접 접속하려면:"
echo "  psql -U fitbuddy_user -h localhost -d fitbuddy_db"
echo "=========================================="

