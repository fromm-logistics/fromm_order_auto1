# logistics_simulator.py
import streamlit as st
import pandas as pd

SPREADSHEET_ID = "1QhlS0l83RwfE1xqiqaGGC_31hYN2_f6LleCFH2xw5Fg"
SHEET_NAME = "원본 업로드"

# 열 이름 (CSV 헤더 기준)
CANCEL_COL = '배송진행여부'   # AC열
KEEP_COLS_ORDERED = ['주문일시', '주문번호', '재고명', '수량', '상품무게', '결제통화', '국가코드']  # B, C, V, W, Z, V, M
# 열 이름이 없을 때 사용할 0-based 인덱스
KEEP_IDX = {
    '주문일시': 1,   # B
    '주문번호': 2,   # C
    '국가코드': 12,  # M
    '재고명':   21,  # V
    '수량':     22,  # W
    '상품무게': 25,  # Z
    '결제통화': 24,  # Y
}
CANCEL_IDX = 28  # AC


def _get_gspread_client():
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

    if len(selected) < 7:
        st.error(f"❌ 필요한 열을 찾을 수 없습니다. 현재 열 목록: {list(df.columns)}")
        return

    orig_names = [s[0] for s in selected]
    new_names  = [s[1] for s in selected]
    df = df[orig_names].copy()
    df.columns = new_names

    # 사용자 지정 순서로 재배열
    df = df[[c for c in KEEP_COLS_ORDERED if c in df.columns]]

    # ── STEP 3.5: 중복 행 합치기 (수량 합산, 상품무게 유지) ──
    group_cols = [c for c in ['주문일시', '주문번호', '재고명', '국가코드', '상품무게'] if c in df.columns]
    if group_cols and '수량' in df.columns:
        df['수량'] = pd.to_numeric(df['수량'], errors='coerce').fillna(0)
        before = len(df)
        df = df.groupby(group_cols, as_index=False)['수량'].sum()
        merged = before - len(df)
        if merged > 0:
            st.info(f"🔀 중복 행 {merged}개 합산됨 → 남은 행: {len(df)}")
        # 열 순서 복원
        df = df[[c for c in KEEP_COLS_ORDERED if c in df.columns]]

    # ── STEP 3.7: 삭제할 행 선택 (재고명 기준) ──────────
    st.write("---")
    st.markdown("### 삭제할 행 선택")

    if '재고명' in df.columns:
        unique_items = sorted(df['재고명'].dropna().astype(str).unique().tolist())
        exclude_items = st.multiselect(
            "제외할 재고명을 선택하세요 (복수 선택 가능)",
            options=unique_items,
            default=[],
            key="logistics_exclude_items",
        )
        if exclude_items:
            before = len(df)
            df = df[~df['재고명'].astype(str).isin(exclude_items)]
            st.info(f"🗑️ {before - len(df)}행 제거됨 → 남은 행: {len(df)}")

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

                # 기존 데이터 클리어 (2행부터, 현재 시트 행 수 기준)
                df_upload = df.copy()
                if '수량' in df_upload.columns:
                    df_upload['수량'] = pd.to_numeric(df_upload['수량'], errors='coerce').fillna(0).astype(int)
                values = df_upload.fillna("").values.tolist()
                existing_rows = ws.row_count
                if existing_rows > 1:
                    ws.batch_clear([f"A2:G{existing_rows}"])

                # 데이터 업로드 (2행부터)
                ws.update(range_name="A2", values=values)

                st.success(f"✅ {len(df)}행 업로드 완료!")

            except KeyError:
                st.error("❌ Streamlit secrets에 'gcp_service_account' 키가 없습니다.")
            except Exception as e:
                if "SpreadsheetNotFound" in type(e).__name__:
                    st.error("❌ 스프레드시트를 찾을 수 없습니다. 서비스 계정에 공유 권한이 있는지 확인하세요.")
                else:
                    st.error(f"❌ 업로드 실패: {e}")
