import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Test Đọc Đề Hóa - Sinh", page_icon="🧪")

st.title("🧪 Thử nghiệm AI Đọc & Giải Đề (Image-to-Text)")
st.markdown("Tải ảnh đề thi lên đây để kiểm tra xem AI nhận diện chữ và giải bài có mượt không nhé!")

# Nhập API Key
api_key = st.text_input("Nhập Google Gemini API Key của bạn:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    # Lấy danh sách model hợp lệ từ API Key của bạn
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
                
        if not available_models:
            st.error("API Key của bạn không có mô hình nào hỗ trợ nhận diện (generateContent).")
        else:
            model_name = st.selectbox("Chọn mô hình AI (được hỗ trợ bởi API Key của bạn):", available_models)
            
            # Khởi tạo model dựa trên lựa chọn
            # Cắt chữ 'models/' nếu có ở đầu vì genai.GenerativeModel tự xử lý
            clean_model_name = model_name.replace("models/", "")
            model = genai.GenerativeModel(clean_model_name)
    except Exception as e:
        st.error(f"Lỗi khi kiểm tra API Key: {e}")
        model = None

    if model:
        uploaded_file = st.file_uploader("Chọn một ảnh đề thi...", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            # Hiển thị ảnh
            image = Image.open(uploaded_file)
            st.image(image, caption='Ảnh đề thi đã tải lên', use_container_width=True)

            if st.button("🚀 Bắt đầu nhận diện & Giải"):
                with st.spinner("AI đang đọc và xử lý đề thi..."):
                    try:
                        # Prompt hướng dẫn AI xử lý
                        prompt = """
                        Bạn là một gia sư Hóa học và Sinh học xuất sắc.
                        Hãy đọc đề thi trong ảnh đính kèm. 
                        1. Trích xuất toàn bộ nội dung câu hỏi từ ảnh thành văn bản rõ ràng (giữ nguyên định dạng, công thức).
                        2. Cung cấp đáp án và lời giải chi tiết cho từng câu hỏi ở bên dưới phần trích xuất.
                        """
                        
                        # Gọi API của Google Gemini
                        response = model.generate_content([prompt, image])
                        
                        st.success("Hoàn thành!")
                        st.markdown("### 📝 Kết quả trích xuất & Giải chi tiết:")
                        st.write(response.text)
                    except Exception as e:
                        st.error(f"Đã xảy ra lỗi: {e}")
else:
    st.info("Vui lòng nhập API Key để bắt đầu.")
