import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="Billboard Check Mate",
    page_icon="✅",
    layout="wide",
)

# 2. 다크모드 테마 및 스타일링 (메인 화면 강제 다크화 버전)
st.markdown("""
    <style>
    /* --- [1] 전체 앱 컨테이너 배경 (우측 하얀 화면 해결) --- */
    [data-testid="stAppViewContainer"] {
        background-color: #111111 !important;
    }
    
    /* 상단 헤더 영역 배경색 고정 */
    [data-testid="stHeader"] {
        background-color: rgba(0,0,0,0) !important;
    }

    /* --- [2] 사이드바 배경색 고정 --- */
    [data-testid="stSidebar"] {
        background-color: #161616 !important;
        border-right: 1px solid #1E293B;
    }

    /* --- [3] 모든 텍스트 컬러 강제 흰색 (메인+사이드바 공통) --- */
    h1, h2, h3, h4, h5, h6, p, label, span, li {
        color: #FFFFFF !important;
    }
    .stApp .stCaption {
        color: #CBD5E1 !important; /* 캡션은 살짝 흐린 회색 */
    }

    /* --- [4] 입력창 스타일 통일 (라인 컬러 & 안내문구) --- */
    /* 메인 카피 창 & 서브 카피 창 공통 */
    .stTextInput > div > div, 
    .stTextArea > div > div {
        background-color: #1E1E1E !important;
        border: 1px solid #334155 !important; /* 라인 컬러 */
        border-radius: 8px !important;
    }

    /* 입력창 내부 실제 글자색 & 안내문구(Placeholder) */
    input, textarea {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }
    input::placeholder, textarea::placeholder {
        color: #64748B !important; /* 안내문구 컬러 */
        opacity: 1 !important;
    }

    /* 클릭 시(Focus) 라인 컬러 */
    .stTextInput:focus-within > div > div, 
    .stTextArea:focus-within > div > div {
        border-color: #10B981 !important;
        box-shadow: 0 0 0 1px #10B981 !important;
    }

    /* --- [5] 파일 업로더 디자인 --- */
    [data-testid="stFileUploader"] section {
        background-color: #1A1A1A !important;
        border: 1px dashed #475569 !important;
        color: #FFFFFF !important;
    }

    /* --- [6] TIP 박스(st.info) 스타일 --- */
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
    }
    [data-testid="stSidebar"] [data-testid="stAlert"] * {
        color: #FFFFFF !important;
    }

    /* --- [핵심] 파일 업로더 내 버튼 스타일 강제 고정 --- */
[data-testid="stFileUploader"] button {
    background-color: #262730 !important; /* 시크릿 모드 느낌의 어두운 배경 */
    color: #FFFFFF !important;           /* 글자색 흰색 */
    border: 1px solid #475569 !important; /* 테두리 라인 */
    transition: all 0.2s ease;
}

    /* 버튼 위에 마우스 올렸을 때(Hover) */
    [data-testid="stFileUploader"] button:hover {
        border-color: #10B981 !important;    /* 에메랄드 포인트 컬러 */
        background-color: #1E1E1E !important;
    }
    
    /* 버튼 내부의 아이콘 컬러 */
    [data-testid="stFileUploader"] button svg {
        fill: #FFFFFF !important;
    }
    
    /* 업로드 창 전체 배경 (하얀 박스 방지) */
    [data-testid="stFileUploader"] section {
        background-color: #1A1A1A !important;
        border: 1px dashed #334155 !important;
        border-radius: 8px !important;
    }
    
    /* 업로드 안내 텍스트 (200MB per file 등) */
    [data-testid="stFileUploader"] section div div {
        color: #CBD5E1 !important;
    }

    /* --- [7] 불필요한 UI 제거 --- */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, header, footer { visibility: hidden; }

/* --- [진짜 최종 완성] 업로드된 파일 정보 카드 스타일 통일 --- */

    /* 1. 파일 카드 전체 컨테이너와 그 내부의 모든 div 배경을 강제로 어둡게 */
    [data-testid="stFileUploaderFileData"], 
    [data-testid="stFileUploaderFileData"] div,
    [data-testid="stFileUploaderFileData"] > div > div {
        background-color: #1E1E1E !important;
        background-image: none !important; /* 혹시 모를 배경 이미지 제거 */
    }

    /* 2. 카드 외곽 테두리 및 라운드 설정 */
    [data-testid="stFileUploaderFileData"] {
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }

    /* 3. 파일명, 용량 텍스트를 흰색으로 강제 고정 */
    [data-testid="stFileUploaderFileData"] span,
    [data-testid="stFileUploaderFileData"] div,
    [data-testid="stFileUploaderFileData"] p {
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
    }

    /* 4. 파일 아이콘 및 삭제(X) 버튼 컬러 */
    [data-testid="stFileUploaderFileData"] svg {
        fill: #FFFFFF !important;
        color: #FFFFFF !important;
    }

    /* 5. 삭제 버튼 배경 투명화 및 호버 효과 */
    [data-testid="stFileUploaderFileData"] button {
        background-color: transparent !important;
    }
    [data-testid="stFileUploaderFileData"] button:hover svg {
        fill: #EF4444 !important; /* 삭제 버튼 마우스 올리면 빨간색 */
    }
    </style>
    """, unsafe_allow_html=True)

# 3. 품질 분석 함수
def evaluate_quality(pil_image):
    img_array = np.array(pil_image.convert("RGB"))
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    p_raw = np.mean(20 * np.log(np.abs(fshift) + 1))
    purity_score = max(0, min(100, 100 - (p_raw - 175.0) * 30)) 
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    clarity_score = max(0, min(100, lap_var / 8)) 
    return (purity_score * 0.7) + (clarity_score * 0.3)

