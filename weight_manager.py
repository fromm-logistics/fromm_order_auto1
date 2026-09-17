# weight_manager.py
import streamlit as st
from weight_db import load_weights, save_weight, save_weights_bulk, delete_weight


def run_weight_manager():
    st.button(
        "⬅️ MD 메뉴로 돌아가기",
        on_click=lambda: st.session_state.update(page="md_main"),
        key="back_from_weight_mgr",
    )
    st.title("⚖️ 재고 무게 관리")
    st.caption("MD 나누기에서 사용하는 재고명별 무게(g)를 저장·수정합니다.")

    # ── 로드 ──────────────────────────────────────────────
    with st.spinner("무게 DB 불러오는 중..."):
        weights = load_weights()

    # ── 통계 ──────────────────────────────────────────────
    st.metric("저장된 재고 수", f"{len(weights):,}개")
    st.write("---")

    # ── 검색 + 목록 ───────────────────────────────────────
    search = st.text_input("🔍 재고명 검색", placeholder="검색어 입력", key="wm_search")
    filtered = (
        {k: v for k, v in weights.items() if search.lower() in k.lower()}
        if search else weights
    )

    if filtered:
        st.markdown(f"**{len(filtered)}개** 표시 중")

        # 변경 추적용 session_state
        if "wm_edits" not in st.session_state:
            st.session_state.wm_edits = {}

        col_h1, col_h2, col_h3 = st.columns([7, 2, 1])
        col_h1.markdown("**재고명**")
        col_h2.markdown("**무게 (g)**")

        for name in sorted(filtered.keys()):
            col1, col2, col3 = st.columns([7, 2, 1])
            col1.text(name)
            new_w = col2.number_input(
                label="무게",
                value=filtered[name],
                min_value=1,
                step=1,
                key=f"wm_{name}",
                label_visibility="collapsed",
            )
            # 저장 버튼 (값이 변경된 경우에만 활성)
            if col3.button("💾", key=f"wsave_{name}", help="저장"):
                if save_weight(name, new_w):
                    st.toast(f"✅ '{name}' 저장 완료 ({new_w}g)")
                    st.rerun()
                else:
                    st.error("저장 실패")

        # 삭제 섹션
        st.write("---")
        with st.expander("🗑️ 재고 삭제"):
            del_name = st.selectbox("삭제할 재고명 선택", options=sorted(filtered.keys()), key="wm_del_select")
            if st.button("삭제 확인", type="primary", key="wm_del_btn"):
                if delete_weight(del_name):
                    st.success(f"'{del_name}' 삭제 완료")
                    st.rerun()
                else:
                    st.error("삭제 실패")
    else:
        st.info("저장된 재고 무게가 없거나 검색 결과가 없습니다.")

    # ── 새 재고 추가 ───────────────────────────────────────
    st.write("---")
    st.subheader("새 재고 추가")
    col1, col2, col3 = st.columns([6, 2, 2])
    new_name = col1.text_input("재고명", placeholder="재고명 입력", key="wm_new_name")
    new_weight = col2.number_input("무게(g)", min_value=1, step=1, key="wm_new_weight")
    col3.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
    if col3.button("추가", key="wm_add_btn"):
        if not new_name.strip():
            st.error("재고명을 입력해주세요.")
        elif new_name in weights:
            st.warning(f"'{new_name}'은 이미 존재합니다. 목록에서 수정해주세요.")
        else:
            if save_weight(new_name.strip(), new_weight):
                st.success(f"'{new_name}' ({new_weight}g) 추가 완료")
                st.rerun()
            else:
                st.error("추가 실패")
    col3.markdown("</div>", unsafe_allow_html=True)

    # ── CSV 일괄 가져오기 ──────────────────────────────────
    st.write("---")
    with st.expander("📥 CSV로 일괄 가져오기"):
        st.caption("헤더: `재고명,무게(g)` 형식의 CSV 파일을 업로드하세요.")
        csv_file = st.file_uploader("CSV 업로드", type=["csv"], key="wm_csv")
        if csv_file:
            import pandas as pd
            try:
                df_csv = pd.read_csv(csv_file)
                if "재고명" in df_csv.columns and "무게(g)" in df_csv.columns:
                    new_weights = {
                        row["재고명"]: int(row["무게(g)"])
                        for _, row in df_csv.dropna().iterrows()
                        if str(row["무게(g)"]).isdigit()
                    }
                    st.dataframe(df_csv, use_container_width=True)
                    if st.button(f"📤 {len(new_weights)}개 저장", key="wm_csv_save"):
                        if save_weights_bulk(new_weights):
                            st.success(f"{len(new_weights)}개 저장 완료")
                            st.rerun()
                else:
                    st.error("열 이름이 '재고명', '무게(g)' 이어야 합니다.")
            except Exception as e:
                st.error(f"CSV 읽기 오류: {e}")
