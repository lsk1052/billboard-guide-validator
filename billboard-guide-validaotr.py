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

# 4. 빌보드 가이드 레이어 합성 함수 (750x1000 최적화)
def apply_billboard_overlay(base_image, main_txt, sub_txt):
    # 강제로 750x1000으로 리사이즈 (검수 편의성)
    base_image = base_image.resize((750, 1000), Image.Resampling.LANCZOS)
    width, height = base_image.size
    
    canvas = base_image.convert("RGBA")
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # A. 상단 헤더 이미지 로드
    header_path = "header-home.png"
    if os.path.exists(header_path):
        header_img = Image.open(header_path).convert("RGBA")
        h_ratio = width / header_img.width
        new_h_size = (width, int(header_img.height * h_ratio))
        header_resized = header_img.resize(new_h_size, Image.Resampling.LANCZOS)
        canvas.paste(header_resized, (0, 0), header_resized)
    
    # B. 폰트 설정
    try:
        # 시스템에 설치된 폰트나 업로드된 폰트 사용 (NanumSquare 등 추천)
        font_main = ImageFont.truetype("Pretendard-Bold.otf", 44)
        font_sub = ImageFont.truetype("Pretendard-Regular.otf", 28)
        font_fixed = ImageFont.truetype("Pretendard-Medium.otf", 20)
    except:
        font_main = font_sub = font_fixed = ImageFont.load_default()

    # C. 하단 그라데이션 (가독성용 - 선택사항)
    # 가독성을 위해 하단에 살짝 어두운 딤을 깔아줍니다.
    dim = Image.new("RGBA", (width, 300), (0, 0, 0, 0))
    dim_draw = ImageDraw.Draw(dim)
    for i in range(300):
        alpha = int((i / 300) * 100)
        dim_draw.line([(0, i), (width, i)], fill=(0, 0, 0, alpha))
    canvas.paste(dim.transpose(Image.FLIP_TOP_BOTTOM), (0, 700), dim.transpose(Image.FLIP_TOP_BOTTOM))

    # D. 가변 텍스트 (Main/Sub) - 롯데 ON 스타일 배치
    # 메인 카피 (행간 처리를 위해 split)
    y_pos = 780
    for line in main_txt.split('\n'):
        draw.text((40, y_pos), line, font=font_main, fill=(255, 255, 255, 255))
        y_pos += 55
    
    # 서브 카피
    draw.text((40, 890), sub_txt, font=font_sub, fill=(255, 255, 255, 230))
    
    # E. 고정 UI (AD / Pagination)
    # AD 마크 (좌측 최하단)
    draw.text((40, 940), "AD", font=font_fixed, fill=(255, 255, 255, 120))
    # 페이지네이션 (우측 최하단)
    draw.text((width - 120, 940), "1 / 15 +", font=font_fixed, fill=(255, 255, 255, 200))
    
    return Image.alpha_composite(canvas, overlay).convert("RGB")

# 5. 메인 UI 구성
st.title("Billboard Guide Validator")
st.caption("750x1000 표준 규격 및 UI 간섭 실시간 검수 도구")

with st.sidebar:
    st.header("📝 소재 편집")
    input_main = st.text_area("메인 카피 (Main)", "아워코모스\n일상 속에 스며드는 디테일")
    input_sub = st.text_input("서브 카피 (Sub)", "스토어 쿠폰 + 카드할인 혜택")
    
    st.divider()
    st.markdown("### 📏 검수 가이드라인")
    st.info("- **규격**: 750x1000px\n- **용량**: 500KB 이하\n- **필수**: 하단 AD 마크 시인성 확보")

uploaded_file = st.file_uploader("검수할 빌보드 이미지를 업로드하세요", type=["png", "jpg", "jpeg"])

if uploaded_file:
    # 이미지 로드
    raw_image = Image.open(uploaded_file).convert("RGB")
    actual_w, actual_h = raw_image.size
    file_kb = uploaded_file.size / 1024
    
    # 품질 분석
    with st.spinner("이미지 품질 분석 중..."):
        q_score = evaluate_quality(raw_image)
    
    # 상단 결과 요약 대시보드
    cols = st.columns(3)
    with cols[0]:
        status = "check-pass" if (actual_w, actual_h) == (750, 1000) else "check-fail"
        st.markdown(f'<div class="{status}">{"✅ 규격 통과" if status == "check-pass" else "❌ 규격 오류"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-text">현재: {actual_w}x{actual_h}px</div>', unsafe_allow_html=True)
    with cols[1]:
        status = "check-pass" if file_kb <= 500 else "check-fail"
        st.markdown(f'<div class="{status}">{"✅ 용량 적정" if status == "check-pass" else "❌ 용량 초과"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-text">{file_kb:.1f} KB</div>', unsafe_allow_html=True)
    with cols[2]:
        status = "check-pass" if q_score >= 60 else "check-fail"
        st.markdown(f'<div class="{status}">{"✅ 화질 양호" if status == "check-pass" else "⚠️ 화질 저하"}</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="status-text">품질 지수: {q_score:.0f}점</div>', unsafe_allow_html=True)

    st.divider()
    
    # [핵심] 실시간 미리보기 화면
    st.subheader("🖼️ 가이드라인 적용 미리보기")
    with st.spinner("UI 레이어를 합성하는 중입니다..."):
        # UI 합성
        preview_img = apply_billboard_overlay(raw_image, input_main, input_sub)
        
        # 화면에 출력
        st.image(preview_img, caption="빌보드 UI 시뮬레이션 결과 (750x1000)", width=750)
        
    st.success("💡 팁: 사이드바에서 텍스트를 수정하면 미리보기에 즉시 반영됩니다.")
