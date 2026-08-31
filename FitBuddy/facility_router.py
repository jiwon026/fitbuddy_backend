# facility_router.py
from typing import List, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from models import SportsFacility
from math import sin, cos, radians, atan2, sqrt

router = APIRouter(prefix="/facility", tags=["facility"])


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0  # km
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = (
        sin(dlat / 2) ** 2
        + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
    )
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c


# ---------- 요청/응답 모델 ----------
class NearbyRequest(BaseModel):
    user_lat: float
    user_lon: float
    radius_km: float = 3.0
    category: Optional[str] = None  # 지금은 안 쓰더라도 형태만 유지


class FacilityOut(BaseModel):
    name: str
    address: str
    lat: float
    lon: float
    distance_km: float

@router.post("/nearby", response_model=List[FacilityOut])
def get_nearby_facilities(req: NearbyRequest, db: Session = Depends(get_db)):
    """
    주변 운동 시설 조회 (위도/경도 범위로 먼저 필터링 후 거리 계산)
    """

    # 1) 위도/경도 범위(대략적인 박스)
    # 위도 1도 ≈ 111km
    lat_delta = req.radius_km / 111.0
    # 경도 1도 ≈ 111km * cos(lat)
    lon_delta = req.radius_km / (111.0 * max(cos(radians(req.user_lat)), 0.1))

    min_lat = req.user_lat - lat_delta
    max_lat = req.user_lat + lat_delta
    min_lon = req.user_lon - lon_delta
    max_lon = req.user_lon + lon_delta

    # 2) DB에서 bounding box 안에 있는 것만 가져오기
    q = db.query(SportsFacility).filter(
        SportsFacility.alsfc_la.between(min_lat, max_lat),
        SportsFacility.alsfc_lo.between(min_lon, max_lon),
    )

    # (선택) 너무 많으면 상한 설정
    q = q.limit(2000)

    facilities = q.all()
    print(f"[FACILITY] 후보 개수: {len(facilities)}")

    # 3) 파이썬에서 실제 거리 계산 + radius 안에 있는 것만 추리기
    results: List[FacilityOut] = []
    seen: set[tuple[str, str]] = set()
    for f in facilities:
        if f.alsfc_la is None or f.alsfc_lo is None:
            continue

        lat = float(f.alsfc_la)
        lon = float(f.alsfc_lo)

        dist = haversine(req.user_lat, req.user_lon, lat, lon)
        if dist > req.radius_km:
            continue

        results.append(
            FacilityOut(
                name=f.alsfc_nm,
                address=f.alsfc_addr or "",
                lat=lat,
                lon=lon,
                distance_km=round(dist, 2),
            )
        )

    results.sort(key=lambda x: x.distance_km)
    print(f"[FACILITY] 최종 반환 개수: {len(results)}")
    return results