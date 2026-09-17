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


def inject_floating_weight_btn(show_refresh: bool = False):
    """MD 관련 모든 페이지 우측 중앙에 구글 시트 플로팅 버튼 삽입.
    show_refresh=True 이면 새로고침 버튼을 맨 위에 함께 표시.
    플로팅 새로고침은 onclick JS로 페이지 내 실제 Streamlit 새로고침 버튼을 클릭함.
    """
    sheet_url = f"https://docs.google.com/spreadsheets/d/{WEIGHT_SPREADSHEET_ID}/"

    # CSS: <style> 블록 내부는 Markdown 코드블록 영향 없음
    refresh_css_block = ""
    refresh_item_html = ""
    if show_refresh:
        refresh_css_block = (
            ".floating-refresh-btn{"
            "display:flex;flex-direction:column;align-items:center;"
            "justify-content:center;gap:4px;width:72px;padding:10px 8px;"
            "background:rgba(255,255,255,0.10);border-radius:14px;"
            "cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,0.25);"
            "transition:background 0.15s,box-shadow 0.15s;}"
            ".floating-refresh-btn:hover{"
            "background:rgba(255,255,255,0.22);box-shadow:0 4px 16px rgba(0,0,0,0.35);}"
            ".floating-refresh-btn .fr-icon{font-size:20px;line-height:1;}"
            ".floating-refresh-btn .fr-label{"
            "font-size:10px;font-weight:600;color:#fff!important;"
            "text-align:center;line-height:1.3;word-break:keep-all;}"
        )
        # onclick: 페이지 내 '새로고침' 텍스트를 가진 버튼을 JS로 클릭
        # <a href> 대신 div+onclick 사용 — Streamlit에서 <a>는 항상 새 탭으로 열림
        js = (
            "(function(){"
            "var btns=document.querySelectorAll('button');"
            "for(var i=0;i<btns.length;i++){"
            "var t=btns[i].innerText||btns[i].textContent||'';"
            "if(t.indexOf('\\uc0c8\\ub85c\\uace0\\uce68')!==-1)"  # 새로고침
            "{btns[i].click();return;}"
            "}})()"
        )
        refresh_item_html = (
            f'<div class="floating-refresh-btn" onclick="{js}">'
            '<span class="fr-icon">🔄</span>'
            '<span class="fr-label">새로고침</span>'
            '</div>'
        )

    sheet_item_html = (
        '<div class="floating-weight-btn">'
        f'<a href="{sheet_url}" target="_blank">'
        '<span class="fw-icon">⚖️</span>'
        '<span class="fw-label">재고 무게<br>추가/수정</span>'
        '</a></div>'
    )

    # CSS는 멀티라인 OK (style 블록은 HTML 블록으로 통째 처리됨)
    # HTML div는 절대 빈 줄 없이 한 줄로 렌더링
    st.markdown(
        f"<style>"
        f".floating-weight-col{{position:fixed;right:80px;top:50%;"
        f"transform:translateY(-50%);z-index:9999;"
        f"display:flex;flex-direction:column;align-items:center;gap:8px;}}"
        f"{refresh_css_block}"
        f".floating-weight-btn a{{display:flex;flex-direction:column;"
        f"align-items:center;justify-content:center;gap:6px;width:72px;"
        f"padding:14px 8px;"
        f"background:linear-gradient(160deg,#FB4866 0%,#FB7E48 100%);"
        f"border-radius:16px;text-decoration:none!important;"
        f"box-shadow:0 4px 20px rgba(251,72,102,0.45);"
        f"transition:transform 0.15s,box-shadow 0.15s;}}"
        f".floating-weight-btn a:hover{{transform:scale(1.06);"
        f"box-shadow:0 6px 28px rgba(251,72,102,0.65);}}"
        f".floating-weight-btn .fw-icon{{font-size:22px;line-height:1;}}"
        f".floating-weight-btn .fw-label{{font-size:10px;font-weight:600;"
        f"color:#fff!important;text-align:center;line-height:1.4;word-break:keep-all;}}"
        f"</style>"
        f'<div class="floating-weight-col">'
        f"{refresh_item_html}"
        f"{sheet_item_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


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