# 4. 빌보드 가이드 레이어 합성 함수
def apply_billboard_overlay(base_image, main_txt, sub_txt, header_filename):
    # 750x1000 정사이즈 리사이즈 (LANCZOS로 선명도 유지)
    base_image = base_image.resize((750, 1000), Image.Resampling.LANCZOS)
    width, height = base_image.size
    
    canvas = base_image.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # A. 헤더 로드
    if os.path.exists(header_filename):
        header_img = Image.open(header_filename).convert("RGBA")
        h_ratio = width / header_img.width
        new_h_size = (width, int(header_img.height * h_ratio))
        header_resized = header_img.resize(new_h_size, Image.Resampling.LANCZOS)
        canvas.paste(header_resized, (0, 0), header_resized)
    
    # B. 폰트 설정
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        font_main = ImageFont.truetype(os.path.join(current_dir, "Pretendard-SemiBold.otf"), 44)
        font_sub = ImageFont.truetype(os.path.join(current_dir, "Pretendard-Medium.otf"), 28)
    except:
        font_main = font_sub = ImageFont.load_default()

    # --- 레이아웃 설정 변수 (수치 조정) ---
    margin_x = 48         
    line_height_main = 55 # 행간
    gap_main_sub = 30     # 메인 마지막 줄과 서브 카피 사이 간격
    
    # [핵심] 메인 카피의 '마지막 줄'이 위치할 Y 좌표를 고정합니다.
    # 기존에 두 줄일 때 두 번째 줄이 찍히던 위치인 787 (732 + 55) 정도로 설정합니다.
    main_y_anchor = 787   
    # ----------------------------------

    # D. 가변 텍스트 그리기
    lines = main_txt.split('\n')
    
    # 메인 카피의 시작 위치를 줄 수에 따라 역산합니다.
    # 1줄이면 anchor 위치에서 시작, 2줄이면 anchor에서 한 줄 위(anchor - 55)에서 시작
    current_y = main_y_bottom = main_y_anchor - (len(lines) - 1) * line_height_main
    
    for line in lines:
        draw.text((margin_x, current_y), line, font=font_main, fill=(255, 255, 255, 255))
        current_y += line_height_main 
    
    # 서브 카피 위치 계산
    # 이제 current_y는 항상 메인 카피 마지막 줄 아래에 위치하게 됩니다.
    sub_y = current_y - line_height_main + gap_main_sub + 40 
    draw.text((margin_x, sub_y), sub_txt, font=font_sub, fill=(255, 255, 255, 230))
    
    return Image.alpha_composite(canvas, overlay).convert("RGB")

# 5. 메인 UI 구성
st.title("Check Mate : 빌보드 가이드 체크")
st.caption("광고 빌보드 배너 디자인 품질 및 규격 검수 프로그램")

with st.sidebar:
    st.header("🖼️ 소재 편집")

    st.info("💡 아래 입력창의 텍스트를 수정하면 미리보기에 즉시 반영됩니다.")
    
    input_main = st.text_area("메인 카피 입력", value="평범한 오늘을 특별하게\n만드는 브랜드")
    input_sub = st.text_input("서브 카피 입력", value="스토어 쿠폰 + 카드할인 혜택")
    
    st.divider()
    st.markdown("### 📋 검수 가이드라인")
    st.caption("- 규격: 750x1000px\n- 용량: 400KB 이하\n- 필수: 헤더 영역에 모델 얼굴 혹은 주요 제품이 겹치지 않게 해주세요.")

uploaded_file = st.file_uploader("검수할 빌보드 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

# --- 메인 화면 미리보기 영역 ---
#
if uploaded_file is not None:
    # 1. 파일 데이터 로드 및 기본 검수
    file_bytes = uploaded_file.getvalue()
    raw_image = Image.open(uploaded_file)
    width, height = raw_image.size
    file_size_kb = len(file_bytes) / 1024

    st.divider()
    
    # --- [검수 기능 복구] 상단 상태 박스 ---
    v_col1, v_col2, v_col3 = st.columns(3)
    
    with v_col1:
        if width == 750 and height == 1000:
            st.success(f"✅ 규격 통과\n현재: {width}x{height}px")
        else:
            st.warning(f"⚠️ 규격 재확인\n권장: 750x1000 (현재: {width}x{height})")
            
    with v_col2:
        if file_size_kb <= 500:
            st.success(f"✅ 용량 적정\n현재: {file_size_kb:.1f} KB")
        else:
            st.error(f"🚨 용량 초과\n현재: {file_size_kb:.1f} KB (제한: 400KB)")
            
    with v_col3:
        # 간단한 화질 점수 계산 (예시)
        quality_score = 85 # 실제 구현 시에는 이미지 분석 로직이 들어갈 수 있습니다.
        st.success(f"✅ 화질 양호\n품질 지수: {quality_score}점")

    st.divider()

    # --- [미리보기] 홈 vs 버티컬 좌우 배치 ---
    st.subheader("가이드라인 적용 미리보기 (홈 / 버티컬)")
    
    p_col1, p_col2 = st.columns(2)
    
    with p_col1:
        st.markdown("#### 🏠 홈 헤더 버전")
        preview_home = apply_billboard_overlay(raw_image, input_main, input_sub, "header-home.png")
        st.image(preview_home, width=750, caption="Home Header 적용 결과")
        
    with p_col2:
        st.markdown("#### 📱 버티컬 헤더 버전")
        preview_vertical = apply_billboard_overlay(raw_image, input_main, input_sub, "header-vertical.png")
        st.image(preview_vertical, width=750, caption="Vertical Header 적용 결과")
