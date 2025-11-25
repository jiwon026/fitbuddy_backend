#!/bin/bash
# 데이터베이스의 프레임 데이터를 확인하는 스크립트

echo "=========================================="
echo "📊 운동 세션 목록"
echo "=========================================="
psql -U min -d fitbuddy_db -c "SELECT workout_id, workout_type, started_at, ended_at, duration_seconds FROM workouts ORDER BY started_at DESC LIMIT 5;"

echo ""
echo "=========================================="
echo "📸 최신 프레임 데이터 (최근 10개)"
echo "=========================================="
psql -U min -d fitbuddy_db -c "SELECT workout_id, frame_number, ROUND(knee_angle::numeric, 1) as knee, ROUND(hip_angle::numeric, 1) as hip, ROUND(torso_tilt_angle::numeric, 1) as tilt FROM workout_frames ORDER BY frame_id DESC LIMIT 10;"

echo ""
echo "=========================================="
echo "📈 통계"
echo "=========================================="
psql -U min -d fitbuddy_db -c "SELECT COUNT(*) as total_frames, COUNT(DISTINCT workout_id) as total_workouts FROM workout_frames;"



