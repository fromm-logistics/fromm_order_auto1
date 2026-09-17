# weight_db.py
# 재고명 → 무게(g) 영구 저장소 (Google Sheets "재고무게DB" 시트 사용)
import streamlit as st

WEIGHT_SPREADSHEET_ID = "1bSv3pKhjUeShcaxPV68QAavKpxtA5nmyE2YgZABlTb8"
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
        # 탭이 없으면: 시트가 1개뿐이면 첫 번째 탭 사용, 아니면 새로 생성
        all_ws = sh.worksheets()
        if len(all_ws) == 1:
            return all_ws[0]
        ws = sh.add_worksheet(title=WEIGHT_SHEET_NAME, rows=2000, cols=2)
        ws.update("A1:B1", [["재고명", "무게(g)"]])
        return ws


@st.cache_data(ttl=120)
def load_weights() -> dict:
    """Google Sheets에서 재고무게 DB 로드. {재고명: 무게(g)}
    컬럼명 '무게(g)' 또는 '무게' 모두 지원.
    """
    try:
        ws = _get_or_create_sheet()
        records = ws.get_all_records()
        if not records:
            return {}
        # 첫 번째 레코드에서 무게 컬럼명 자동 감지
        sample = records[0]
        weight_col = "무게(g)" if "무게(g)" in sample else "무게"
        result = {}
        for r in records:
            name = r.get("재고명", "")
            raw_w = r.get(weight_col, "")
            if not name:
                continue
            try:
                result[name] = int(float(str(raw_w)))
            except (ValueError, TypeError):
                pass
        return result
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


def inject_floating_weight_btn():
    """MD 관련 모든 페이지 우측에 구글 시트 플로팅 버튼 삽입."""
    sheet_url = f"https://docs.google.com/spreadsheets/d/{WEIGHT_SPREADSHEET_ID}/"
    st.markdown(f"""
<style>
.floating-weight-btn {{
    position: fixed;
    right: 24px;
    top: 80px;
    z-index: 9999;
}}
.floating-weight-btn a {{
    display: block;
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.12);
    color: rgba(255,255,255,0.75) !important;
    padding: 10px 14px;
    border-radius: 10px;
    text-decoration: none !important;
    font-size: 11px;
    text-align: center;
    line-height: 1.6;
    transition: background 0.15s, border-color 0.15s;
}}
.floating-weight-btn a:hover {{
    background: rgba(200,130,170,0.10);
    border-color: rgba(200,130,170,0.35);
    color: #fff !important;
}}
</style>
<div class="floating-weight-btn">
    <a href="{sheet_url}" target="_blank">📊 상시판매 재고<br>무게 추가/제거/수정</a>
</div>
""", unsafe_allow_html=True)


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
