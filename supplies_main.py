# supplies_main.py  —  부자재 발주 관리 대시보드
import streamlit as st
import pandas as pd
import io, json, os, re

# ──────────────────────────────────────────────────────────────
# 저장 경로
# ──────────────────────────────────────────────────────────────

_DIR      = os.path.dirname(os.path.abspath(__file__))
SAVE_FILE = os.path.join(_DIR, 'supplies_data.json')

# ──────────────────────────────────────────────────────────────
# 파싱 유틸
# ──────────────────────────────────────────────────────────────

def _s(val):
    v = str(val).strip()
    return '' if v.lower() == 'nan' else v

def _n(val):
    s = str(val).strip()
    if not s or s.lower() == 'nan':
        return 0.0
    try:
        return float(s.replace(',', ''))
    except Exception:
        return 0.0

def _date(val):
    try:
        return pd.to_datetime(str(val)).strftime('%Y-%m-%d')
    except Exception:
        return ''

def _company_from_filename(filename):
    base = filename
    for ext in ['.xlsx', '.xls']:
        base = base.replace(ext, '')
    return base.split('_')[0]

def _enhance_item_name(품명, 규격):
    """에어캡 류 품목: 사이즈를 품목명에 포함해 구별
    규격 = '0.04 / 15*15+5'  →  size = '15*15+5'
    규격 = '10*20+5'          →  size = '10*20+5'
    """
    if '에어캡' not in 품명:
        return 품명
    size = 규격.split(' / ')[-1].strip() if 규격 else ''
    return f"{품명} {size}" if size else 품명

# ──────────────────────────────────────────────────────────────
# WONDERWALL 포맷 파서  (씨에스팩·하보크 등)
# ──────────────────────────────────────────────────────────────

def _parse_wonderwall(df, filename):
    nrows, ncols = df.shape
    def g(r, c):  return _s(df.iat[r, c])  if r < nrows and c < ncols else ''
    def gn(r, c): return _n(df.iat[r, c])  if r < nrows and c < ncols else 0.0

    company     = g(4, 8) or _company_from_filename(filename)
    order_no    = g(11, 3)
    order_date  = _date(g(11, 9))
    manager     = g(12, 3)
    destination = g(13, 3)

    header_row = None
    for i in range(nrows):
        if g(i, 1) == 'CODE':
            header_row = i; break
    if header_row is None:
        return []

    STOP = ('합계', '소계', '부가가치세', 'total', 'subtotal', 'vat', 'v.a.t')
    items = []
    for i in range(header_row + 1, nrows):
        name = g(i, 1)
        if not name: continue
        if '\n' in name: continue
        if any(k in name.lower() for k in STOP): break

        규격 = g(i, 3)
        supply_amt = int(gn(i, 10))
        vat        = int(gn(i, 11))
        items.append({
            '발주일자':    order_date,
            '업체':        company,
            '발주번호':    order_no,
            '입고처':      destination,
            '담당자':      manager,
            '품명':        _enhance_item_name(name, 규격),
            '규격':        규격,
            '단가':        int(gn(i, 8)),
            '수량':        int(gn(i, 9)),
            '공급가액':    supply_amt,
            '부가세':      vat,
            'VAT포함금액': supply_amt + vat,
            '파일명':      filename,
        })
    return items

# ──────────────────────────────────────────────────────────────
# 범에어캡 포맷 파서
# ──────────────────────────────────────────────────────────────

