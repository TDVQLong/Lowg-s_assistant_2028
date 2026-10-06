import streamlit as st
from openai import OpenAI
from PIL import Image

st.set_page_config(page_title="Test Đọc Đề Hóa - Sinh", page_icon="🧪")

st.title("🧪 Thử nghiệm AI Đọc & Giải Đề (Image-to-Text)")
st.markdown("Tải ảnh đề thi lên đây để kiểm tra xem AI nhận diện chữ và giải bài có mượt không nhé!")

# Nhập API Key
api_key = st.text_input("Nhập OpenRouter API Key của bạn:", type="password")

if api_key:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=api_key,
    )
    # Lấy danh sách model hợp lệ từ API Key của bạn
    available_models = []
    try:
        models = client.models.list()
        for m in models:
            available_models.append(m.id)
                
        if not available_models:
            st.error("Không tìm thấy mô hình nào từ OpenRouter.")
        else:
            model_name = st.selectbox("Chọn mô hình AI (OpenRouter):", available_models)
            model = model_name
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
                        
                        import io
                        import base64
                        
                        buffered = io.BytesIO()
                        if image.mode in ("RGBA", "P"):
                            image = image.convert("RGB")
                        image.save(buffered, format="JPEG")
                        img_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
                        
                        # Gọi API của OpenRouter
                        response = client.chat.completions.create(
                            model=model,
                            messages=[
                                {
                                    "role": "user",
                                    "content": [
                                        {"type": "text", "text": prompt},
                                        {
                                            "type": "image_url",
                                            "image_url": {
                                                "url": f"data:image/jpeg;base64,{img_b64}",
                                                "detail": "high"
                                            }
                                        }
                                    ]
                                }
                            ]
                        )
                        
                        st.success("Hoàn thành!")
                        st.markdown("### 📝 Kết quả trích xuất & Giải chi tiết:")
                        st.write(response.choices[0].message.content)
                    except Exception as e:
                        st.error(f"Đã xảy ra lỗi: {e}")
else:
    st.info("Vui lòng nhập API Key để bắt đầu.")
