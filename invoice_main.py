# invoice_main.py
import streamlit as st
import pandas as pd
from datetime import datetime
from html.parser import HTMLParser
import io
import re


# ── 내장 html.parser 기반 HTML 테이블 파서 (lxml/bs4 불필요) ──────────────
class _TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self._table, self._row, self._cell, self._in = [], [], [], [], False

    def handle_starttag(self, tag, attrs):
        tag = tag.lower()
        if tag == 'table':   self._table = []
        elif tag == 'tr':    self._row = []
        elif tag in ('td', 'th'): self._cell = []; self._in = True

    def handle_endtag(self, tag):
        tag = tag.lower()
        if tag == 'table':
            if self._table: self.tables.append(self._table[:])
        elif tag == 'tr':
            if self._row: self._table.append(self._row[:])
        elif tag in ('td', 'th'):
            self._row.append(''.join(self._cell).strip()); self._in = False

    def handle_data(self, data):
        if self._in: self._cell.append(data)


def _parse_html_table(html_text: str) -> pd.DataFrame | None:
    """HTML 문자열에서 가장 큰 테이블을 DataFrame으로 반환."""
    p = _TableParser()
    p.feed(html_text)
    if not p.tables:
        return None
    table = max(p.tables, key=len)
    if len(table) < 2:
        return None
    headers = [str(h).strip() for h in table[0]]
    rows = [r + [''] * max(0, len(headers) - len(r)) for r in table[1:]]
    rows = [r[:len(headers)] for r in rows]
    return pd.DataFrame(rows, columns=headers)

