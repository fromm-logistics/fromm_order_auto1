# logistics_simulator.py
import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

SPREADSHEET_ID = "1QhlS0l83RwfE1xqiqaGGC_31hYN2_f6LleCFH2xw5Fg"
SHEET_NAME = "원본 업로드"

# 열 이름 (CSV 헤더 기준)
CANCEL_COL = '배송진행여부'   # AC열
KEEP_COLS_ORDERED = ['주문일시', '주문번호', '재고명', '수량', '국가코드']  # B, C, V, W, M
# 열 이름이 없을 때 사용할 0-based 인덱스
KEEP_IDX = {
    '주문일시': 1,   # B
    '주문번호': 2,   # C
    '국가코드': 12,  # M
    '재고명':   21,  # V
    '수량':     22,  # W
}
CANCEL_IDX = 28  # AC


def _get_gspread_client():
    creds = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=[
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
        ],
    )
    return gspread.authorize(creds)


def run_logistics_simulator():
    st.button(
        "⬅️ 메인 메뉴로 돌아가기",
        on_click=lambda: st.session_state.update(page="main"),
        key="back_to_main_from_logistics",
    )
    st.title("📊 물류비 시뮬레이터")

    # ── STEP 1: CSV 업로드 ──────────────────────────────
    st.markdown("### 1단계: CSV 파일 업로드")
    uploaded = st.file_uploader("CSV 파일을 업로드하세요", type=["csv"])
    if uploaded is None:
        return

    try:
        try:
            df = pd.read_csv(uploaded, encoding="utf-8-sig", dtype=str)
        except Exception:
            uploaded.seek(0)
            df = pd.read_csv(uploaded, encoding="cp949", dtype=str)

        df.columns = df.columns.astype(str).str.strip()
        st.success(f"📂 {uploaded.name} 업로드 완료: {df.shape[0]}행")

    except Exception as e:
        st.error(f"❌ 파일 읽기 오류: {e}")
        return

    # ── STEP 2: cancelled 행 제거 ──────────────────────
    if CANCEL_COL in df.columns:
        cancel_series = df[CANCEL_COL]
    elif len(df.columns) > CANCEL_IDX:
        cancel_series = df.iloc[:, CANCEL_IDX]
    else:
        cancel_series = None

    if cancel_series is not None:
        before = len(df)
        df = df[cancel_series.astype(str).str.strip().str.lower() != "cancelled"]
        removed = before - len(df)
        if removed > 0:
            st.info(f"🗑️ cancelled 행 {removed}개 제거됨 → 남은 행: {len(df)}")

    # ── STEP 3: 열 5개만 남기기 ────────────────────────
    selected = []
    for col_name, idx in KEEP_IDX.items():
        if col_name in df.columns:
            selected.append((col_name, col_name))
        elif len(df.columns) > idx:
            selected.append((df.columns[idx], col_name))

    if len(selected) < 5:
        st.error(f"❌ 필요한 열을 찾을 수 없습니다. 현재 열 목록: {list(df.columns)}")
        return

    orig_names = [s[0] for s in selected]
    new_names  = [s[1] for s in selected]
    df = df[orig_names].copy()
    df.columns = new_names

    # 사용자 지정 순서로 재배열
    df = df[[c for c in KEEP_COLS_ORDERED if c in df.columns]]

    st.markdown("### 미리보기 (상위 10행)")
    st.dataframe(df.head(10), use_container_width=True)
    st.write(f"총 **{len(df)}행** / **{len(df.columns)}열**")

    # ── STEP 4: Google Sheets 업로드 ───────────────────
    st.write("---")
    st.markdown("### 2단계: Google Sheets '원본 업로드' 시트에 붙여넣기")

    col1, col2 = st.columns(2)
    with col1:
        upload_clicked = st.button("📤 Google Sheets에 업로드", use_container_width=True)
    with col2:
        st.link_button("🔗 시트 열기", "https://docs.google.com/spreadsheets/d/1QhlS0l83RwfE1xqiqaGGC_31hYN2_f6LleCFH2xw5Fg/edit?gid=700911321#gid=700911321", use_container_width=True)

    if upload_clicked:
        with st.spinner("업로드 중..."):
            try:
                gc = _get_gspread_client()
                sh = gc.open_by_key(SPREADSHEET_ID)
                ws = sh.worksheet(SHEET_NAME)

                # 기존 데이터 클리어 (2행부터)
                last_col = "E"  # 5개 열 A~E
                ws.batch_clear([f"A2:{last_col}100000"])

                # 데이터 업로드 (2행부터)
                values = df.fillna("").values.tolist()
                ws.update(f"A2", values)

                st.success(f"✅ {len(df)}행 업로드 완료!")

            except KeyError:
                st.error(
                    "❌ Streamlit secrets에 'gcp_service_account' 키가 없습니다.\n"
                    "아래 설정 방법을 참고해주세요."
                )
            except gspread.exceptions.SpreadsheetNotFound:
                st.error("❌ 스프레드시트를 찾을 수 없습니다. 서비스 계정에 공유 권한이 있는지 확인하세요.")
            except Exception as e:
                st.error(f"❌ 업로드 실패: {e}")

    # ── 설정 안내 ───────────────────────────────────────
    with st.expander("⚙️ Google Sheets 연동 설정 방법"):
        st.markdown("""
1. [Google Cloud Console](https://console.cloud.google.com/)에서 **서비스 계정** 생성
2. **Google Sheets API** 및 **Google Drive API** 활성화
3. 서비스 계정 → **키 추가 → JSON 다운로드**
4. Streamlit Cloud → 앱 설정 → **Secrets**에 아래 형식으로 입력:

```toml
[gcp_service_account]
type = "service_account"
project_id = "your-project-id"
private_key_id = "..."
private_key = "-----BEGIN RSA PRIVATE KEY-----\\n...\\n-----END RSA PRIVATE KEY-----\\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
```

5. 위 스프레드시트를 서비스 계정 이메일에 **편집자** 권한으로 공유
        """)
