import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';
import 'katex/dist/katex.min.css';
import './App.css';

function App() {
  const [apiKey, setApiKey] = useState('');
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('gemini-1.5-flash');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState('');
  const [error, setError] = useState('');

  const fetchModels = async () => {
    if (!apiKey) {
      setError("Vui lòng nhập API Key trước.");
      return;
    }
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`http://localhost:8000/api/models?api_key=${apiKey}`);
      const data = await response.json();
      if (data.success) {
        setModels(data.models);
        if (data.models.length > 0) {
          setSelectedModel(data.models[0]);
        }
      } else {
        setError("Lỗi khi lấy danh sách model.");
      }
    } catch (err) {
      setError("Không thể kết nối đến Backend (FastAPI). Đảm bảo Backend đang chạy ở cổng 8000.");
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleSolve = async () => {
    if (!file || !apiKey) {
      setError("Vui lòng nhập API Key và chọn file ảnh.");
      return;
    }
    setLoading(true);
    setError('');
    setResult('');
    
    const formData = new FormData();
    formData.append('image', file);
    formData.append('api_key', apiKey);
    formData.append('model_name', selectedModel);

    try {
      const response = await fetch('http://localhost:8000/api/solve', {
        method: 'POST',
        body: formData,
      });
      const data = await response.json();
      if (response.ok && data.success) {
        setResult(data.result);
      } else {
        setError(data.detail || "Đã xảy ra lỗi khi giải đề.");
      }
    } catch (err) {
      setError("Lỗi kết nối đến Backend.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header animate-fade-in" style={{ animationDelay: '0s' }}>
        <h1>☕ Trợ Lý AI Hóa Sinh</h1>
        <p>Tải ảnh đề thi lên và trải nghiệm sức mạnh của "Gia sư AI 1 kèm 1"</p>
      </header>

      <main className="main-content">
        <div className="glass-panel api-setup animate-fade-in" style={{ animationDelay: '0.1s' }}>
          <h2>1. Kết nối AI</h2>
          <div className="input-group">
            <input 
              type="password" 
              placeholder="Nhập OpenRouter API Key của bạn..."
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
            />
            <button onClick={fetchModels} disabled={loading}>
              {loading && !file ? "Đang kết nối..." : "Lấy danh sách Model"}
            </button>
          </div>
          
          {models.length > 0 && (
            <div className="input-group" style={{ marginTop: '16px' }}>
              <select 
                value={selectedModel} 
                onChange={(e) => setSelectedModel(e.target.value)}
                style={{ flex: 1, padding: '12px', borderRadius: '8px', border: '1px solid var(--surface-border)', background: 'rgba(255, 255, 255, 0.8)', color: 'var(--text-primary)' }}
              >
                {models.map((m) => (
                  <option key={m} value={m}>{m}</option>
                ))}
              </select>
            </div>
          )}
        </div>

        <div className="glass-panel upload-zone animate-fade-in" style={{ animationDelay: '0.2s' }}>
          <div className="upload-content">
            <span className="upload-icon">☁️</span>
            <h3>{file ? file.name : "Kéo thả hoặc Nhấn để tải ảnh đề thi"}</h3>
            <p>Hỗ trợ định dạng JPG, PNG (Tối đa 5MB)</p>
            <input type="file" className="file-input" accept="image/png, image/jpeg" onChange={handleFileChange} />
          </div>
        </div>

        {error && (
          <div className="glass-panel error-panel animate-fade-in" style={{ color: 'var(--danger-color)', borderColor: 'var(--danger-color)' }}>
            <p>❌ {error}</p>
          </div>
        )}

        <button 
          className="animate-fade-in" 
          style={{ animationDelay: '0.3s', padding: '16px', fontSize: '1.1rem' }}
          onClick={handleSolve}
          disabled={loading || !file}
        >
          {loading && file ? "☕ AI đang suy nghĩ (Uống ngụm cà phê đợi xíu nhé)..." : "🚀 Bắt đầu nhận diện & Giải"}
        </button>

        {result && (
          <div className="glass-panel result-panel animate-fade-in" style={{ animationDelay: '0.1s' }}>
            <h2>📝 Kết quả Giải chi tiết:</h2>
            <div className="markdown-body" style={{ marginTop: '16px', lineHeight: '1.6' }}>
              <ReactMarkdown 
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
                urlTransform={(url) => url}
              >
                {result}
              </ReactMarkdown>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
