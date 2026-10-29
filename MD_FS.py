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
        product_names = sorted(df['재고명'].dropna().unique())
        saved_special = st.session_state.get("fs_special_flags_fs", {})
        new_special = {}

        st.markdown("### 🎁 특전 상품 설정")
        st.caption("특전으로 지정된 재고는 무게 계산에서 제외되며, 각 주문의 마지막 박스 번호에 포함됩니다.")

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

    if df is not None and st.button("✅ 실행", disabled=bool(missing)):
        special_flags = st.session_state.get('fs_special_flags_fs', {})
        special_set = {prod for prod, flag in special_flags.items() if flag}
        buf_all, buf_dom, buf_int = _process_fs(df, effective_tp, box_limit, special_set=special_set)
        st.session_state['fs_buf_all'] = buf_all.getvalue()
        st.session_state['fs_buf_dom'] = buf_dom.getvalue()
        st.session_state['fs_buf_int'] = buf_int.getvalue()
        st.success("FS 처리 완료!")

    if 'fs_buf_all' in st.session_state:
        today = datetime.datetime.now().strftime("%y%m%d")
        st.download_button("▶ 원본 시트 다운로드", st.session_state['fs_buf_all'],
                           file_name=f"FS_{today}_원본.xlsx")
        st.download_button("▶ 국내 시트 다운로드", st.session_state['fs_buf_dom'],
                           file_name=f"FS_{today}_국내.xlsx")
        st.download_button("▶ 해외 시트 다운로드", st.session_state['fs_buf_int'],
                           file_name=f"FS_{today}_해외.xlsx")


# ───────────────────────────────────────────────────
# 3) 핵심 처리 함수
# ───────────────────────────────────────────────────
def _process_fs(df: pd.DataFrame, tp: dict, limit: int, special_set: set = None):
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
