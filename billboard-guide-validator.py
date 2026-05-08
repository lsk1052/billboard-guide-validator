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

# 4. 빌보드 가이드 레이어 합성 함수 (750x1000 및 이미지 UI 최적화)
def apply_billboard_overlay(base_image, main_txt, sub_txt):
    # 강제로 750x1000으로 리사이즈하여 검수 규격 통일
    base_image = base_image.resize((750, 1000), Image.Resampling.LANCZOS)
    width, height = base_image.size
    
    canvas = base_image.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # A. 상단 헤더 이미지 로드 (이곳에 하단 UI 이미지 로직도 추후 추가 가능)
    header_path = "header-home.png"
    if os.path.exists(header_path):
        header_img = Image.open(header_path).convert("RGBA")
        h_ratio = width / header_img.width
        new_h_size = (width, int(header_img.height * h_ratio))
        header_resized = header_img.resize(new_h_size, Image.Resampling.LANCZOS)
        canvas.paste(header_resized, (0, 0), header_resized)
    
    # B. 폰트 설정
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        main_font_path = os.path.join(current_dir, "Pretendard-SemiBold.otf")
        sub_font_path = os.path.join(current_dir, "Pretendard-Medium.otf")
        
        font_main = ImageFont.truetype(main_font_path, 44) 
        font_sub = ImageFont.truetype(sub_font_path, 28)
        # font_fixed는 이미지 UI로 대체하므로 삭제했습니다.
        
    except Exception as e:
        st.error(f"폰트 로드 실패: {e}")
        font_main = font_sub = ImageFont.load_default()

    # --- [수치 반영] 레이아웃 설정 변수 ---
    margin_x = 48         # 좌측 여백 (요청하신 48 반영)
    main_y_start = 732    # 메인 카피 시작 높이 (요청하신 732 반영)
    line_height_main = 55 # 메인 카피 행간 (Figma 125% 반영)
    gap_main_sub = 30      # 메인/서브 간격 (요청하신 8 반영)
    # ----------------------------------

    # D. 가변 텍스트 그리기
    current_y = main_y_start
    lines = main_txt.split('\n')
    for line in lines:
        draw.text((margin_x, current_y), line, font=font_main, fill=(255, 255, 255, 255))
        current_y += line_height_main 
    
    # 서브 카피 위치 계산
    # 보정값 40은 폰트의 상승 값(Ascent)을 고려한 수치입니다.
    sub_y = current_y - line_height_main + gap_main_sub + 40 
    draw.text((margin_x, sub_y), sub_txt, font=font_sub, fill=(255, 255, 255, 230))
    
    # E. 하단 UI 영역 (텍스트 로직 삭제됨)
    # 이미 이미지로 처리하시기로 했으므로, header-home.png처럼 
    # 별도의 footer 이미지를 제작해 paste 하시면 더욱 완벽해집니다.
    
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
    
    # [요청사항] 좌우 2컬럼 배치
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏠 홈 헤더 버전")
        # 홈 헤더 적용 (header-home.png)
        preview_home = apply_billboard_overlay(raw_image, input_main, input_sub, "header-home.png")
        st.image(preview_home, use_container_width=True, caption="Home Header 적용 결과")
        
    with col2:
        st.markdown("#### 📱 버티컬 헤더 버전")
        # 버티컬 헤더 적용 (header-vertical.png)
        preview_vertical = apply_billboard_overlay(raw_image, input_main, input_sub, "header-vertical.png")
        st.image(preview_vertical, use_container_width=True, caption="Vertical Header 적용 결과")

    st.divider()
    
    # [핵심] 실시간 미리보기 화면
    st.subheader("🖼️ 가이드라인 적용 미리보기")
    with st.spinner("UI 레이어를 합성하는 중입니다..."):
        # UI 합성
        preview_img = apply_billboard_overlay(raw_image, input_main, input_sub)
        
        # 화면에 출력
        st.image(preview_img, caption="빌보드 UI 시뮬레이션 결과 (750x1000)", width=750)
        
    st.success("💡 팁: 사이드바에서 텍스트를 수정하면 미리보기에 즉시 반영됩니다.")
