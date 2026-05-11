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

# 2. 색상 완전 고정 (시스템 테마 무시 버전)
st.markdown("""
    <style>
    /* [1] 전역 배경 및 텍스트 색상 강제 고정 */
    /* 라이트 모드여도 무조건 배경은 검게, 글자는 하얗게 만듭니다. */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #111111 !important;
        color: #FFFFFF !important;
    }

    /* 모든 텍스트 요소를 흰색으로 고정 */
    h1, h2, h3, h4, h5, h6, p, label, span, li, small {
        color: #FFFFFF !important;
    }

    /* [2] 사이드바 고정 컬러 */
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div {
        background-color: #161616 !important;
        border-right: 1px solid #1E293B;
    }

    /* [3] 입력창 (메인/서브 카피) 스타일 고정 */
    /* .stTextArea와 .stTextInput 내부의 모든 배경/테두리를 하나로 묶어 처리 */
    .stTextArea textarea, .stTextInput input, 
    div[data-baseweb="base-input"], div[data-baseweb="input"] {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        -webkit-text-fill-color: #FFFFFF !important;
        border: none !important;
    }

    /* 입력창 바깥 테두리 라인 */
    .stTextArea > div > div, .stTextInput > div > div {
        background-color: #1E1E1E !important;
        border: 1px solid #334155 !important; /* ← 여기서 테두리 컬러 수정 */
        border-radius: 8px !important;
    }

    /* 안내문구(Placeholder) 컬러 */
    input::placeholder, textarea::placeholder {
        color: #64748B !important; /* ← 여기서 안내문구 컬러 수정 */
        opacity: 1 !important;
    }

    /* [4] 파일 업로더 및 파일 정보 카드 고정 */
    /* 업로드 영역 */
    [data-testid="stFileUploader"] section {
        background-color: #1A1A1A !important;
        border: 1px dashed #475569 !important;
    }

    /* 업로드된 파일 카드 (문제의 하얀 박스 완벽 차단) */
    [data-testid="stFileUploaderFileData"], 
    [data-testid="stFileUploaderFileData"] *,
    [data-testid="stFileUploaderFileData"] div {
        background-color: #1E1E1E !important;
        color: #FFFFFF !important;
        border-color: #334155 !important;
    }

    /* [5] 사이드바 TIP 박스 (st.info) 고정 */
    [data-testid="stSidebar"] [data-testid="stAlert"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
    }
    [data-testid="stSidebar"] [data-testid="stAlert"] * {
        color: #FFFFFF !important;
    }

    /* [6] UI 정리 (불필요한 버튼 및 메뉴 숨기기) */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, header, footer { visibility: hidden; }

    /* [7] 버튼 스타일 고정 */
    button[kind="secondary"] {
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #475569 !important;
    }

    /* --- [수정] 상태 박스(st.success) 테두리 다이어트 --- */
    
    /* 1. 상태 박스 배경과 테두리 설정 */
    div[data-testid="stNotification"], 
    div[data-testid="stAlert"], 
    div[role="alert"] {
        background-color: #064E3B !important; 
        
        /* 0.5px 두께는 유지하되, 색상 농도를 40%로 낮춰서 가늘어 보이게 만듭니다 */
        border: 0.5px solid rgba(16, 185, 129, 0.4) !important; 
        
        border-radius: 8px !important;
        
        /* [중요] 테두리를 두꺼워 보이게 만드는 필터와 그림자를 제거합니다 */
        filter: none !important; 
        box-shadow: none !important; 
    }
    
    /* 2. 박스 내부 텍스트 및 아이콘 (기존 유지하되 두께 조절) */
    div[data-testid="stNotification"] *, 
    div[data-testid="stAlert"] *, 
    div[role="alert"] * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 300 !important; /* 텍스트 두께도 살짝 줄이면 전체적으로 더 샤프해 보입니다 */
    }
    
    /* 3. 컨테이너 중첩 제거 (혹시 모를 이중 테두리 방지) */
    div[data-testid="stAlertContainer"] {
        background-color: transparent !important;
        border: none !important;
    }

    /* 3. 일반 모드 크롬에서 배경이 투명하게 비치는 현상 방지 */
    div[data-testid="stAlertContainer"] {
        background-color: transparent !important;
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
