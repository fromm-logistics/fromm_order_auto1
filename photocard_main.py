import streamlit as st
import pandas as pd
import io
import re
from datetime import datetime


def run_photocard_main():
    st.title("🃏 포토카드 갯수")

    # session_state 초기화
    if 'pc_df' not in st.session_state:
        st.session_state.pc_df = None
    if 'pc_selected' not in st.session_state:
        st.session_state.pc_selected = []
    if 'pc_results' not in st.session_state:
        st.session_state.pc_results = None

    # 메인 메뉴로 돌아가기 버튼
    if st.button("⬅️ 메인 메뉴로 돌아가기"):
        st.session_state.page = 'main'
        st.session_state.pc_df = None
        st.session_state.pc_selected = []
        st.session_state.pc_results = None
        st.rerun()

    st.write("---")

    # STEP 1: CSV 파일 업로드
    st.markdown("### 1단계: CSV 파일을 업로드하세요")
    uploaded_file = st.file_uploader("CSV 파일을 업로드하세요.", type=["csv"])

    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file, encoding='utf-8-sig', dtype=str)
        except Exception:
            uploaded_file.seek(0)
            df = pd.read_csv(uploaded_file, encoding='cp949', dtype=str)

        df.columns = df.columns.astype(str).str.strip()

        if '재고명' not in df.columns:
            st.error("❌ CSV 파일에 '재고명' 열이 없습니다.")
            st.warning("💡 파일에서 감지된 열 목록:")
            st.write(list(df.columns))
        else:
            st.session_state.pc_df = df
            st.session_state.pc_results = None  # 파일 바뀌면 결과 초기화
            st.success(f"📂 {uploaded_file.name} 파일이 업로드되었습니다.")

    # STEP 2: 재고명 선택
    if st.session_state.pc_df is not None:
        df = st.session_state.pc_df
        st.write("---")
        st.markdown("### 2단계: 재고명을 선택하세요")

        options = sorted(
            df['재고명'].dropna()
            .astype(str)
            .str.strip()
            .replace('', pd.NA)
            .dropna()
            .unique()
            .tolist()
        )

        selected = st.multiselect(
            "재고명 선택 (복수 선택 가능)",
            options=options,
            default=st.session_state.pc_selected
        )
        st.session_state.pc_selected = selected

        if selected:
            st.write("---")
            st.markdown("### 3단계: 포토카드 종 수를 입력하세요")
            card_counts = {}
            for item in selected:
                card_counts[item] = st.number_input(
                    f"포토카드 종 수 - {item}",
                    min_value=1, step=1, value=1,
                    key=f"card_count_{item}"
                )

            if st.button("포토카드 수량 정리 실행", use_container_width=True):
                df_work = st.session_state.pc_df.copy()

                # 1. '배송진행여부'에서 "cancelled" 행 삭제
                if '배송진행여부' in df_work.columns:
                    df_work = df_work[
                        df_work['배송진행여부'].astype(str).str.strip().str.lower() != 'cancelled'
                    ]

                # 필요 열 확인
                missing = [c for c in ['재고명', '주문번호', '수량'] if c not in df_work.columns]
                if missing:
                    st.error(f"❌ 필요한 열이 없습니다: {missing}")
                else:
                    df_work['수량'] = pd.to_numeric(df_work['수량'], errors='coerce').fillna(0).astype(int)

                    results = {}
                    for item in selected:
                        df_item = df_work[df_work['재고명'] == item][['주문번호', '수량']]

                        # 2. 주문번호 기준 수량 합계 피벗
                        pivot = df_item.groupby('주문번호', as_index=False)['수량'].sum()
                        pivot.columns = ['주문번호', '수량합계']

                        # 3. 세트 / 낱장 계산
                        pivot['세트'] = pivot['수량합계'] // card_counts[item]
                        pivot['낱장'] = pivot['수량합계'] % card_counts[item]

                        # 4. 총합
                        results[item] = {
                            'pivot': pivot,
                            'total_set':   int(pivot['세트'].sum()),
                            'total_loose': int(pivot['낱장'].sum()),
                            'total_qty':   int(pivot['수량합계'].sum()),
                        }

                    st.session_state.pc_results = results

        # 결과 출력
        if st.session_state.pc_results:
            results = st.session_state.pc_results
            st.write("---")
            st.markdown("### 결과")

            for item, data in results.items():
                st.markdown(f"#### 📦 {item}")
                st.dataframe(data['pivot'], use_container_width=True)
                st.markdown(
                f"**세트: {data['total_set']:,}EA &nbsp;/&nbsp; "
                f"낱장: {data['total_loose']:,}EA &nbsp;/&nbsp; "
                f"총: {data['total_qty']:,}EA**",
                unsafe_allow_html=True
                )

            # 5. 엑셀 다운로드 (재고명별 시트)
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                for item, data in results.items():
                    sheet_name = re.sub(r'[\[\]:*?/\\]', '_', item)[:31]  # 엑셀 시트명 31자 제한
                    pivot = data['pivot'].copy()
                    total_row = pd.DataFrame([{
                        '주문번호': '합계',
                        '수량합계': data['total_qty'],
                        '세트':     data['total_set'],
                        '낱장':     data['total_loose'],
                    }])
                    pd.concat([pivot, total_row], ignore_index=True).to_excel(
                        writer, sheet_name=sheet_name, index=False
                    )

            today_str = datetime.today().strftime('%Y%m%d')
            st.download_button(
                label="💾 결과 엑셀 다운로드",
                data=buffer.getvalue(),
                file_name=f"{today_str}_포토카드갯수.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )