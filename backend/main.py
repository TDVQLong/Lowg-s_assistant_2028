from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import google.generativeai as genai
from PIL import Image
import io
import re
import base64

app = FastAPI()

# Cấu hình CORS để Frontend (React) ở cổng 5173 có thể gọi API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/solve")
async def solve_exam(
    image: UploadFile = File(...),
    api_key: str = Form(...),
    model_name: str = Form("gemini-1.5-flash")
):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
        
    try:
        # Đọc dữ liệu ảnh được upload
        contents = await image.read()
        img = Image.open(io.BytesIO(contents))
        
        # Cấu hình API Key cho thư viện Google
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Prompt hướng dẫn AI xử lý
        prompt = """
        Bạn là một gia sư Hóa học và Sinh học xuất sắc.
        Hãy đọc đề thi trong ảnh đính kèm. 
        1. Trích xuất toàn bộ nội dung câu hỏi từ ảnh thành văn bản rõ ràng (giữ nguyên định dạng, công thức LaTeX).
        2. VẤN ĐỀ HÌNH ẢNH: Nếu câu hỏi có chứa biểu đồ, đồ thị, sơ đồ thí nghiệm hoặc hình vẽ minh họa, hãy chèn đoạn mã sau vào đúng vị trí của hình ảnh đó trong văn bản: `[BOX: ymin, xmin, ymax, xmax]`
        (Trong đó ymin, xmin, ymax, xmax là tọa độ hộp bao quanh hình ảnh (bounding box) tương ứng trong ảnh, với các giá trị chuẩn hóa từ 0 đến 1000). 
        TUYỆT ĐỐI không cần miêu tả hình ảnh bằng chữ, chỉ cần dùng đoạn mã [BOX: ...].
        3. Cung cấp đáp án và lời giải chi tiết cho từng câu hỏi ở bên dưới phần trích xuất.
        """
        
        # Gọi API của Google Gemini
        response = model.generate_content([prompt, img])
        result_text = response.text
        
        # Hàm cắt ảnh và chuyển sang Base64 Markdown
        def replace_box_with_image(match):
            try:
                ymin, xmin, ymax, xmax = map(int, match.groups())
                width, height = img.size
                left = (xmin / 1000) * width
                top = (ymin / 1000) * height
                right = (xmax / 1000) * width
                bottom = (ymax / 1000) * height
                
                # Cắt ảnh
                cropped = img.crop((left, top, right, bottom))
                
                # Chuyển thành base64
                buffered = io.BytesIO()
                cropped.save(buffered, format="PNG")
                img_str = base64.b64encode(buffered.getvalue()).decode()
                
                return f"\n\n![Hình minh họa](data:image/png;base64,{img_str})\n\n"
            except Exception as e:
                print("Lỗi khi cắt ảnh:", e)
                return match.group(0) # Trả lại chuỗi cũ nếu lỗi
                
        # Regex tìm [BOX: 123, 456, 789, 123]
        pattern = r"\[BOX:\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]"
        result_text = re.sub(pattern, replace_box_with_image, result_text)
        
        return {"success": True, "result": result_text}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/models")
def get_models(api_key: str):
    if not api_key:
        raise HTTPException(status_code=400, detail="API Key is required")
    try:
        genai.configure(api_key=api_key)
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name.replace("models/", ""))
        return {"success": True, "models": available_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
