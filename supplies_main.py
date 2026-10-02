# supplies_main.py  —  부자재 발주 관리 대시보드
import streamlit as st
import pandas as pd
import io
import re

# ──────────────────────────────────────────────────────────────
# 유틸
# ──────────────────────────────────────────────────────────────

def _s(val):
    """NaN-safe 문자열 변환"""
    v = str(val).strip()
    return '' if v.lower() == 'nan' else v

def _n(val):
    """NaN-safe 숫자 변환"""
    try:
        return float(str(val).replace(',', '').strip())
    except Exception:
        return 0.0

def _date(val):
    """안전한 날짜 파싱 → YYYY-MM-DD"""
    try:
        return pd.to_datetime(str(val)).strftime('%Y-%m-%d')
    except Exception:
        return ''

def _company_from_filename(filename):
    """파일명 첫 '_' 앞을 업체명으로 사용"""
    base = filename
    for ext in ['.xlsx', '.xls']:
        base = base.replace(ext, '')
    return base.split('_')[0]


# ──────────────────────────────────────────────────────────────
# WONDERWALL 포맷 파서  (씨에스팩·하보크 등)
# ──────────────────────────────────────────────────────────────

def _parse_wonderwall(df, filename):
    nrows, ncols = df.shape

    def g(r, c):
        return _s(df.iat[r, c]) if r < nrows and c < ncols else ''

    def gn(r, c):
        return _n(df.iat[r, c]) if r < nrows and c < ncols else 0.0

    company     = g(4, 8) or _company_from_filename(filename)
    order_no    = g(11, 3)
    order_date  = _date(g(11, 9))
    manager     = g(12, 3)
    destination = g(13, 3)

    # 헤더 행 탐색  (col 1 == 'CODE')
    header_row = None
    for i in range(nrows):
        if g(i, 1) == 'CODE':
            header_row = i
            break
    if header_row is None:
        return []

    STOP_WORDS = ('합계', '소계', '부가가치세', 'total', 'subtotal', 'vat', 'v.a.t')
    items = []
    for i in range(header_row + 1, nrows):
        name = g(i, 1)
        if not name:
            continue
        if '\n' in name:                              # 비고·요청사항 행
            continue
        if any(k in name.lower() for k in STOP_WORDS):
            break

        size       = g(i, 3)
        unit_price = int(gn(i, 8))
        quantity   = int(gn(i, 9))
        supply_amt = int(gn(i, 10))
        vat        = int(gn(i, 11))

        items.append({
            '발주일자':   order_date,
            '업체':       company,
            '발주번호':   order_no,
            '입고처':     destination,
            '담당자':     manager,
            '품명':       name,
            '규격':       size,
            '단가':       unit_price,
            '수량':       quantity,
            '공급가액':   supply_amt,
            '부가세':     vat,
            'VAT포함금액': supply_amt + vat,
            '파일명':     filename,
        })

    return items


# ──────────────────────────────────────────────────────────────
# 범에어캡 포맷 파서  (발주서 시트)
# ──────────────────────────────────────────────────────────────

def _parse_bum_aircap(df, filename):
    nrows, ncols = df.shape

    def g(r, c):
        return _s(df.iat[r, c]) if r < nrows and c < ncols else ''

    def gn(r, c):
        return _n(df.iat[r, c]) if r < nrows and c < ncols else 0.0

    company    = _company_from_filename(filename)
    order_date = _date(g(8, 3))
    manager    = g(10, 3)

    # 배송지 동적 탐색
    destination = ''
    for i in range(nrows):
        v = g(i, 0)
        if '배송지' in v or '입고처' in v:
            destination = g(i, 3)
            break

    # 헤더 행 탐색  (col 0 == 'No')
    header_row = None
    for i in range(nrows):
        if g(i, 0) == 'No':
            header_row = i
            break
    if header_row is None:
        return []

    items = []
    for i in range(header_row + 1, nrows):
        no = g(i, 0)
        if not re.match(r'^\d+$', no):   # 번호가 없으면 집계행 또는 끝
            break

        name       = g(i, 1)
        thickness  = g(i, 4)
        size_raw   = g(i, 5)
        size       = f"{thickness} / {size_raw}" if thickness else size_raw
        quantity   = int(gn(i, 6))
        unit_price = int(gn(i, 8))
        supply_amt = int(gn(i, 9))
        vat        = round(supply_amt * 0.1)

        items.append({
            '발주일자':   order_date,
            '업체':       company,
            '발주번호':   '',
            '입고처':     destination,
            '담당자':     manager,
            '품명':       name,
            '규격':       size,
            '단가':       unit_price,
            '수량':       quantity,
            '공급가액':   supply_amt,
            '부가세':     vat,
            'VAT포함금액': supply_amt + vat,
            '파일명':     filename,
        })

    return items


# ──────────────────────────────────────────────────────────────
# 파일 파싱 진입점
# ──────────────────────────────────────────────────────────────

def parse_order_file(file_bytes, filename):
    """Excel 발주서를 자동 감지하여 파싱. (rows, error_str) 반환"""
    try:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
    except Exception as e:
        return [], str(e)

    all_items = []
    error = None

    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(
                io.BytesIO(file_bytes), sheet_name=sheet,
                header=None, dtype=str
            )
            if sheet.upper() == 'WONDERWALL':
                items = _parse_wonderwall(df, filename)
            else:
                items = _parse_bum_aircap(df, filename)
            all_items.extend(items)
        except Exception as e:
            error = f"{sheet}: {e}"

    return all_items, error


# ──────────────────────────────────────────────────────────────
# 메인 UI
# ──────────────────────────────────────────────────────────────

_DISPLAY_COLS = [
    '발주일자', '업체', '발주번호', '입고처',
    '품명', '규격', '단가', '수량', '공급가액', '부가세', 'VAT포함금액',
]