def run_invoice_main():
    st.title("📦 송장")

    # 메인 메뉴로 돌아가기 버튼
    if st.button("⬅️ 메인 메뉴로 돌아가기"):
        st.session_state.page = 'main'
        st.session_state.invoice_courier = None
        st.session_state.invoice_region = None
        st.session_state.df_result = None
        st.rerun()

    st.write("---")

    # STEP 1: 택배사 선택
    st.markdown("### 1단계: 택배사를 선택하세요")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("다보내", use_container_width=True):
            st.session_state.invoice_courier = "다보내"
            st.session_state.invoice_region = None
            st.session_state.df_result = None
            st.rerun()
    with col2:
        if st.button("패스트박스", use_container_width=True):
            st.session_state.invoice_courier = "패스트박스"
            st.session_state.invoice_region = None
            st.session_state.df_result = None
            st.rerun()

    # STEP 2: 지역 선택
    if st.session_state.invoice_courier:
        st.write("---")
        st.markdown(f"현재 선택된 택배사: **{st.session_state.invoice_courier}**")
        st.markdown("### 2단계: 배송 지역을 선택하세요")

        col3, col4 = st.columns(2)
        with col3:
            if st.button("국내", use_container_width=True):
                st.session_state.invoice_region = "국내"
                st.session_state.df_result = None
                st.rerun()
        with col4:
            if st.button("해외", use_container_width=True):
                st.session_state.invoice_region = "해외"
                st.session_state.df_result = None
                st.rerun()

    # STEP 3: 파일 업로드 및 데이터 처리
    if st.session_state.invoice_courier and st.session_state.invoice_region:
        st.write("---")
        st.markdown(f"선택된 조건: **{st.session_state.invoice_courier} - {st.session_state.invoice_region}**")

        # 다보내 - 국내인 경우에만 엑셀 처리 로직 활성화
        if st.session_state.invoice_courier == "다보내" and st.session_state.invoice_region == "국내":
            st.markdown("### 3단계: 파일 업로드 및 변환")

            uploaded_file = st.file_uploader(
                "[다보내 - 국내] 'Microsoft Excel 97-2003 워크시트(.xls)' 파일을 업로드하세요.",
                type=["xls"]
            )

            if uploaded_file is not None:
                st.success(f"📂 {uploaded_file.name} 파일이 가져오기 완료되었습니다.")

                courier_input = st.selectbox(
                    "배송사를 선택하세요",
                    options=["", "cjlogistics", "epost", "hanjin", "logen", "lotte"],
                    index=0,
                    format_func=lambda x: "-- 선택하세요 --" if x == "" else x
                )

                if st.button("송장업로드 파일 변환 실행", use_container_width=True):
                    if not courier_input.strip():
                        st.error("⚠️ 배송사 이름을 먼저 입력한 후 변환을 실행해 주세요!")
                    else:
                        try:
                            uploaded_file.seek(0)
                            html_text = uploaded_file.read().decode('utf-8', errors='ignore')
                            df = None

                            # --- 🛠️ 1차 시도: 내장 html.parser (외부 패키지 불필요) ---
                            df = _parse_html_table(html_text)

                            # --- 🛠️ 2차 시도: pandas read_html (lxml/bs4 있는 환경) ---
                            if df is None or not any(col in df.columns for col in ['송장번호', '코드1', '주문수량']):
                                try:
                                    df_list = pd.read_html(io.StringIO(html_text), header=0)
                                    if df_list:
                                        df = df_list[0]
                                        df.columns = df.columns.astype(str).str.strip()
                                except Exception:
                                    pass

                            # --- 🛠️ 3차 시도: 진짜 바이너리 XLS (xlrd) ---
                            if df is None or not any(col in df.columns for col in ['송장번호', '코드1', '주문수량']):
                                try:
                                    uploaded_file.seek(0)
                                    df_xls = pd.read_excel(uploaded_file, engine='xlrd', header=None)
                                    # 헤더 행 탐색
                                    for i in range(min(10, len(df_xls))):
                                        row_vals = df_xls.iloc[i].astype(str).str.strip().tolist()
                                        if '코드1' in row_vals or '송장번호' in row_vals:
                                            df_xls.columns = df_xls.iloc[i].astype(str).str.strip()
                                            df = df_xls[i+1:].reset_index(drop=True)
                                            break
                                except Exception:
                                    pass

                            # 최종 검증
                            if df is None or len(df) == 0:
                                raise ValueError("파일 구조를 해석할 수 없습니다. 파일이 손상됐거나 형식이 다릅니다.")

                            df.columns = df.columns.astype(str).str.strip()

                            # 열 존재 확인
                            required_cols = ['주문수량', '송장번호', '코드1', '복사_관리번호']
                            missing_cols = [c for c in required_cols if c not in df.columns]

                            if missing_cols:
                                st.error(f"❌ 엑셀 파일에 필요한 열이 없습니다: {missing_cols}")
                                st.warning("💡 파일에서 감지된 열 목록:")
                                st.write(list(df.columns))
                                st.markdown("👇 **업로드된 데이터 형태 미리보기**")
                                st.dataframe(df.head(5))
                            else:
                                # 1. '판매처'에서 "프롬스토어(해외)" 행 삭제
                                if '판매처' in df.columns:
                                    df = df[df['판매처'] != "프롬스토어(해외)"]

                                # 2. '수령자주소'에 "YTO(노머스 대련CC)" 포함하는 행 삭제
                                if '수령자주소' in df.columns:
                                    df = df[~df['수령자주소'].astype(str).str.contains(r"YTO\(노머스 대련CC\)", na=False)]

                                # 3. 지정된 열만 남기기
                                df = df[required_cols]

                                # 4. '코드1'에서 빈값(NaN) 행 삭제
                                df = df.dropna(subset=['코드1'])
                                df = df[df['코드1'].astype(str).str.strip() != ""]
                                df = df[df['코드1'].astype(str).str.lower() != "nan"]

                                # 5. '복사_관리번호'에서 0이 아닌 값들은 행 삭제
                                df = df[df['복사_관리번호'].astype(str).str.strip() == "0"]

                                # 6. '코드1'과 '송장번호' 중복값 제거 후 '주문수량' 합치기
                                df['주문수량'] = pd.to_numeric(df['주문수량'], errors='coerce').fillna(0).astype(int)
                                df = df.groupby(['코드1', '송장번호'], as_index=False)['주문수량'].sum()

                                # 7~9. 열 순서 정렬 및 '배송사' 열 추가
                                df['배송사'] = courier_input.strip()
                                df = df[['코드1', '배송사', '송장번호', '주문수량']]

                                # 10. 열 헤드 이름 수정
                                df.columns = ['id', 'courier', 'waybill', 'amount']

                                st.session_state.df_result = df
                                st.success("🎉 파일 변환이 성공적으로 완료되었습니다!")
                                st.rerun()

                        except Exception as e:
                            st.error(f"❌ 파일 처리 중 에러가 발생했습니다: {e}")

                # 변환 완료 후 저장 단계
                if st.session_state.df_result is not None:
                    st.write("---")
                    st.markdown("### 4단계: 변환된 파일 저장")
                    st.dataframe(st.session_state.df_result, use_container_width=True)

                    today_str = datetime.today().strftime('%Y%m%d')
                    file_name = f"{today_str}_다보내_국내.csv"

                    # 모든 값을 텍스트로 변환 후 CSV 저장
                    # ① float 포맷 제거: 1395397.0 → 1395397
                    # ② Excel 텍스트 강제 인식: ="값" 형식으로 감싸기
                    #    (pandas to_csv는 "를 이중 이스케이프하므로 CSV를 직접 작성)
                    df_export = st.session_state.df_result.copy()
                    for col in df_export.columns:
                        if pd.api.types.is_numeric_dtype(df_export[col]):
                            df_export[col] = df_export[col].astype('int64').astype(str)
                        else:
                            df_export[col] = (
                                df_export[col].astype(str)
                                .str.replace(r'\.0$', '', regex=True)
                            )

                    header_line = ','.join(df_export.columns.tolist())
                    data_lines = [
                        ','.join(str(v) for v in row)
                        for row in df_export.itertuples(index=False, name=None)
                    ]
                    csv_str = header_line + '\n' + '\n'.join(data_lines) + '\n'
                    csv_bytes = csv_str.encode('utf-8-sig')

                    st.download_button(
                        label="💾 변환된 파일 저장 (다운로드)",
                        data=csv_bytes,
                        file_name=file_name,
                        mime="text/csv",
                        use_container_width=True
                    )
        else:
            st.markdown("### 3단계: 파일을 업로드하세요")
            st.info(f"현재 [{st.session_state.invoice_courier} - {st.session_state.invoice_region}] 기능은 준비 중입니다.")