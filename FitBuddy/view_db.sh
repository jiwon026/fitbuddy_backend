#!/bin/bash
# PostgreSQL 데이터베이스 확인 스크립트

echo "=========================================="
echo "FitBuddy 데이터베이스 확인"
echo "=========================================="
echo ""

DB_NAME="fitbuddy_db"

echo "1. 데이터베이스 목록 (fitbuddy 관련):"
psql -d postgres -c "SELECT datname FROM pg_database WHERE datname LIKE '%fitbuddy%';" 2>&1
echo ""

echo "2. 테이블 목록:"
psql -d $DB_NAME -c "\dt" 2>&1
echo ""

echo "3. users 테이블 구조:"
psql -d $DB_NAME -c "\d users" 2>&1
echo ""

echo "4. users 테이블 데이터 (최대 10개):"
psql -d $DB_NAME -c "SELECT user_id, email, name, created_at FROM users LIMIT 10;" 2>&1
echo ""

echo "5. users 테이블 총 개수:"
psql -d $DB_NAME -c "SELECT COUNT(*) as total_users FROM users;" 2>&1
echo ""

echo "6. workouts 테이블 데이터 (최대 10개):"
psql -d $DB_NAME -c "SELECT workout_id, user_id, workout_type, started_at FROM workouts LIMIT 10;" 2>&1
echo ""

echo "=========================================="
echo "직접 접속하려면:"
echo "  psql -d fitbuddy_db"
echo ""
echo "접속 후 유용한 명령어:"
echo "  \\dt          - 테이블 목록"
echo "  \\d users     - users 테이블 구조"
echo "  SELECT * FROM users;  - users 데이터 조회"
echo "  \\q           - 종료"
echo "=========================================="

