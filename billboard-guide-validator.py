import streamlit as st
from PIL import Image, ImageDraw, ImageFont
import cv2
import numpy as np
import os

# 1. 페이지 설정
st.set_page_config(
    page_title="Billboard Check Mate",
    page_icon="🖼️",
    layout="wide",
)

# 2. 다크모드 테마 및 스타일링
st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #F8FAFC; }
    .check-pass { font-size: 1.2rem; font-weight: 800; color: #10B981; }
    .check-fail { font-size: 1.2rem; font-weight: 800; color: #EF4444; }
    .status-text { font-size: 0.85rem; color: #94A3B8; }
    .stImage { border-radius: 12px; border: 1px solid #1E293B; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3); }
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

    # --- 레이아웃 설정 변수 (요청하신 수치 정확히 반영) ---
    margin_x = 48         
    main_y_start = 732    
    line_height_main = 55 
    gap_main_sub = 30     # [요청] 메인-서브 간격 30px 반영
    # -----------------------------------------------

    # D. 가변 텍스트 그리기
    current_y = main_y_start
    lines = main_txt.split('\n')
    for line in lines:
        draw.text((margin_x, current_y), line, font=font_main, fill=(255, 255, 255, 255))
        current_y += line_height_main 
    
    # 서브 카피 위치 (수치 계산 보정)
    # current_y는 마지막 줄을 그린 후 행간이 한 번 더해진 상태입니다.
    # 폰트의 실제 높이(약 44px)를 고려하여 30px 간격이 보이도록 조정했습니다.
    sub_y = current_y - line_height_main + gap_main_sub + 40
    draw.text((margin_x, sub_y), sub_txt, font=font_sub, fill=(255, 255, 255, 230))
    
    return Image.alpha_composite(canvas, overlay).convert("RGB")

# 5. 메인 UI 구성
st.title("Billboard Guide Validator")
st.caption("750x1000 표준 규격 및 UI 간섭 실시간 검수 도구")

with st.sidebar:
    st.header("🖼️ 소재 편집")
    input_main = st.text_area("메인 카피 입력", value="안녕하세요?\n디자인 시뮬레이션입니다.", help="줄바꿈을 사용하여 행간을 확인할 수 있습니다.")
    input_sub = st.text_input("서브 카피 입력", value="스토어 쿠폰 + 카드할인 혜택")
    
    # [요청사항] 팁 위치 이동
    st.info("💡 **팁:** 여기서 텍스트를 수정하면 우측 미리보기에 즉시 반영됩니다.")
    
    st.divider()
    st.markdown("### 📋 검수 가이드라인")
    st.caption("- 규격: 750x1000px\n- 용량: 500KB 이하\n- 필수: 하단 AD 마크 시인성 확보")

uploaded_file = st.file_uploader("검수할 빌보드 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

# --- 메인 화면 미리보기 영역 ---
if uploaded_file is not None:
    raw_image = Image.open(uploaded_file)
    
    st.divider()
    st.subheader("🖼️ 가이드라인 적용 미리보기 (홈 vs 버티컬)")
    
    # 좌우 2컬럼 배치
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 홈 헤더 버전")
        # [해결] 4번째 인자로 "header-home.png" 전달
        preview_home = apply_billboard_overlay(raw_image, input_main, input_sub, "header-home.png")
        # width=350을 설정하여 화면에 적절한 크기로 선명하게 출력
        st.image(preview_home, width=350, caption="Home Header (750x1000)")
        
    with col2:
        st.markdown("#### 📱 버티컬 헤더 버전")
        # [해결] 4번째 인자로 "header-vertical.png" 전달
        preview_vertical = apply_billboard_overlay(raw_image, input_main, input_sub, "header-vertical.png")
        st.image(preview_vertical, width=350, caption="Vertical Header (750x1000)")

    st.divider()
    
    # [핵심] 실시간 미리보기 화면
    st.subheader("🖼️ 가이드라인 적용 미리보기")
    with st.spinner("UI 레이어를 합성하는 중입니다..."):
        # UI 합성
        preview_img = apply_billboard_overlay(raw_image, input_main, input_sub)
        
        # 화면에 출력
        st.image(preview_img, caption="빌보드 UI 시뮬레이션 결과 (750x1000)", width=750)
        
    st.success("💡 팁: 사이드바에서 텍스트를 수정하면 미리보기에 즉시 반영됩니다.")
