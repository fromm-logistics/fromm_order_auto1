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

    # session_state 초기화 (클라우드 환경 대응)
    if 'invoice_courier' not in st.session_state:
        st.session_state.invoice_courier = None
    if 'invoice_region' not in st.session_state:
        st.session_state.invoice_region = None
    if 'df_result' not in st.session_state:
        st.session_state.df_result = None

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
        elif st.session_state.invoice_courier == "패스트박스" and st.session_state.invoice_region == "국내":
            st.markdown("### 3단계: 파일 업로드 및 변환")

            uploaded_file = st.file_uploader(
                "[패스트박스 - 국내] 'Microsoft Excel 97-2003 워크시트(.xls)' 파일을 업로드하세요.",
                type=["xls"]
            )

            if uploaded_file is not None:
                st.success(f"📂 {uploaded_file.name} 파일이 가져오기 완료되었습니다.")

                courier_input = st.selectbox(
                    "배송사를 선택하세요",
                    options=["", "cjlogistics", "epost", "hanjin", "logen", "lotte"],
                    index=0,
                    format_func=lambda x: "-- 선택하세요 --" if x == "" else x,
                    key="fastbox_courier_select"
                )

                if st.button("송장업로드 파일 변환 실행", use_container_width=True, key="fastbox_convert_btn"):
                    if not courier_input.strip():
                        st.error("⚠️ 배송사 이름을 먼저 선택한 후 변환을 실행해 주세요!")
                    else:
                        try:
                            uploaded_file.seek(0)
                            html_text = uploaded_file.read().decode('utf-8', errors='ignore')
                            df = None

                            df = _parse_html_table(html_text)

                            if df is None or not any(col in df.columns for col in ['송장번호', '코드1', '주문수량']):
                                try:
                                    df_list = pd.read_html(io.StringIO(html_text), header=0)
                                    if df_list:
                                        df = df_list[0]
                                        df.columns = df.columns.astype(str).str.strip()
                                except Exception:
                                    pass

                            if df is None or not any(col in df.columns for col in ['송장번호', '코드1', '주문수량']):
                                try:
                                    uploaded_file.seek(0)
                                    df_xls = pd.read_excel(uploaded_file, engine='xlrd', header=None)
                                    for i in range(min(10, len(df_xls))):
                                        row_vals = df_xls.iloc[i].astype(str).str.strip().tolist()
                                        if '코드1' in row_vals or '송장번호' in row_vals:
                                            df_xls.columns = df_xls.iloc[i].astype(str).str.strip()
                                            df = df_xls[i+1:].reset_index(drop=True)
                                            break
                                except Exception:
                                    pass

                            if df is None or len(df) == 0:
                                raise ValueError("파일 구조를 해석할 수 없습니다. 파일이 손상됐거나 형식이 다릅니다.")

                            df.columns = df.columns.astype(str).str.strip()

                            required_cols = ['주문수량', '송장번호', '코드1', '복사_관리번호']
                            missing_cols = [c for c in required_cols if c not in df.columns]

                            if missing_cols:
                                st.error(f"❌ 엑셀 파일에 필요한 열이 없습니다: {missing_cols}")
                                st.warning("💡 파일에서 감지된 열 목록:")
                                st.write(list(df.columns))
                                st.dataframe(df.head(5))
                            else:
                                # 1. '판매처'에서 "wonderwall(해외)" 행 삭제
                                if '판매처' in df.columns:
                                    df = df[df['판매처'] != "Wonderwall(해외)"]

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
                    file_name = f"{today_str}_패스트박스_국내.csv"

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
        elif st.session_state.invoice_courier == "다보내" and st.session_state.invoice_region == "해외":
            st.markdown("### 3단계: 파일 업로드 및 변환")

            uploaded_file = st.file_uploader(
                "[다보내 - 해외] CSV 파일을 업로드하세요.",
                type=["csv"]
            )

            if uploaded_file is not None:
                st.success(f"📂 {uploaded_file.name} 파일이 가져오기 완료되었습니다.")

                if st.button("송장업로드 파일 변환 실행", use_container_width=True, key="dabonae_overseas_convert_btn"):
                    try:
                        # CSV 읽기 (인코딩 자동 감지)
                        uploaded_file.seek(0)
                        try:
                            df = pd.read_csv(uploaded_file, encoding='utf-8-sig', dtype=str)
                        except Exception:
                            uploaded_file.seek(0)
                            df = pd.read_csv(uploaded_file, encoding='cp949', dtype=str)

                        df.columns = df.columns.astype(str).str.strip()

                        # ="값" 형식으로 저장된 셀을 순수 값으로 변환 (예: ="NONE" → NONE)
                        df = df.apply(lambda col: col.str.replace(r'^="(.*)"$', r'\1', regex=True))

                        # 열 존재 확인
                        required_cols = ['현지 배송사', '배송 No1', '관리번호', '상품수량']
                        missing_cols = [c for c in required_cols if c not in df.columns]

                        if missing_cols:
                            st.error(f"❌ CSV 파일에 필요한 열이 없습니다: {missing_cols}")
                            st.warning("💡 파일에서 감지된 열 목록:")
                            st.write(list(df.columns))
                            st.dataframe(df.head(5))
                        else:
                            # 1. 필요한 열만 남기기
                            df = df[required_cols]

                            # 2. '관리번호' 빈값 또는 "NONE" 행 삭제
                            df = df[df['관리번호'].notna()]
                            df = df[df['관리번호'].astype(str).str.strip() != ""]
                            df = df[df['관리번호'].astype(str).str.strip().str.upper() != "NONE"]
                            df = df[df['관리번호'].astype(str).str.lower() != "nan"]

                            # 3. '현지 배송사' 또는 '배송 No1' 빈값 행 삭제
                            df = df[df['현지 배송사'].notna()]
                            df = df[df['현지 배송사'].astype(str).str.strip() != ""]
                            df = df[df['현지 배송사'].astype(str).str.lower() != "nan"]
                            df = df[df['배송 No1'].notna()]
                            df = df[df['배송 No1'].astype(str).str.strip() != ""]
                            df = df[df['배송 No1'].astype(str).str.lower() != "nan"]

                            # 4. '현지 배송사' 소문자 변환
                            df['현지 배송사'] = df['현지 배송사'].astype(str).str.lower().str.strip()

                            # 5. 열 순서 재정렬
                            df = df[['관리번호', '현지 배송사', '배송 No1', '상품수량']]

                            # 6. 열 헤드 이름 수정
                            df.columns = ['id', 'courier', 'waybill', 'amount']

                            # 7. 'id'와 'courier' 중복값 제거 후 'amount' 합치기
                            df['amount'] = pd.to_numeric(df['amount'], errors='coerce').fillna(0).astype(int)
                            df = df.groupby(['id', 'courier'], as_index=False).agg({'waybill': 'first', 'amount': 'sum'})
                            df = df[['id', 'courier', 'waybill', 'amount']]

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
                    file_name = f"{today_str}_다보내_해외.csv"

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
        elif st.session_state.invoice_courier == "패스트박스" and st.session_state.invoice_region == "해외":
            st.markdown("### 3단계: 파일 업로드 및 변환")

            uploaded_file = st.file_uploader(
                "[패스트박스 - 해외] 암호화된 ZIP 파일을 업로드하세요.",
                type=["zip"]
            )

            if uploaded_file is not None:
                st.success(f"📂 {uploaded_file.name} 파일이 가져오기 완료되었습니다.")

                password_input = st.text_input(
                    "비밀번호를 입력해 주세요.",
                    type="password",
                    key="fastbox_overseas_pw"
                )

                if st.button("송장업로드 파일 변환 실행", use_container_width=True, key="fastbox_overseas_btn"):
                    if not password_input.strip():
                        st.error("⚠️ 비밀번호를 입력해 주세요!")
                    else:
                        try:
                            zip_bytes = uploaded_file.read()
                            pw = password_input.encode('utf-8')
                            all_dfs = []

                            # pyzipper(AES) 우선, 없으면 표준 zipfile(ZipCrypto) 사용
                            try:
                                import pyzipper
                                zf_ctx = pyzipper.AESZipFile(io.BytesIO(zip_bytes))
                                zf_ctx.setpassword(pw)
                                use_pyzipper = True
                            except ImportError:
                                import zipfile as zf_mod
                                zf_ctx = zf_mod.ZipFile(io.BytesIO(zip_bytes))
                                use_pyzipper = False

                            with zf_ctx as zf:
                                if not use_pyzipper:
                                    zf.setpassword(pw)

                                # '주문목록_숫자' 파일 목록 수집 후 정렬
                                file_names = sorted(
                                    n for n in zf.namelist()
                                    if re.search(r'주문목록_\d+', n)
                                )

                                if not file_names:
                                    st.error("❌ ZIP 내에 '주문목록_숫자' 형식의 파일이 없습니다.")
                                else:
                                    for fname in file_names:
                                        data = zf.read(fname)
                                        df_raw = pd.read_excel(
                                            io.BytesIO(data), engine='openpyxl', dtype=str
                                        )
                                        df_raw.columns = df_raw.columns.astype(str).str.strip()

                                        # 1. '판매사 품주번호' 8번째 자리가 '-'가 아닌 행 삭제
                                        col_id = '판매사 품주번호'
                                        if col_id not in df_raw.columns:
                                            st.warning(f"⚠️ {fname}: '{col_id}' 열 없음 — 건너뜁니다.")
                                            continue
                                        df_raw = df_raw[df_raw[col_id].astype(str).str.len() >= 8]
                                        df_raw = df_raw[df_raw[col_id].astype(str).str[7] == '-']

                                        # 2. 필요 열만 남기기
                                        required = ['판매사 품주번호', '희망배송사', '해외배송송장번호', '수량']
                                        missing = [c for c in required if c not in df_raw.columns]
                                        if missing:
                                            st.warning(f"⚠️ {fname}: 열 누락 {missing} — 건너뜁니다.")
                                            continue
                                        df_raw = df_raw[required]

                                        # 3. '판매사 품주번호' 앞 7자리만 남기기
                                        df_raw['판매사 품주번호'] = df_raw['판매사 품주번호'].astype(str).str[:7]

                                        # 3-1. '희망배송사'에서 emspremium → ems 치환
                                        df_raw['희망배송사'] = df_raw['희망배송사'].str.replace('emspremium', 'ems', regex=False)

                                        # 4. 열 이름 변경
                                        df_raw.columns = ['id', 'courier', 'waybill', 'amount']

                                        all_dfs.append(df_raw)

                            if not all_dfs:
                                raise ValueError("처리된 데이터가 없습니다. 파일 구조를 확인해 주세요.")

                            # 5+6. 전체 합치기 + 중복 제거 (id+courier 기준, amount 합산)
                            df_combined = pd.concat(all_dfs, ignore_index=True)
                            df_combined['amount'] = pd.to_numeric(
                                df_combined['amount'], errors='coerce'
                            ).fillna(0).astype(int)
                            df_combined = df_combined.groupby(
                                ['id', 'courier'], as_index=False
                            ).agg({'waybill': 'first', 'amount': 'sum'})
                            df_combined = df_combined[['id', 'courier', 'waybill', 'amount']]

                            st.session_state.df_result = df_combined
                            st.success("🎉 파일 변환이 성공적으로 완료되었습니다!")
                            st.rerun()

                        except ImportError:
                            st.error("❌ pyzipper 패키지가 필요합니다. 터미널에서 `pip install pyzipper`를 실행해 주세요.")
                        except RuntimeError as e:
                            st.error("❌ 비밀번호가 올바르지 않거나 파일이 손상되었습니다.")
                        except Exception as e:
                            st.error(f"❌ 파일 처리 중 에러가 발생했습니다: {e}")

                # 변환 완료 후 저장
                if st.session_state.df_result is not None:
                    st.write("---")
                    st.markdown("### 4단계: 변환된 파일 저장")
                    st.dataframe(st.session_state.df_result, use_container_width=True)

                    today_str = datetime.today().strftime('%Y%m%d')
                    file_name = f"{today_str}_패스트박스_해외.csv"

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