def run_supplies_main():
    st.button("◀ 이전으로 돌아가기",
              on_click=lambda: st.session_state.update(page='main'))
    st.title("📦 부자재 관리")

    # ── 파일 업로드 ──────────────────────────────────────────
    uploaded_files = st.file_uploader(
        "발주서 Excel 파일 업로드 (여러 파일 동시 업로드 가능)",
        type=['xlsx'],
        accept_multiple_files=True,
        key='supplies_uploader',
    )

    col_clr, _ = st.columns([1, 5])
    with col_clr:
        if st.button("🗑️ 데이터 초기화"):
            st.session_state.pop('supplies_df', None)
            st.session_state.pop('supplies_sources', None)
            st.rerun()

    if uploaded_files:
        rows = []
        errors = []
        seen = set()

        for uf in uploaded_files:
            if uf.name in seen:
                continue
            seen.add(uf.name)
            items, err = parse_order_file(uf.read(), uf.name)
            rows.extend(items)
            if err:
                errors.append(f"{uf.name}: {err}")

        for e in errors:
            st.warning(f"⚠️ {e}")

        if rows:
            st.session_state['supplies_df'] = pd.DataFrame(rows)
            st.session_state['supplies_sources'] = list(seen)
        else:
            st.error("❌ 파싱된 데이터가 없습니다. 파일 형식을 확인하세요.")

    # ── 데이터 없으면 안내 ────────────────────────────────────
    if 'supplies_df' not in st.session_state or st.session_state['supplies_df'].empty:
        st.info("📂 발주서 파일을 업로드하면 대시보드가 표시됩니다.")
        return

    df = st.session_state['supplies_df'].copy()

    # ── 요약 지표 ────────────────────────────────────────────
    st.markdown("---")

    df_ord = df[df['수량'] > 0]   # 실제 발주된 행만 집계

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📋 로드된 파일",    f"{df['파일명'].nunique()}건")
    m2.metric("🏢 업체 수",        f"{df['업체'].nunique()}개")
    m3.metric("💰 공급가액 합계",  f"₩{df_ord['공급가액'].sum():,.0f}")
    m4.metric("💳 VAT포함 합계",   f"₩{df_ord['VAT포함금액'].sum():,.0f}")

    # ── 필터 ─────────────────────────────────────────────────
    st.markdown("---")
    f1, f2, f3 = st.columns([2, 2, 3])

    with f1:
        company_options = ['전체'] + sorted(df['업체'].dropna().unique().tolist())
        sel_company = st.selectbox("업체", company_options)

    with f2:
        show_zero = st.checkbox("수량 0 행 포함", value=False)

    with f3:
        search_item = st.text_input("품명 검색", placeholder="예: 에어캡, 박스")

    # 필터 적용
    filt = df.copy()
    if sel_company != '전체':
        filt = filt[filt['업체'] == sel_company]
    if not show_zero:
        filt = filt[filt['수량'] > 0]
    if search_item.strip():
        filt = filt[filt['품명'].str.contains(search_item.strip(), na=False, case=False)]

    # ── 발주 내역 테이블 ─────────────────────────────────────
    st.subheader(f"발주 내역 ({len(filt)}건)")

    if filt.empty:
        st.info("조건에 맞는 발주 내역이 없습니다.")
    else:
        st.dataframe(
            filt[_DISPLAY_COLS].reset_index(drop=True),
            use_container_width=True,
            hide_index=True,
            column_config={
                '단가':       st.column_config.NumberColumn(format="₩%d"),
                '수량':       st.column_config.NumberColumn(format="%d"),
                '공급가액':   st.column_config.NumberColumn(format="₩%d"),
                '부가세':     st.column_config.NumberColumn(format="₩%d"),
                'VAT포함금액': st.column_config.NumberColumn(format="₩%d"),
            },
        )

        # CSV 다운로드
        csv_bytes = (
            filt[_DISPLAY_COLS]
            .to_csv(index=False, encoding='utf-8-sig')
            .encode('utf-8-sig')
        )
        st.download_button(
            "⬇️ CSV 다운로드", csv_bytes,
            "부자재_발주내역.csv", "text/csv",
        )

    # ── 차트 ─────────────────────────────────────────────────
    df_chart = filt[filt['수량'] > 0]
    if not df_chart.empty:
        st.markdown("---")
        c1, c2 = st.columns(2)

        with c1:
            st.subheader("업체별 공급가액")
            by_company = (
                df_chart.groupby('업체')['공급가액']
                .sum()
                .sort_values(ascending=False)
            )
            st.bar_chart(by_company)

        with c2:
            st.subheader("품목별 공급가액 (상위 10)")
            by_item = (
                df_chart.groupby('품명')['공급가액']
                .sum()
                .sort_values(ascending=False)
                .head(10)
            )
            st.bar_chart(by_item)

        # 업체별 소계 요약
        st.markdown("---")
        st.subheader("업체별 소계")
        summary = (
            df_chart.groupby('업체')
            .agg(
                발주일자=('발주일자', lambda x: ', '.join(sorted(x.unique()))),
                품목수=('품명', 'nunique'),
                총수량=('수량', 'sum'),
                공급가액합계=('공급가액', 'sum'),
                부가세합계=('부가세', 'sum'),
                VAT포함합계=('VAT포함금액', 'sum'),
            )
            .reset_index()
        )
        st.dataframe(
            summary,
            use_container_width=True,
            hide_index=True,
            column_config={
                '공급가액합계':  st.column_config.NumberColumn(format="₩%d"),
                '부가세합계':    st.column_config.NumberColumn(format="₩%d"),
                'VAT포함합계':   st.column_config.NumberColumn(format="₩%d"),
            },
        )