def _parse_bum_aircap(df, filename):
    nrows, ncols = df.shape
    def g(r, c):  return _s(df.iat[r, c])  if r < nrows and c < ncols else ''
    def gn(r, c): return _n(df.iat[r, c])  if r < nrows and c < ncols else 0.0

    company = _company_from_filename(filename)

    # 발주일자: col 0에 '발주일자' 포함된 행 동적 탐색
    order_date = ''
    for i in range(nrows):
        if '발주일자' in g(i, 0):
            order_date = _date(g(i, 3)); break

    # 담당자: col 0에 '담당자 :' 포함된 행
    manager = ''
    for i in range(nrows):
        c0 = g(i, 0)
        if '담당자' in c0 and ':' in c0:
            manager = g(i, 3); break

    # 배송지: 패턴 A (col 0 = "배송지", col 3 = 주소)
    #         패턴 B (어느 셀이든 "배송지: 주소..." 내장)
    destination = ''
    for i in range(nrows):
        for j in range(ncols):
            cell = g(i, j)
            if '배송지' not in cell:
                continue
            m = re.search(r'배송지\s*:?\s*([^\n:]+)', cell)
            addr = m.group(1).strip() if m else ''
            if addr and len(addr) > 4 and not re.match(r'^[\s:]*$', addr):
                destination = addr
            else:
                destination = g(i, 3) or (g(i, j + 1) if j + 1 < ncols else '')
            break
        if destination:
            break

    # 헤더 행: col 0 == 'No'
    header_row = None
    for i in range(nrows):
        if g(i, 0) == 'No':
            header_row = i; break
    if header_row is None:
        return []

    items = []
    for i in range(header_row + 1, nrows):
        no = g(i, 0)
        if not re.match(r'^\d+$', no): break

        규격 = f"{g(i,4)} / {g(i,5)}" if g(i, 4) else g(i, 5)
        supply_amt = int(gn(i, 9))
        vat        = round(supply_amt * 0.1)
        items.append({
            '발주일자':    order_date,
            '업체':        company,
            '발주번호':    '',
            '입고처':      destination,
            '담당자':      manager,
            '품명':        _enhance_item_name(g(i, 1), 규격),
            '규격':        규격,
            '단가':        int(gn(i, 8)),
            '수량':        int(gn(i, 6)),
            '공급가액':    supply_amt,
            '부가세':      vat,
            'VAT포함금액': supply_amt + vat,
            '파일명':      filename,
        })
    return items

# ──────────────────────────────────────────────────────────────
# 파일 파싱 진입점
# ──────────────────────────────────────────────────────────────

def parse_order_file(file_bytes, filename):
    try:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
    except Exception as e:
        return [], str(e)

    all_items, error = [], None
    for sheet in xl.sheet_names:
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), sheet_name=sheet,
                               header=None, dtype=str)
            items = _parse_wonderwall(df, filename) if sheet.upper() == 'WONDERWALL' \
                    else _parse_bum_aircap(df, filename)
            all_items.extend(items)
        except Exception as e:
            error = f"{sheet}: {e}"
    return all_items, error

# ──────────────────────────────────────────────────────────────
# 영속 저장 / 로드
# ──────────────────────────────────────────────────────────────

