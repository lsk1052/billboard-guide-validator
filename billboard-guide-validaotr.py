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

# 2. 스타일링 (기존 다크모드 유지)
st.markdown("""
    <style>
    .stApp { background-color: #111111; color: #F2F2F2; }
    .check-pass { font-size: 1.2rem; font-weight: 800; color: #00E676; }
    .check-fail { font-size: 1.2rem; font-weight: 800; color: #FF5252; }
    .status-text { font-size: 0.85rem; color: #AAAAAA; }
    </style>
    """, unsafe_allow_html=True)

# 3. 품질 분석 함수 (기존 로직 활용)
def evaluate_quality(pil_image):
    img_array = np.array(pil_image.convert("RGB"))
    img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    
    # 노이즈 분석 (FFT)
    f = np.fft.fft2(gray)
    fshift = np.fft.fftshift(f)
    p_raw = np.mean(20 * np.log(np.abs(fshift) + 1))
    purity_score = max(0, min(100, 100 - (p_raw - 175.0) * 30)) 
    
    # 선명도 분석 (Laplacian)
    lap_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    clarity_score = max(0, min(100, lap_var / 8)) 
    
    return (purity_score * 0.7) + (clarity_score * 0.3)

# 4. 빌보드 가이드 레이어 합성 함수
def apply_billboard_overlay(base_image, main_txt, sub_txt):
    width, height = base_image.size
    canvas = base_image.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # A. 상단 헤더 이미지 로드 및 합성
    header_path = "header.png"
    if os.path.exists(header_path):
        header_img = Image.open(header_path).convert("RGBA")
        # 이미지 너비에 맞춰 헤더 리사이즈
        h_ratio = width / header_img.width
        new_h_size = (width, int(header_img.height * h_ratio))
        header_resized = header_img.resize(new_h_size, Image.Resampling.LANCZOS)
        canvas.paste(header_resized, (0, 0), header_resized)
    
    # B. 텍스트 설정 (폰트 파일이 없을 경우 대비 기본 폰트 사용)
    try:
        # 한글 폰트 경로 (사용자 환경에 맞춰 수정 필요)
        font_main = ImageFont.truetype("AppleGothic.ttf", int(width * 0.05))
        font_sub = ImageFont.truetype("AppleGothic.ttf", int(width * 0.03))
        font_fixed = ImageFont.truetype("AppleGothic.ttf", int(width * 0.025))
    except:
        font_main = font_sub = font_fixed = ImageFont.load_default()

    # C. 가변 텍스트 (Main/Sub)
    draw.text((width * 0.05, height * 0.75), main_txt, font=font_main, fill=(255, 255, 255, 255))
    draw.text((width * 0.05, height * 0.83), sub_txt, font=font_sub, fill=(255, 255, 255, 200))
    
    # D. 고정 UI (AD / Pagination)
    draw.text((width * 0.05, height * 0.92), "AD", font=font_fixed, fill=(255, 255, 255, 120))
    draw.text((width * 0.85, height * 0.92), "1 / 15 +", font=font_fixed, fill=(255, 255, 255, 200))
    
    return Image.alpha_composite(canvas, overlay).convert("RGB")

# 5. 메인 UI 구성
st.title("Billboard 가이드 검증기")
st.caption("헤더 간섭 및 텍스트 가독성 실시간 검수")

with st.sidebar:
    st.header("📝 텍스트 편집")
    input_main = st.text_area("메인 카피 (Main)", "아워코모스\n일상 속에 스며드는 디테일")
    input_sub = st.text_input("서브 카피 (Sub)", "스토어 쿠폰 + 카드할인 혜택")
    
    st.divider()
    st.markdown("### 📏 권장 규격\n- **사이즈**: 1080x1350px\n- **용량**: 500KB 미만")

uploaded_file = st.file_uploader("이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGB")
    w, h = image.size
    file_kb = uploaded_file.size / 1024
    
    # 분석
    q_score = evaluate_quality(image)
    
    # 결과 요약
    cols = st.columns(3)
    with cols[0]:
        status = "check-pass" if (w, h) == (1080, 1350) else "check-fail"
        st.markdown(f'<div class="{status}">규격 체크</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-text">{w}x{h}px</div>', unsafe_allow_html=True)
    with cols[1]:
        status = "check-pass" if file_kb <= 500 else "check-fail"
        st.markdown(f'<div class="{status}">용량 체크</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-text">{file_kb:.1f} KB</div>', unsafe_allow_html=True)
    with cols[2]:
        status = "check-pass" if q_score >= 60 else "check-fail"
        st.markdown(f'<div class="{status}">화질 점수</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-text">{q_score:.0f}점 / 100</div>', unsafe_allow_html=True)

    st.divider()
    
    # 가이드 합성 프리뷰
    with st.spinner("가이드라인을 적용 중..."):
        preview_img = apply_billboard_overlay(image, input_main, input_sub)
        st.image(preview_img, caption="빌보드 실제 적용 시뮬레이션", use_container_width=True)