import streamlit as st
import requests
import pandas as pd
from dotenv import load_dotenv
import os
from datetime import datetime, timedelta

# Load environment variables
load_dotenv()

# NEIS API Configuration
NEIS_API_KEY = os.getenv('NEIS_API_KEY')
SCHOOL_INFO_URL = "https://open.neis.go.kr/hub/schoolInfo"
MEAL_INFO_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

def fetch_school_info(school_name=None, school_type=None, region=None):
    """
    NEIS API에서 학교 정보를 가져옵니다
    """
    params = {
        'KEY': NEIS_API_KEY,
        'Type': 'json',
        'pIndex': 1,
        'pSize': 100
    }
    
    if school_name:
        params['SCHUL_NM'] = school_name
    if school_type:
        params['SCHUL_KND_SC_NM'] = school_type
    if region:
        params['LCTN_SC_NM'] = region

    try:
        response = requests.get(SCHOOL_INFO_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'schoolInfo' in data and 'row' in data['schoolInfo'][1]:
            return pd.DataFrame(data['schoolInfo'][1]['row'])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"데이터를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return pd.DataFrame()

def fetch_meal_info(atpt_ofcdc_sc_code, sd_schul_code, date=None):
    """
    NEIS API에서 급식 정보를 가져옵니다
    """
    if date is None:
        date = datetime.now().strftime("%Y%m%d")
        
    params = {
        'KEY': NEIS_API_KEY,
        'Type': 'json',
        'ATPT_OFCDC_SC_CODE': atpt_ofcdc_sc_code,  # 시도교육청 코드
        'SD_SCHUL_CODE': sd_schul_code,            # 학교 코드
        'MLSV_YMD': date
    }

    try:
        response = requests.get(MEAL_INFO_URL, params=params)
        response.raise_for_status()
        data = response.json()
        
        if 'mealServiceDietInfo' in data and 'row' in data['mealServiceDietInfo'][1]:
            return pd.DataFrame(data['mealServiceDietInfo'][1]['row'])
        return pd.DataFrame()
    except Exception as e:
        st.error(f"급식 정보를 가져오는 중 오류가 발생했습니다: {str(e)}")
        return pd.DataFrame()

# Streamlit UI
st.title("🏫 학교 정보 및 급식 검색")
st.write("학교 정보와 급식 정보를 검색합니다")

# 탭 생성
tab1, tab2 = st.tabs(["학교 정보 검색", "급식 정보 검색"])

# 학교 정보 검색 탭
with tab1:
    st.header("학교 정보 검색")
    
    # 검색 필터
    col1, col2, col3 = st.columns(3)
    with col1:
        school_name = st.text_input("학교명")
    with col2:
        school_type = st.selectbox(
            "학교 종류",
            ["", "초등학교", "중학교", "고등학교", "특수학교"]
        )
    with col3:
        region = st.text_input("지역 (시/도)")
    
    # 검색 버튼
    if st.button("학교 검색", key="school_search_button"):
        if not NEIS_API_KEY:
            st.error(".env 파일에 NEIS_API_KEY를 설정해주세요")
        else:
            with st.spinner("학교 정보를 가져오는 중..."):
                df = fetch_school_info(school_name, school_type, region)
                
                if not df.empty:
                    st.success(f"{len(df)}개의 학교를 찾았습니다")
                    st.dataframe(df)
                    
                    # 학교 정보를 세션 상태에 저장
                    st.session_state.schools_df = df
                else:
                    st.info("검색 조건에 맞는 학교가 없습니다")

# 급식 정보 검색 탭
with tab2:
    st.header("급식 정보 검색")
    
    # 학교 선택
    if 'schools_df' in st.session_state and not st.session_state.schools_df.empty:
        selected_school = st.selectbox(
            "급식 정보를 확인할 학교를 선택하세요",
            st.session_state.schools_df['SCHUL_NM'].tolist()
        )
        
        if selected_school:
            selected_school_info = st.session_state.schools_df[st.session_state.schools_df['SCHUL_NM'] == selected_school].iloc[0]
            
            # 날짜 선택
            meal_date = st.date_input(
                "급식 날짜 선택",
                datetime.now()
            )
            
            # 급식 정보 조회 버튼
            if st.button("급식 정보 조회", key="meal_search_button"):
                with st.spinner("급식 정보를 가져오는 중..."):
                    meal_df = fetch_meal_info(
                        selected_school_info['ATPT_OFCDC_SC_CODE'],
                        selected_school_info['SD_SCHUL_CODE'],
                        meal_date.strftime("%Y%m%d")
                    )
                    
                    if not meal_df.empty:
                        st.success("급식 정보를 찾았습니다")
                        # 급식 정보 표시
                        for _, meal in meal_df.iterrows():
                            st.subheader(f"{meal['MLSV_YMD']} 급식 메뉴")
                            st.write(meal['DDISH_NM'].replace("<br/>", "\n"))
                    else:
                        st.info("해당 날짜의 급식 정보가 없습니다")
    else:
        st.info("먼저 '학교 정보 검색' 탭에서 학교를 검색해주세요")

# Instructions
with st.expander("사용 방법"):
    st.markdown("""
    1. '학교 정보 검색' 탭에서 학교를 검색하세요:
       - 학교명 입력
       - 학교 종류 선택
       - 지역(시/도) 입력
    2. 검색 버튼을 클릭하여 결과를 가져오세요
    3. '급식 정보 검색' 탭으로 이동하세요
    4. 학교 목록에서 급식 정보를 확인할 학교를 선택하세요
    5. 날짜를 선택하고 급식 정보 조회 버튼을 클릭하세요
    """)

# Footer
st.markdown("---")
st.markdown("데이터 제공: NEIS(교육정보개방포털)") 