def _load_saved():
    if not os.path.exists(SAVE_FILE):
        return pd.DataFrame()
    try:
        with open(SAVE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return pd.DataFrame(data) if data else pd.DataFrame()
    except Exception:
        return pd.DataFrame()

def _save_data(df):
    with open(SAVE_FILE, 'w', encoding='utf-8') as f:
        json.dump(df.to_dict(orient='records'), f,
                  ensure_ascii=False, indent=2, default=str)

def _delete_saved_file(saved_df, filename):
    """저장 데이터에서 특정 파일명 제거 후 저장"""
    new_df = saved_df[saved_df['파일명'] != filename].reset_index(drop=True)
    if new_df.empty:
        if os.path.exists(SAVE_FILE):
            os.remove(SAVE_FILE)
    else:
        _save_data(new_df)
    return new_df

# ──────────────────────────────────────────────────────────────
# 데이터 병합 + 날짜 정렬
# ──────────────────────────────────────────────────────────────

def _merge_and_sort(*dfs):
    parts = [d for d in dfs if d is not None and not d.empty]
    if not parts:
        return pd.DataFrame()
    combined = pd.concat(parts, ignore_index=True)
    combined = combined.drop_duplicates(subset=['파일명', '품명', '규격', '발주일자'])
    combined = combined.sort_values('발주일자', ascending=True).reset_index(drop=True)
    return combined

# ──────────────────────────────────────────────────────────────
# 표시용 포맷 (천단위 쉼표)
# ──────────────────────────────────────────────────────────────

_DISPLAY_COLS  = ['발주일자', '업체', '발주번호', '입고처',
                  '품명', '규격', '단가', '수량', '공급가액', '부가세', 'VAT포함금액']
_CURRENCY_COLS = ['단가', '공급가액', '부가세', 'VAT포함금액']

def _fmt_c(x):
    try: return f"₩{int(x):,}"
    except: return str(x)

def _fmt_n(x):
    try: return f"{int(x):,}"
    except: return str(x)

def _display_df(df):
    out = df[_DISPLAY_COLS].copy().reset_index(drop=True)
    for col in _CURRENCY_COLS:
        out[col] = out[col].apply(_fmt_c)
    out['수량'] = out['수량'].apply(_fmt_n)
    return out

# ──────────────────────────────────────────────────────────────
# 메인 UI
# ──────────────────────────────────────────────────────────────

def run_supplies_main():
    st.button("◀ 이전으로 돌아가기",
              on_click=lambda: st.session_state.update(page='main'))
    st.title("📦 부자재 관리")

    # 저장된 데이터 로드 (세션 초기화 시 한 번만)
    if 'supplies_saved_df' not in st.session_state:
        st.session_state['supplies_saved_df'] = _load_saved()

    saved_df = st.session_state.get('supplies_saved_df', pd.DataFrame())
    new_df   = st.session_state.get('supplies_new_df',   pd.DataFrame())
    all_df   = _merge_and_sort(saved_df, new_df)

    tab1, tab2 = st.tabs(["📁 파일 관리", "📊 대시보드 보기"])

    # ══════════════════════════════════════════════════════════
    # TAB 1: 파일 관리
    # ══════════════════════════════════════════════════════════
    with tab1:

        uploaded_files = st.file_uploader(
            "발주서 Excel 파일 업로드 (여러 파일 동시 업로드 가능)",
            type=['xlsx'],
            accept_multiple_files=True,
            key='supplies_uploader',
        )

        # 파일 집합이 바뀐 경우만 파싱
        if uploaded_files:
            uploaded_names = frozenset(uf.name for uf in uploaded_files)
            prev_names     = st.session_state.get('supplies_prev_names', frozenset())

            if uploaded_names != prev_names:
                rows, errors = [], []
                for uf in uploaded_files:
                    items, err = parse_order_file(uf.read(), uf.name)
                    rows.extend(items)
                    if err:
                        errors.append(f"{uf.name}: {err}")
                for e in errors:
                    st.warning(f"⚠️ {e}")
                if rows:
                    new_df = pd.DataFrame(rows)
                    st.session_state['supplies_new_df']     = new_df
                    st.session_state['supplies_prev_names'] = uploaded_names
                    all_df = _merge_and_sort(saved_df, new_df)
                else:
                    st.error("❌ 파싱된 데이터가 없습니다.")

        st.markdown("")

        # ── 저장 / 초기화 버튼 ──────────────────────────────
        btn_save, btn_clr, _ = st.columns([1, 1, 3])
        with btn_save:
            save_clicked = st.button("💾 저장", type="primary", disabled=all_df.empty)
        with btn_clr:
            clr_clicked  = st.button("🗑️ 전체 초기화")

        if save_clicked and not all_df.empty:
            _save_data(all_df)
            st.session_state['supplies_saved_df'] = all_df.copy()
            st.session_state.pop('supplies_new_df', None)
            st.session_state.pop('supplies_prev_names', None)
            saved_df = all_df.copy()
            new_df   = pd.DataFrame()
            st.success(f"✅ {len(all_df):,}건 저장 완료!")

        if clr_clicked:
            st.session_state['_supplies_confirm_clr'] = True

        if st.session_state.get('_supplies_confirm_clr'):
            st.warning("⚠️ 저장된 모든 데이터가 삭제됩니다. 계속하시겠습니까?")
            cc1, cc2 = st.columns([1, 1])
            with cc1:
                if st.button("✅ 확인 (삭제)", type="primary"):
                    if os.path.exists(SAVE_FILE):
                        os.remove(SAVE_FILE)
                    for k in ['supplies_saved_df', 'supplies_new_df',
                              'supplies_prev_names', '_supplies_confirm_clr']:
                        st.session_state.pop(k, None)
                    st.rerun()
            with cc2:
                if st.button("❌ 취소"):
                    st.session_state.pop('_supplies_confirm_clr', None)
                    st.rerun()

        st.markdown("---")

        # ── 파일 목록 (삭제 버튼 포함) ──────────────────────
        if all_df.empty:
            st.info("📂 발주서 파일을 업로드하거나 저장된 데이터가 없습니다.")
        else:
            saved_names = set(saved_df['파일명'].unique()) if not saved_df.empty else set()
            all_names   = sorted(all_df['파일명'].unique())

            st.subheader(f"파일 현황 ({len(all_names)}건)")

            for fn in all_names:
                is_saved = fn in saved_names
                c_info, c_del = st.columns([9, 1])
                with c_info:
                    icon   = "💾" if is_saved else "🆕"
                    status = "저장됨" if is_saved else "미저장 — 저장 버튼으로 확정"
                    st.write(f"{icon} **{fn}** — {status}")
                with c_del:
                    if is_saved:
                        if st.button("🗑️", key=f"del_{fn}", help=f"'{fn}' 저장 데이터에서 삭제"):
                            updated = _delete_saved_file(saved_df, fn)
                            st.session_state['supplies_saved_df'] = updated
                            saved_df = updated
                            all_df   = _merge_and_sort(saved_df, new_df)
                            st.rerun()

            # 신규 업로드 미리보기
            if not new_df.empty:
                st.markdown("---")
                st.subheader("신규 업로드 미리보기")
                preview = new_df[new_df['수량'] > 0].copy()
                if preview.empty:
                    st.info("신규 파일에 수량 > 0인 항목이 없습니다.")
                else:
                    st.dataframe(_display_df(preview), use_container_width=True, hide_index=True)

    # ══════════════════════════════════════════════════════════
    # TAB 2: 대시보드 보기
    # ══════════════════════════════════════════════════════════
    with tab2:

        if all_df.empty:
            st.info("📂 파일을 업로드하거나 저장된 데이터가 없습니다.")
        else:
            df     = all_df.copy()
            df_ord = df[df['수량'] > 0]

            # ── 요약 지표 ─────────────────────────────────────
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("📋 발주 파일",     f"{df['파일명'].nunique()}건")
            m2.metric("🏢 업체 수",        f"{df['업체'].nunique()}개")
            m3.metric("💰 공급가액 합계",  f"₩{df_ord['공급가액'].sum():,}")
            m4.metric("💳 VAT포함 합계",   f"₩{df_ord['VAT포함금액'].sum():,}")

            st.markdown("---")

            # ── 필터 ──────────────────────────────────────────
            f1, f2, f3 = st.columns([2, 2, 3])
            with f1:
                company_opts = ['전체'] + sorted(df['업체'].dropna().unique().tolist())
                sel_company  = st.selectbox("업체", company_opts)
            with f2:
                show_zero   = st.checkbox("수량 0 행 포함", value=False)
            with f3:
                search_item = st.text_input("품명 검색", placeholder="예: 에어캡, 박스")

            filt = df.copy()
            if sel_company != '전체':
                filt = filt[filt['업체'] == sel_company]
            if not show_zero:
                filt = filt[filt['수량'] > 0]
            if search_item.strip():
                filt = filt[filt['품명'].str.contains(search_item.strip(), na=False, case=False)]

            # ── 발주 내역 테이블 ───────────────────────────────
            st.subheader(f"발주 내역 ({len(filt):,}건)")

            if filt.empty:
                st.info("조건에 맞는 발주 내역이 없습니다.")
            else:
                st.dataframe(_display_df(filt), use_container_width=True, hide_index=True)
                csv_bytes = (
                    filt[_DISPLAY_COLS]
                    .to_csv(index=False, encoding='utf-8-sig')
                    .encode('utf-8-sig')
                )
                st.download_button("⬇️ CSV 다운로드", csv_bytes,
                                   "부자재_발주내역.csv", "text/csv")

            df_chart = filt[filt['수량'] > 0]
            if not df_chart.empty:
                st.markdown("---")

                # ── 업체별 공급가액 차트 ───────────────────────
                st.subheader("업체별 공급가액")
                by_company = (df_chart.groupby('업체')['공급가액']
                              .sum().sort_values(ascending=False))
                st.bar_chart(by_company)

                st.markdown("---")

                # ── 품목별 누적 수량 ───────────────────────────
                st.subheader("품목별 누적 수량")

                item_agg = (
                    df_chart.groupby('품명')
                    .agg(
                        발주횟수=('수량', 'count'),
                        누적수량=('수량', 'sum'),
                        최근단가=('단가', 'last'),
                        누적공급가액=('공급가액', 'sum'),
                        업체=('업체', lambda x: ' / '.join(sorted(x.unique()))),
                        기간=('발주일자', lambda x: f"{x.min()} ~ {x.max()}"
                              if x.min() != x.max() else x.min()),
                    )
                    .reset_index()
                    .sort_values('누적수량', ascending=False)
                )

                # 숫자 포맷
                item_agg['누적수량']    = item_agg['누적수량'].apply(_fmt_n)
                item_agg['최근단가']    = item_agg['최근단가'].apply(_fmt_c)
                item_agg['누적공급가액'] = item_agg['누적공급가액'].apply(_fmt_c)
                item_agg['발주횟수']    = item_agg['발주횟수'].apply(_fmt_n)

                # 열 순서 정리
                item_agg = item_agg[['품명', '업체', '기간', '발주횟수', '누적수량', '최근단가', '누적공급가액']]

                st.dataframe(item_agg, use_container_width=True, hide_index=True)
