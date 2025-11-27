"""
인증 관련 함수
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from typing import Optional
from Chatbot_main.database import get_db

# 임시 사용자 모델 (실제 구현 필요)
class CurrentUser:
    """현재 인증된 사용자"""
    def __init__(self, user_id: int):
        self.user_id = user_id

# OAuth2 스키마 (실제 구현 필요)
# 개발 단계에서는 Optional로 설정하여 인증을 선택적으로 만듦
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> CurrentUser:
    """
    현재 사용자 가져오기
    
    Args:
        token: OAuth2 토큰 (선택사항, 개발 단계)
        db: 데이터베이스 세션
    
    Returns:
        CurrentUser: 현재 사용자 객체
    
    TODO: 실제 토큰 검증 로직 구현 필요
    """
    # 개발 단계: 토큰이 없어도 기본 사용자 반환
    # 프로덕션에서는 토큰 검증 필수
    if token is None:
        # 개발 모드: 기본 사용자 반환
        return CurrentUser(user_id=1)
    
    # TODO: 실제 JWT 토큰 검증 및 사용자 조회
    # try:
    #     payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    #     user_id = payload.get("sub")
    #     user = db.query(User).filter(User.user_id == user_id).first()
    #     if user is None:
    #         raise HTTPException(status_code=404, detail="User not found")
    #     return CurrentUser(user_id=user.user_id)
    # except JWTError:
    #     raise HTTPException(status_code=401, detail="Invalid token")
    
    # 임시: 토큰이 있으면 user_id=1 반환
    return CurrentUser(user_id=1)


