# load_facilities.py
import pandas as pd
from decimal import Decimal

from database import SessionLocal
from models import SportsFacility

CSV_PATH = "data/KS_ALSFC_NEARBY_PBTRNSP_INFO_202507.csv"


def main():
    # ====== CSV 읽기 ======
    try:
        df = pd.read_csv(CSV_PATH, encoding="cp949")
    except UnicodeDecodeError:
        df = pd.read_csv(CSV_PATH, encoding="utf-8-sig")

    print("총 행 개수:", len(df))
    print("컬럼:", df.columns.tolist())

    session = SessionLocal()
    inserted = 0

    try:
        for _, row in df.iterrows():
            name = str(row["ALSFC_NM"]).strip()
            if not name:
                continue

            try:
                lat = float(row["ALSFC_LA"])
                lon = float(row["ALSFC_LO"])
            except Exception:
                # 위도/경도 이상하면 스킵
                continue

            addr = str(row.get("ALSFC_ADDR", "")).strip()
            sdiv = str(row.get("ALSFC_SDIV_NM", "")).strip()
            ty   = str(row.get("ALSFC_TY_NM", "")).strip()
            ctprvn_cd  = str(row.get("ALSFC_CTPRVN_CD", "")).strip()
            ctprvn_nm  = str(row.get("ALSFC_CTPRVN_NM", "")).strip()
            signgu_cd  = str(row.get("ALSFC_SIGNGU_CD", "")).strip()
            signgu_nm  = str(row.get("ALSFC_SIGNGU_NM", "")).strip()

            fac = SportsFacility()
            fac.alsfc_nm = name
            fac.alsfc_sdiv_nm = sdiv
            fac.alsfc_ty_nm = ty
            fac.alsfc_ctprvn_cd = ctprvn_cd
            fac.alsfc_ctprvn_nm = ctprvn_nm
            fac.alsfc_signgu_cd = signgu_cd
            fac.alsfc_signgu_nm = signgu_nm
            fac.alsfc_addr = addr

            # DECIMAL 컬럼이니까 Decimal로 캐스팅
            fac.alsfc_la = Decimal(str(lat))
            fac.alsfc_lo = Decimal(str(lon))

            # geom은 당장 안 써도 되면 생략해도 OK (null 허용이면)
            # 나중에 PostGIS 쓰고 싶으면 여기서 POINT 생성해도 됨

            session.add(fac)
            inserted += 1

            if inserted % 1000 == 0:
                session.flush()
                print(f"{inserted}개 적재 중...")

        session.commit()
        print(f"DB에 최종 {inserted}개 시설 저장 완료!")

    except Exception as e:
        session.rollback()
        print("에러 발생:", e)
    finally:
        session.close()


if __name__ == "__main__":
    main()
