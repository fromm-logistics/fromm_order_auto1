# weight_db.py
# 재고명 → 무게(g) 영구 저장소 (Google Sheets "재고무게DB" 시트 사용)
import streamlit as st

WEIGHT_SPREADSHEET_ID = "1QhlS0l83RwfE1xqiqaGGC_31hYN2_f6LleCFH2xw5Fg"
WEIGHT_SHEET_NAME = "재고무게DB"


def _client():
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)


def _get_or_create_sheet():
    gc = _client()
    sh = gc.open_by_key(WEIGHT_SPREADSHEET_ID)
    try:
        return sh.worksheet(WEIGHT_SHEET_NAME)
    except Exception:
        ws = sh.add_worksheet(title=WEIGHT_SHEET_NAME, rows=2000, cols=2)
        ws.update("A1:B1", [["재고명", "무게(g)"]])
        return ws


@st.cache_data(ttl=120)
def load_weights() -> dict:
    """Google Sheets에서 재고무게 DB 로드. {재고명: 무게(g)}"""
    try:
        ws = _get_or_create_sheet()
        records = ws.get_all_records()
        return {
            r["재고명"]: int(r["무게(g)"])
            for r in records
            if r.get("재고명") and str(r.get("무게(g)", "")).isdigit()
        }
    except Exception:
        return {}


def save_weight(name: str, weight: int) -> bool:
    """단일 재고명-무게 저장 또는 업데이트."""
    try:
        ws = _get_or_create_sheet()
        records = ws.get_all_records()
        names = [r["재고명"] for r in records]
        if name in names:
            ws.update_cell(names.index(name) + 2, 2, weight)
        else:
            ws.append_row([name, weight])
        load_weights.clear()
        return True
    except Exception:
        return False


def save_weights_bulk(weights: dict) -> bool:
    """여러 재고명-무게 한 번에 저장 (신규/업데이트 자동 판별)."""
    if not weights:
        return True
    try:
        ws = _get_or_create_sheet()
        records = ws.get_all_records()
        name_to_row = {r["재고명"]: i + 2 for i, r in enumerate(records)}
        for name, weight in weights.items():
            if name in name_to_row:
                ws.update_cell(name_to_row[name], 2, int(weight))
            else:
                ws.append_row([name, int(weight)])
        load_weights.clear()
        return True
    except Exception:
        return False


def delete_weight(name: str) -> bool:
    """재고명 삭제."""
    try:
        ws = _get_or_create_sheet()
        records = ws.get_all_records()
        names = [r["재고명"] for r in records]
        if name in names:
            ws.delete_rows(names.index(name) + 2)
            load_weights.clear()
            return True
        return False
    except Exception:
        return False
