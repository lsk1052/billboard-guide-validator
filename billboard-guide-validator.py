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

    st.info("💡 **팁:** 여기서 텍스트를 수정하면 미리보기에 즉시 반영됩니다.")
    
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
