from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
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
        
        # Chuyển ảnh gốc thành base64 để gửi lên OpenRouter
        buffered_full = io.BytesIO()
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save(buffered_full, format="JPEG")
        img_b64 = base64.b64encode(buffered_full.getvalue()).decode("utf-8")
        
        # Cấu hình API Key cho OpenRouter thông qua OpenAI SDK
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        
        prompt = """
        Bạn là một gia sư Hóa học và Sinh học xuất sắc.
        Hãy đọc đề thi trong ảnh đính kèm. 
        1. Trích xuất toàn bộ nội dung câu hỏi từ ảnh thành văn bản rõ ràng (giữ nguyên định dạng, công thức LaTeX).
        2. VẤN ĐỀ HÌNH ẢNH (RẤT QUAN TRỌNG): Đề thi có chứa hình vẽ minh họa (ví dụ: các bình thí nghiệm). THAY VÌ miêu tả hình vẽ bằng chữ, BẠN BẮT BUỘC phải xác định tọa độ của hình vẽ đó trong bức ảnh gốc và chèn mã sau vào vị trí của hình:
        [BOX: ymin, xmin, ymax, xmax]
        (Trong đó ymin, xmin, ymax, xmax là 4 con số định vị từ 0 đến 1000. Ví dụ: [BOX: 450, 600, 520, 950]). Tuyệt đối không giải thích bằng chữ về hình vẽ đó.
        3. Cung cấp đáp án và lời giải chi tiết cho từng câu hỏi.
        """
        
        # Gọi API của OpenRouter
        response = client.chat.completions.create(
            model=model_name,
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
        result_text = response.choices[0].message.content
        
        # Hàm cắt ảnh và chuyển sang Base64 Markdown
        def replace_box_with_image(match):
            try:
                ymin, xmin, ymax, xmax = map(int, match.groups())
                width, height = img.size
                # Thêm padding (khoảng lề) 3% để ảnh cắt không bị quá sát
                padding_x = width * 0.03
                padding_y = height * 0.03
                
                left = max(0, ((xmin / 1000) * width) - padding_x)
                top = max(0, ((ymin / 1000) * height) - padding_y)
                right = min(width, ((xmax / 1000) * width) + padding_x)
                bottom = min(height, ((ymax / 1000) * height) + padding_y)
                
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
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        available_models = []
        for m in client.models.list():
            available_models.append(m.id)
        return {"success": True, "models": available_models}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
