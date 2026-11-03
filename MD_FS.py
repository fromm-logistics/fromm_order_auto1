import streamlit as st
import pandas as pd
import io, re, random
import datetime
from openpyxl import load_workbook
from openpyxl.styles import PatternFill
from weight_db import load_weights, inject_floating_weight_btn  # ← 구글 시트 무게 DB

# ───────────────────────────────────────────────────
# 1) 유저가 수정·확장 가능한 영역:
#    – 기본 target_products(재고명→무게 매핑) — 시트에 없는 경우 폴백
#    – box_limit(박스 최대 용량)
# ───────────────────────────────────────────────────
target_products = {}
box_limit = 15000  # 기본 박스 최대 용량

exclude_products = [
    # '상품명 예시',
]

def _reset_fs():
    load_weights.clear()
    for k in ['fs_df', 'fs_buf_all', 'fs_buf_dom', 'fs_buf_int']:
        st.session_state.pop(k, None)

def run_md_fs():
    inject_floating_weight_btn(show_refresh=True)

    # 뒤로가기 버튼 (표시)
    st.button("◀ MD 창으로 돌아가기",
              on_click=lambda: st.session_state.update(page="md_main"),
              key="back_to_md_main_from_fs")

    # 새로고침 버튼 — CSS로 숨김, 플로팅 버튼 JS가 이 버튼을 클릭함
    st.markdown(
        '<style>.element-container:has(#fs-refresh-anchor)+'
        '.element-container{display:none!important}</style>'
        '<div id="fs-refresh-anchor"></div>',
        unsafe_allow_html=True,
    )
    st.button("🔄 새로고침", on_click=_reset_fs, key="fs_refresh")

    # 플로팅 새로고침 → 숨겨진 Streamlit 버튼을 JS로 클릭
    import streamlit.components.v1 as components
    components.html(
        '<script>'
        '(function wire(){'
        'var doc=window.parent.document;'
        'var trigger=doc.getElementById("floating-refresh-trigger");'
        'if(trigger&&!trigger._w){'
        'trigger._w=true;'
        'trigger.addEventListener("click",function(){'
        'var btns=doc.querySelectorAll("button");'
        'for(var i=0;i<btns.length;i++){'
        'var t=btns[i].innerText||btns[i].textContent||"";'
        'if(t.indexOf("\\uc0c8\\ub85c\\uace0\\uce68")!==-1){btns[i].click();return;}'
        '}});'
        '}else if(!trigger){setTimeout(wire,200);}'
        '})()'
        '</script>',
        height=0,
        scrolling=False,
    )
    st.title("📋 FS 나누기")

    # ── 구글 시트 무게 로드 (시트 우선, 코드 내 값 폴백) ──
    _sheet_w = load_weights()
    effective_tp = {**target_products, **_sheet_w}
    if _sheet_w:
        st.caption(f"📊 구글 시트에서 **{len(_sheet_w)}개** 무게 로드됨")
    else:
        st.warning("⚠️ 구글 시트 무게 로드 실패 — 코드 내 기본값 사용 중")

    uploaded = st.file_uploader("▶ FS 전용 CSV 업로드", type="csv", key="fs_csv")
    if uploaded:
        df = pd.read_csv(uploaded, dtype={'우편번호': str, '전화번호': str})

        # 제외 상품 필터링
        if exclude_products:
            before = len(df)
            df = df[~df['재고명'].astype(str).isin(exclude_products)]
            removed = before - len(df)
            if removed > 0:
                st.info(f"🗑️ 제외 상품 {removed}행 삭제됨: {exclude_products}")

        st.session_state['fs_df'] = df
        st.success(f"CSV 업로드 완료: {df.shape[0]}행")
    else:
        df = st.session_state.get('fs_df')

    missing = []
    if df is not None:
        missing = sorted(set(df['재고명'].dropna()) - set(effective_tp))
        if missing:
            st.error(f"🚫 실행 불가 — 무게 시트에 없는 재고 **{len(missing)}개** 발견\n\n우측 버튼으로 시트에 추가 후 🔄 새로고침하세요:")
            _items = ""
            for _i, _n in enumerate(missing, 1):
                _js = _n.replace('\\', '\\\\').replace("'", "\\'")
                _items += (
                    f'<div class="mi"><span class="mn">{_i}.</span>'
                    f'<span class="mt">{_n}</span>'
                    f'<button class="cb" onclick="cp(\'{_js}\',this)">복사</button></div>'
                )
            components.html(
                '<style>'
                'body{margin:0;padding:4px 0;background:#0f1117;font-family:sans-serif;}'
                '.mi{display:flex;align-items:center;gap:10px;padding:10px 14px;'
                'background:#1c1640;border:1px solid #4a3080;border-radius:8px;margin:4px 0;}'
                '.mn{color:#a78bfa;font-size:12px;font-weight:700;min-width:22px;'
                'text-align:right;flex-shrink:0;}'
                '.mt{flex:1;font-family:monospace;font-size:13px;color:#e2d9f3;'
                'word-break:break-all;line-height:1.4;}'
                '.cb{background:rgba(251,72,102,0.12);border:1px solid rgba(251,72,102,0.45);'
                'color:#fb4866;border-radius:6px;padding:5px 12px;font-size:11px;font-weight:700;'
                'cursor:pointer;white-space:nowrap;flex-shrink:0;transition:all 0.15s;}'
                '.cb:hover{background:rgba(251,72,102,0.3);}'
                '.cb.ok{background:rgba(34,197,94,0.15);border-color:rgba(34,197,94,0.45);color:#22c55e;}'
                '</style>'
                '<script>'
                'function cp(t,b){'
                'navigator.clipboard.writeText(t).then(function(){'
                'b.textContent="✅ 복사됨";b.classList.add("ok");'
                'setTimeout(function(){b.textContent="복사";b.classList.remove("ok");},1500);'
                '});}'
                '</script>'
                + _items,
                height=len(missing) * 56 + 16,
                scrolling=False,
            )
        else:
            st.success("모든 재고명이 무게 DB에 포함됩니다.")

    # ── 특전 토글 UI (missing 없을 때만 표시) ──
    if df is not None and not missing:
        _price = pd.to_numeric(df['상품금액'], errors='coerce').fillna(0)
        product_names = sorted(df.loc[_price.isin([0, 1]), '재고명'].dropna().unique())
        saved_special = st.session_state.get("fs_special_flags_fs", {})
        new_special = {}

        st.markdown("### 🎁 특전 상품 설정")
        st.caption("특전으로 지정된 재고는 무게 계산에서 제외되며, 각 주문의 마지막 박스 번호에 포함됩니다.")

        def _fs_toggle_all():
            val = st.session_state["fs_master_toggle"]
            for p in product_names:
                st.session_state[f"fs_sp_{p}"] = val

        _, col_master_toggle = st.columns([4, 1])
        with col_master_toggle:
            st.toggle("전체 특전", key="fs_master_toggle",
                      on_change=_fs_toggle_all)
        st.markdown('<hr style="margin:4px 0;border:none;border-top:2px solid #555;">', unsafe_allow_html=True)

        for prod in product_names:
            is_special = st.session_state.get(f"fs_sp_{prod}", saved_special.get(prod, False))
            col_name, col_toggle = st.columns([4, 1])
            with col_name:
                st.markdown(f"**{prod}**")
            with col_toggle:
                is_special = st.toggle("특전", value=is_special, key=f"fs_sp_{prod}")
            new_special[prod] = is_special
            st.markdown('<hr style="margin:2px 0;border:none;border-top:1px solid #333;">', unsafe_allow_html=True)

        st.session_state["fs_special_flags_fs"] = new_special

        special_count = sum(1 for v in new_special.values() if v)
        if special_count:
            st.info(f"📌 특전 재고 {special_count}개 — 각 주문의 마지막 박스 번호에 합산됩니다.")

    poka_mode = st.session_state.get('fs_poka_mode', False)

    if df is not None and not missing:
        if not poka_mode:
            col_run, col_poka = st.columns([1, 1])
            with col_run:
                if st.button("✅ 실행"):
                    special_flags = st.session_state.get('fs_special_flags_fs', {})
                    special_set = {p for p, f in special_flags.items() if f}
                    buf_all, buf_dom, buf_int = _process_fs(df, effective_tp, box_limit, special_set=special_set)
                    st.session_state['fs_buf_all'] = buf_all.getvalue()
                    st.session_state['fs_buf_dom'] = buf_dom.getvalue()
                    st.session_state['fs_buf_int'] = buf_int.getvalue()
                    st.success("FS 처리 완료!")
            with col_poka:
                if st.button("💰 금액별 포카 추가"):
                    st.session_state['fs_poka_mode'] = True
                    st.session_state['fs_poka_step'] = 1
                    st.session_state['fs_poka_scroll'] = True
                    st.rerun()
        else:

            poka_step = st.session_state.get('fs_poka_step', 1)

            if st.button("← 취소", key="fs_poka_cancel"):
                st.session_state['fs_poka_mode'] = False
                st.session_state.pop('fs_poka_step', None)
                st.rerun()

            round_no = len(st.session_state.get('fs_poka_configs', [])) + 1

            # ── 완료된 라운드 요약 ──
            completed = st.session_state.get('fs_poka_configs', [])
            if completed:
                st.markdown("##### ✅ 완료된 포카 설정")
                for i, cfg in enumerate(completed, 1):
                    cap_str = str(cfg['cap']) if cfg.get('cap') is not None else '무제한'
                    st.info(f"라운드 {i} | 재고명: **{cfg['재고명']}** | 기준: {cfg['base']:,}원 | 최대: {cap_str}")

            # ── Step 1: 재고 체크박스 선택 ──
            if poka_step == 1:
                # Step 1 진입 시 상단으로 스크롤
                if st.session_state.pop('fs_poka_scroll', False):
                    import streamlit.components.v1 as _stc
                    _stc.html(
                        "<script>setTimeout(function(){"
                        "var el=window.parent.document.getElementById('stMain');"
                        "if(el)el.scrollTo({top:0,behavior:'smooth'});"
                        "},80);</script>",
                        height=0
                    )
                st.markdown(f"### 💰 금액별 포카 추가 — 라운드 {round_no} · 재고 선택")
                _df_num = pd.DataFrame(df.to_dict('records'))
                _price = pd.to_numeric(_df_num['상품금액'], errors='coerce').fillna(0)
                poka_products = sorted(_df_num.loc[_price != 0, '재고명'].dropna().unique())

                saved_selected = set(st.session_state.get('fs_poka_selected', []))
                new_selected = []

                st.markdown("##### 재고명 선택")
                for prod in poka_products:
                    checked = st.checkbox(prod, value=(prod in saved_selected), key=f"fs_chk_{round_no}_{prod}")
                    if checked:
                        new_selected.append(prod)

                st.session_state['fs_poka_selected'] = new_selected

                if new_selected and st.button("다음 →", key="fs_poka_next1"):
                    st.session_state['fs_poka_step'] = 2
                    st.session_state['fs_poka_scroll'] = True
                    st.rerun()

            # ── Step 2: 환율(일괄) + 주문별 총액 + 금액 기준 + 상품정보 + 실행 ──
            elif poka_step == 2:
                # Step 2 진입 시 상단으로 스크롤
                if st.session_state.pop('fs_poka_scroll', False):
                    import streamlit.components.v1 as _stc
                    _stc.html(
                        "<script>setTimeout(function(){"
                        "var el=window.parent.document.getElementById('stMain');"
                        "if(el)el.scrollTo({top:0,behavior:'smooth'});"
                        "},80);</script>",
                        height=0
                    )
                st.markdown(f"### 💰 금액별 포카 추가 — 라운드 {round_no} · 설정")

                selected = list(st.session_state.get('fs_poka_selected', []))

                # 환율 일괄 입력 (라운드별 독립 키)
                rate = st.number_input(
                    "환율 (USD → KRW, 선택한 재고 전체 적용)",
                    min_value=1,
                    value=1000,
                    key=f"fs_poka_rate_input_{round_no}"
                )

                # 주문별 총 실결제금액 계산
                _df2 = pd.DataFrame(df.to_dict('records'))
                _df2['수량'] = pd.to_numeric(_df2['수량'], errors='coerce').fillna(0).astype(int)
                _df2['상품금액'] = pd.to_numeric(_df2['상품금액'], errors='coerce').fillna(0).astype(float)

                def calc_amount(row, _sel=selected, _rate=rate):
                    if row['결제통화'] == 'USD' and row['재고명'] in _sel:
                        return row['상품금액'] * row['수량'] * _rate
                    elif row['결제통화'] == 'KRW':
                        return row['상품금액'] * row['수량']
                    return 0

                _df2['_금액'] = _df2.apply(calc_amount, axis=1)
                order_totals = _df2.groupby('주문번호')['_금액'].sum().reset_index()
                order_totals.columns = ['주문번호', '총 실결제금액']
                order_totals['총 실결제금액'] = order_totals['총 실결제금액'].astype(int)

                st.dataframe(order_totals, use_container_width=True, hide_index=True)

                st.markdown("---")
                base = st.number_input("금액 기준", min_value=1,
                                       value=50000,
                                       key=f"fs_poka_base_input_{round_no}")

                limit_type = st.radio("제한 여부", ["무제한", "제한"],
                                      horizontal=True,
                                      key=f"fs_poka_limit_radio_{round_no}")

                cap = None
                if limit_type == "제한":
                    cap = st.number_input("최대 수량 (제한)", min_value=1,
                                          value=7,
                                          key=f"fs_poka_cap_input_{round_no}")

                def get_qty(total):
                    q = int(total // base)
                    if cap is not None:
                        q = min(q, cap)
                    return q

                order_totals['포카 수량'] = order_totals['총 실결제금액'].apply(get_qty)
                order_totals_show = order_totals[order_totals['포카 수량'] > 0]
                if not order_totals_show.empty:
                    st.markdown("##### 📦 포카 지급 결과")
                    st.dataframe(order_totals_show, use_container_width=True, hide_index=True)
                else:
                    st.info("조건에 해당하는 주문이 없습니다.")

                # ── 포카 상품 정보 입력 ──
                st.markdown("---")
                st.markdown("##### 📝 추가할 포카 상품 정보 입력")
                bonus_pname  = st.text_input("상품명",  key=f"fs_bonus_pname_{round_no}")
                bonus_option = st.text_input("옵션명",  key=f"fs_bonus_option_{round_no}")
                bonus_jname  = st.text_input("재고명",  key=f"fs_bonus_jname_{round_no}")
                bonus_jcode  = st.text_input("재고코드", key=f"fs_bonus_jcode_{round_no}")

                all_filled = bool(bonus_pname and bonus_option and bonus_jname and bonus_jcode)

                # 현재 라운드 값을 즉시 캡처 (클로저 아닌 값 고정)
                _cur_selected = list(selected)
                _cur_rate     = int(rate)
                _cur_base     = int(base)
                _cur_cap      = int(cap) if cap is not None else None
                _cur_pname    = str(bonus_pname)
                _cur_option   = str(bonus_option)
                _cur_jname    = str(bonus_jname)
                _cur_jcode    = str(bonus_jcode)

                def _build_current_config():
                    return {
                        'selected': _cur_selected,
                        'rate':     _cur_rate,
                        'base':     _cur_base,
                        'cap':      _cur_cap,
                        '상품명':   _cur_pname,
                        '옵션명':   _cur_option,
                        '재고명':   _cur_jname,
                        '재고코드': _cur_jcode,
                    }

                col_prev, col_more, col_exec = st.columns([1, 2, 2])
                with col_prev:
                    if st.button("← 이전", key="fs_poka_prev"):
                        st.session_state['fs_poka_step'] = 1
                        st.rerun()
                with col_more:
                    if st.button("➕ 포카 1번 더 추가하기", disabled=not all_filled, key="fs_poka_more"):
                        configs = st.session_state.get('fs_poka_configs', [])
                        configs.append(_build_current_config())
                        st.session_state['fs_poka_configs'] = configs
                        # 다음 라운드 초기화
                        st.session_state['fs_poka_step'] = 1
                        st.session_state['fs_poka_selected'] = []
                        st.rerun()
                with col_exec:
                    if st.button("✅ 실행", disabled=not all_filled, key="fs_poka_run"):
                        configs = st.session_state.get('fs_poka_configs', [])
                        configs.append(_build_current_config())
                        special_flags = st.session_state.get('fs_special_flags_fs', {})
                        special_set = {p for p, f in special_flags.items() if f}
                        buf_all, buf_dom, buf_int = _process_fs(
                            df, effective_tp, box_limit,
                            special_set=special_set,
                            bonus_configs=configs
                        )
                        st.session_state['fs_buf_all'] = buf_all.getvalue()
                        st.session_state['fs_buf_dom'] = buf_dom.getvalue()
                        st.session_state['fs_buf_int'] = buf_int.getvalue()
                        # 완료 후 poka 상태 초기화
                        st.session_state['fs_poka_configs'] = []
                        st.session_state['fs_poka_mode'] = False
                        st.success(f"FS 처리 완료 (포카 {len(configs)}종 추가 포함)!")

    if 'fs_buf_all' in st.session_state:
        today = datetime.datetime.now().strftime("%y%m%d")
        st.download_button("▶ 원본 시트 다운로드", st.session_state['fs_buf_all'],
                           file_name=f"FS_{today}_원본.xlsx")


# ───────────────────────────────────────────────────
# 3) 핵심 처리 함수
# ───────────────────────────────────────────────────
def _process_fs(df: pd.DataFrame, tp: dict, limit: int, special_set: set = None, bonus_configs: list = None):
    if special_set is None:
        special_set = set()

    df = pd.DataFrame(df.to_dict('records'))
    df['수량'] = pd.to_numeric(df['수량'], errors='coerce').fillna(0).astype(int)
    df['상품금액'] = pd.to_numeric(df['상품금액'], errors='coerce').fillna(1).astype(float)

    def assign_order_numbers(group):
        total_w, suffix, out = 0.0, 1, []
        special_rows = []
        base_order_no = group['주문번호'].iloc[0]

        for _, row in group.iterrows():
            if row['재고명'] in special_set:
                special_rows.append(row.copy())
                continue

            weight = float(tp.get(row['재고명'], 0) or 0)
            qty = int(row['수량'])
            while qty > 0:
                if total_w + weight > limit:
                    suffix += 1
                    total_w = 0.0
                can = min(qty, int((limit - total_w) // weight) if weight > 0 else qty)
                nr = row.copy()
                nr['수량'] = can
                nr['주문번호'] = f"{base_order_no}-{suffix}"
                out.append(nr.to_dict())
                total_w += can * weight
                qty -= can

        # 특전 → 마지막 박스 번호에 추가
        for row in special_rows:
            nr = row.copy()
            nr['주문번호'] = f"{base_order_no}-{suffix}"
            out.append(nr.to_dict())

        return out

    rows = []
    for _, grp in df.groupby('주문번호'):
        rows += assign_order_numbers(grp)

    if not rows:
        st.warning("처리 가능한 데이터가 없습니다.")
        return io.BytesIO(), io.BytesIO(), io.BytesIO()

    res = pd.DataFrame(rows, columns=df.columns)

    res['상품금액'] = pd.to_numeric(res['상품금액'], errors='coerce').fillna(1).astype(float)
    res['상품금액'] = res['상품금액'].replace(0, 1)
    m = (res['국가코드'] != 'KR') & (res['결제통화'] == 'KRW')
    res.loc[m, '결제통화'] = 'USD'
    res['상품금액'] = res['상품금액'].astype(float)
    res.loc[m, '상품금액'] = res.loc[m, '상품금액'] / 1000
    res['실결제금액'] = res['수량'] * res['상품금액']
    res = res[res['수량'] > 0].copy()
    res['상품명'] = res['재고명']
    res.loc[res['국가명'] == "Japan", '국가명'] = "."

    # ── 금액별 포카 행 삽입 (복수 라운드) ──
    if bonus_configs:
        _df_orig = pd.DataFrame(df.to_dict('records'))
        _df_orig['수량'] = pd.to_numeric(_df_orig['수량'], errors='coerce').fillna(0).astype(int)
        _df_orig['상품금액'] = pd.to_numeric(_df_orig['상품금액'], errors='coerce').fillna(0).astype(float)

        for bonus_config in bonus_configs:
            _bc_selected = bonus_config['selected']
            _bc_rate     = bonus_config['rate']   # 단일 환율
            _bc_base     = bonus_config['base']
            _bc_cap      = bonus_config.get('cap', None)

            def _bc_amount(row, sel=_bc_selected, rate=_bc_rate):
                if row['결제통화'] == 'USD' and row['재고명'] in sel:
                    return row['상품금액'] * row['수량'] * rate
                elif row['결제통화'] == 'KRW':
                    return row['상품금액'] * row['수량']
                return 0

            _df_orig['_금액'] = _df_orig.apply(_bc_amount, axis=1)
            _order_totals = _df_orig.groupby('주문번호')['_금액'].sum()

            bonus_rows = []
            for orig_no, total in _order_totals.items():
                qty = int(total // _bc_base)
                if _bc_cap is not None:
                    qty = min(qty, _bc_cap)
                if qty <= 0:
                    continue
                mask = (
                    res['주문번호'].str.startswith(str(orig_no) + '-') &
                    res['재고명'].isin(_bc_selected)
                )
                if not mask.any():
                    continue
                tmpl = res[mask].iloc[0].copy()
                tmpl['상품명']   = bonus_config['상품명']
                tmpl['옵션명']   = bonus_config['옵션명']
                tmpl['재고명']   = bonus_config['재고명']
                tmpl['재고코드'] = bonus_config['재고코드']
                tmpl['수량']     = qty
                tmpl['상품무게'] = 1
                tmpl['상품금액'] = 1
                tmpl['실결제금액'] = qty
                tmpl['id']       = ''
                bonus_rows.append(tmpl.to_dict())

            if bonus_rows:
                res = pd.concat([res, pd.DataFrame(bonus_rows, columns=res.columns)], ignore_index=True)

    dom = res[res['국가코드'] == 'KR'].copy()
    intl = res[res['국가코드'] != 'KR'].copy()

    intl['희망배송사'] = intl['국가코드'].map(
        lambda c: 'sfexpress' if c in ('CN', 'HK', 'MO') else (
            'ems' if c == 'JP' else (
                'emspremium' if c in ['US', 'IT', 'CO', 'RO', 'DE', 'NL', 'SE', 'AR'] else 'ems'
            )
        )
    )

    fromis_keywords = ["FROM OUR 20S", "프로미스나인"]
    def generate_bonus_rows(src):
        src = src.copy()
        src['원주문번호'] = src['주문번호'].str[:20]
        bonus = []
        mask = src['재고명'].apply(lambda x: any(k in str(x) for k in fromis_keywords))
        for oid, g in src[mask].groupby('원주문번호'):
            currency = g['결제통화'].iloc[0]
            total = g['실결제금액'].sum()
            ratio = 50000 if currency == "KRW" else 50
            cnt = int(total // ratio)
            if cnt > 0:
                r = g.iloc[0].copy()
                r['주문번호'] = f"{oid}-1"
                r['재고코드'] = "301285"
                r['재고명'] = "[프로미스나인 팝업_FROM OUR 20S] MD 구매 특전 포토카드 (5종)"
                r['상품명'] = r['재고명']
                r['옵션명'] = r['재고명']
                r['수량'] = cnt
                r['상품금액'] = 1
                r['실결제금액'] = cnt
                r['결제통화'] = "USD"
                bonus.append(r)
        return pd.DataFrame(bonus, columns=src.columns)

    def fmt(p):
        s = re.sub(r"\D", "", str(p))
        if len(s) == 11:
            return f"{s[:3]}-{s[3:7]}-{s[7:]}"
        return s
    dom['전화번호'] = dom['전화번호'].apply(fmt)

    # ── 정렬: 주문일시 → id → 주문번호 오름차순 ──
    _sort_cols = [c for c in ['주문일시', 'id', '주문번호'] if c in df.columns]
    def _sort_df(d):
        sc = [c for c in ['주문일시', 'id', '주문번호'] if c in d.columns]
        if not sc:
            return d
        return d.sort_values(sc, ascending=True, na_position='last').reset_index(drop=True)

    df   = _sort_df(df)
    dom  = _sort_df(dom)
    intl = _sort_df(intl)

    buf_all = io.BytesIO()
    buf_dom = io.BytesIO()
    buf_int = io.BytesIO()
    with pd.ExcelWriter(buf_all, engine="openpyxl") as w:
        df.to_excel(w, sheet_name="원본", index=False)
        dom.to_excel(w, sheet_name="국내", index=False)
        intl.to_excel(w, sheet_name="해외", index=False)
    with pd.ExcelWriter(buf_dom, engine="openpyxl") as w:
        dom.to_excel(w, sheet_name="국내", index=False)
    with pd.ExcelWriter(buf_int, engine="openpyxl") as w:
        intl.to_excel(w, sheet_name="해외", index=False)
    buf_all.seek(0)
    buf_dom.seek(0)
    buf_int.seek(0)
    return buf_all, buf_dom, buf_int
