# md_main.py
import streamlit as st
from MD_FS import run_md_fs, target_products as fs_products
from MD_SS import run_md_ss, target_products as ss_products
from MD_general import run_md_general
from weight_db import load_weights, save_weights_bulk, WEIGHT_SPREADSHEET_ID

SHEET_URL = f"https://docs.google.com/spreadsheets/d/{WEIGHT_SPREADSHEET_ID}/"


def run_md_main():
    st.button("◀ 이전으로 돌아가기", on_click=lambda: st.session_state.update(page="main"))
    st.title("📋 MD 나누기")

    st.button("FS 나누기",      on_click=lambda: st.session_state.update(page="md_fs"))
    st.button("SS 나누기",      on_click=lambda: st.session_state.update(page="md_ss"))
    st.button("General 나누기", on_click=lambda: st.session_state.update(page="md_general"))

    st.markdown("---")
    st.subheader("⚖️ 재고 무게 관리")

    existing = load_weights()

    if not existing:
        st.warning("저장된 무게가 없습니다. 초기 데이터를 업로드해주세요.")
        if st.button("📤 MD_FS + MD_SS 무게 초기 업로드"):
            all_products = {**ss_products, **fs_products}  # FS가 중복 시 우선
            with st.spinner(f"{len(all_products)}개 업로드 중..."):
                if save_weights_bulk(all_products):
                    st.success(f"✅ {len(all_products)}개 재고 무게 업로드 완료!")
                    st.rerun()
                else:
                    st.error("업로드 실패")
    else:
        st.caption(f"현재 **{len(existing)}개** 재고 무게 저장됨")

    st.link_button("🔗 구글 시트에서 무게 수정하기", SHEET_URL)


def run_md_fs_page():
    run_md_fs()

def run_md_ss_page():
    run_md_ss()

def run_md_general_page():
    run_md_general()
