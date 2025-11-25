# FitBuddy/user_manager.py
# 사용자 회원가입 및 관리 기능

import sys
from pathlib import Path
import hashlib
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from FitBuddy.database import SessionLocal
from models import User
from sqlalchemy.exc import IntegrityError

def hash_password(password: str) -> str:
    """비밀번호를 해시화"""
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email: str, name: str, password: str, password_confirm: str) -> int:
    """
    새 사용자를 생성합니다 (회원가입).
    
    Args:
        email: 이메일 (로그인용)
        name: 이름
        password: 비밀번호
        password_confirm: 비밀번호 확인
    
    Returns:
        user_id: 생성된 사용자 ID (실패 시 None)
    """
    db = SessionLocal()
    try:
        # 비밀번호 확인
        if password != password_confirm:
            print("❌ 회원가입 실패: 비밀번호가 일치하지 않습니다.")
            return None
        
        # 비밀번호 해시화
        password_hash = hash_password(password)
        
        # 사용자 생성 (회원가입 정보만)
        user = User(
            email=email,
            name=name,
            password_hash=password_hash
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        print(f"✓ 회원가입 성공! 사용자 ID: {user.user_id}")
        return user.user_id
        
    except IntegrityError:
        db.rollback()
        print(f"❌ 회원가입 실패: 이메일 '{email}'가 이미 존재합니다.")
        return None
    except Exception as e:
        db.rollback()
        print(f"❌ 회원가입 실패: {e}")
        return None
    finally:
        db.close()

def verify_user(email: str, password: str) -> int:
    """
    사용자 로그인 검증
    
    Args:
        email: 이메일
        password: 비밀번호
    
    Returns:
        user_id: 검증 성공 시 사용자 ID, 실패 시 None
    """
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        
        if user and user.password_hash == hash_password(password):
            print(f"✓ 로그인 성공! 사용자 ID: {user.user_id}, 이름: {user.name}")
            return user.user_id
        else:
            print("❌ 로그인 실패: 이메일 또는 비밀번호가 올바르지 않습니다.")
            return None
    except Exception as e:
        print(f"❌ 로그인 오류: {e}")
        return None
    finally:
        db.close()

def get_user(user_id: int):
    """사용자 정보 조회"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        return user
    finally:
        db.close()

def update_user_info(user_id: int, height_cm: int = None, weight_kg: float = None, 
                     gender: str = None, workout_goal: str = None):
    """사용자 정보 업데이트 (키, 몸무게, 성별, 운동목적)"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            print(f"❌ 사용자를 찾을 수 없습니다.")
            return False
        
        if height_cm is not None:
            user.height_cm = height_cm
        if weight_kg is not None:
            user.weight_kg = weight_kg
        if gender is not None:
            user.gender = gender
        if workout_goal is not None:
            user.workout_goal = workout_goal
        
        db.commit()
        print(f"✓ 사용자 정보가 업데이트되었습니다.")
        return True
    except Exception as e:
        db.rollback()
        print(f"❌ 업데이트 실패: {e}")
        return False
    finally:
        db.close()

def list_users():
    """모든 사용자 목록 조회"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        print("\n" + "=" * 90)
        print(f"총 {len(users)}명의 사용자")
        print("=" * 90)
        print(f"{'ID':<6} {'이름':<15} {'이메일':<25} {'키':<8} {'몸무게':<8} {'성별':<8} {'운동목적':<15}")
        print("-" * 90)
        for user in users:
            height = f"{user.height_cm}cm" if user.height_cm else "-"
            weight = f"{user.weight_kg}kg" if user.weight_kg else "-"
            gender = user.gender or "-"
            goal = user.workout_goal or "-"
            print(f"{user.user_id:<6} {user.name:<15} {user.email:<25} {height:<8} {weight:<8} {gender:<8} {goal:<15}")
        print("=" * 90)
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="사용자 관리")
    parser.add_argument("action", choices=["create", "login", "list", "update-info"], help="실행할 작업")
    parser.add_argument("--email", help="이메일")
    parser.add_argument("--name", help="이름")
    parser.add_argument("--password", help="비밀번호")
    parser.add_argument("--password-confirm", help="비밀번호 확인")
    parser.add_argument("--user-id", type=int, help="사용자 ID")
    parser.add_argument("--height", type=int, help="키 (cm)")
    parser.add_argument("--weight", type=float, help="몸무게 (kg)")
    parser.add_argument("--gender", choices=["male", "female", "other"], help="성별")
    parser.add_argument("--goal", help="운동 목적")
    
    args = parser.parse_args()
    
    if args.action == "create":
        if not args.email or not args.name or not args.password or not args.password_confirm:
            print("❌ --email, --name, --password, --password-confirm이 필요합니다.")
        else:
            create_user(args.email, args.name, args.password, args.password_confirm)
    
    elif args.action == "login":
        if not args.email or not args.password:
            print("❌ --email과 --password가 필요합니다.")
        else:
            verify_user(args.email, args.password)
    
    elif args.action == "list":
        list_users()
    
    elif args.action == "update-info":
        if not args.user_id:
            print("❌ --user-id가 필요합니다.")
        else:
            update_user_info(
                args.user_id,
                height_cm=args.height,
                weight_kg=args.weight,
                gender=args.gender,
                workout_goal=args.goal
            )

