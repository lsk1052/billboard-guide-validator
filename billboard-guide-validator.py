import io
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

# 2. 색상 및 UI 스타일 완전 고정 (Success/Error 분리 버전)
st.markdown("""
    <style>
    /* [1] 전역 배경 및 텍스트 색상 */
    .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        background-color: #111111 !important;
        color: #FFFFFF !important;
    }

    h1, h2, h3, h4, h5, h6, p, label, span, li, small {
        color: #FFFFFF !important;
    }

    /* [2] 사이드바 디자인 */
    [data-testid="stSidebar"] {
        background-color: #161616 !important;
        border-right: 1px solid #1E293B;
    }

    /* [3] 입력창(Focus 시 Red) */
    [data-baseweb="textarea"], [data-baseweb="input"] {
        background-color: #1E1E1E !important;
        border: 1px solid #334155 !important;
        border-radius: 8px !important;
    }
    [data-baseweb="textarea"]:focus-within, [data-baseweb="input"]:focus-within {
        border: 1px solid #FF4B4B !important;
        box-shadow: none !important;
    }

    /* --- [핵심 수정] 상태 박스(Alert) 컬러 시스템 분리 --- */
    
    /* 1. 공통 초기화 (기존의 강제 초록색 설정을 제거) */
    div[data-testid="stNotification"], div[data-testid="stAlert"], div[role="alert"] {
        background-color: transparent !important; 
        border-radius: 8px !important;
        filter: none !important;
        box-shadow: none !important;
    }

    /* 2. Success (초록 - 적합) : 아이콘 라벨이 Success인 경우 */
    div[data-testid="stNotification"]:has(svg[aria-label="Success"]),
    div[role="alert"]:has(svg[aria-label="Success"]) {
        background-color: #064E3B !important; 
        border: 1px solid rgba(16, 185, 129, 0.4) !important;
    }

    /* 3. Error & Warning 통합 (빨강 - 부적합) : 아이콘 라벨이 Error 또는 Warning인 경우 */
    div[data-testid="stNotification"]:has(svg[aria-label="Error"]),
    div[data-testid="stNotification"]:has(svg[aria-label="Warning"]),
    div[role="alert"]:has(svg[aria-label="Error"]),
    div[role="alert"]:has(svg[aria-label="Warning"]) {
        background-color: #7F1D1D !important; 
        border: 1px solid rgba(239, 68, 68, 0.4) !important;
    }

    /* 4. 내부 텍스트 및 아이콘 화이트 고정 */
    div[data-testid="stNotification"] *, div[role="alert"] * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
    }

    /* [4] 이미지 및 버튼 레이아웃 */
    .stImage { display: flex; justify-content: center; }
    div.stDownloadButton { display: flex; justify-content: center; }
    div.stDownloadButton > button {
        width: 750px !important;
        background-color: #262730 !important;
        color: #FFFFFF !important;
        border: 1px solid #475569 !important;
    }

    /* [5] 기타 UI 정리 */
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"] { display: none !important; }
    #MainMenu, header, footer { visibility: hidden; }
    .block-container { padding-top: 4rem !important; }
    [data-testid="stSidebar"] hr { border-color: #475569 !important; opacity: 0.8; }
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
    
    st.header("📍 미리보기 설정")
    # 라디오 버튼 추가
    view_mode = st.radio(
        "확인할 빌보드 유형을 선택하세요",
        ["홈 빌보드", "버티컬 빌보드"]
    )
    
    st.divider()
    # ...
    
    st.header("🖼️ 소재 편집")

    st.info("💡 아래 입력창의 텍스트를 수정하면 미리보기에 즉시 반영됩니다.")
    
    input_main = st.text_area("메인 카피 입력", value="평범한 오늘을 특별하게\n만드는 브랜드")
    input_sub = st.text_input("서브 카피 입력", value="스토어 쿠폰 + 카드할인 혜택")
    
    st.divider()
    st.markdown("### 📋 검수 가이드라인")
    st.caption("- 규격: 750x1000px\n- 용량: 400KB 이하\n- 필수: 헤더 영역에 모델 얼굴 혹은 주요 제품이 겹치지 않게 해주세요.")

uploaded_file = st.file_uploader("검수할 빌보드 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

# --- 메인 화면 미리보기 영역 ---
# --- 메인 화면 검수 로직 (2단계 피드백) ---
if uploaded_file is not None:
    file_bytes = uploaded_file.getvalue()
    raw_image = Image.open(uploaded_file)
    width, height = raw_image.size
    file_size_kb = len(file_bytes) / 1024

    st.divider()
    
    v_col1, v_col2, v_col3 = st.columns(3)
    
    with v_col1:
        if width == 750 and height == 1000:
            st.success(f"✅ 규격 적합\n{width}x{height}px")
        else:
            st.error(f"🚨 규격 부적합\n현재: {width}x{height} (권장: 750x1000)")
            
    with v_col2:
        if file_size_kb <= 500:
            st.success(f"✅ 용량 적합\n{file_size_kb:.1f} KB")
        else:
            st.error(f"🚨 용량 초과\n현재: {file_size_kb:.1f} KB (제한: 500KB)")
            
    with v_col3:
        final_score = evaluate_quality(raw_image)
        # 화질도 70점 기준 합격/불합격으로 엄격하게 분리
        if final_score >= 70:
            st.success(f"✅ 화질 적합\n품질 지수: {final_score:.1f}점")
        else:
            st.error(f"🚨 화질 부적합\n품질 지수: {final_score:.1f}점 (재촬영 권장)")

    st.divider()
    
    # --- [미리보기] 선택한 모드에 따라 중앙 배치 ---
    # 비율을 [1.2, 3, 1.2] 정도로 조정하면 750px 이미지가 중앙에 더 안정적으로 배치됩니다.
    m_col1, m_col2, m_col3 = st.columns([1.2, 3, 1.2])

    with m_col2:
        st.subheader(f"🔍 {view_mode} 미리보기")
        
        if view_mode == "홈 빌보드":
            preview_home = apply_billboard_overlay(raw_image, input_main, input_sub, "header-home.png")
            
            # width=750 유지 (CSS가 이를 중앙으로 밀어줍니다)
            st.image(preview_home, width=750, caption="Home Header 적용 결과 (750x1000)")
            
            buf = io.BytesIO()
            preview_home.save(buf, format="PNG")
            byte_im = buf.getvalue()
            
            st.download_button(
                label="🏠 홈 버전 다운로드",
                data=byte_im,
                file_name="billboard_home_preview.png",
                mime="image/png"
                # use_container_width=True는 지워도 됩니다. CSS에서 750px을 강제합니다.
            )

        else:  # "버티컬 빌보드" 선택 시
            preview_vertical = apply_billboard_overlay(raw_image, input_main, input_sub, "header-vertical.png")
            
            st.image(preview_vertical, width=750, caption="Vertical Header 적용 결과 (750x1000)")
            
            buf_v = io.BytesIO()
            preview_vertical.save(buf_v, format="PNG")
            byte_im_v = buf_v.getvalue()
            
            st.download_button(
                label="📱 버티컬 버전 다운로드",
                data=byte_im_v,
                file_name="billboard_vertical_preview.png",
                mime="image/png"
            )
