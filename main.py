from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
import logging
from openai import OpenAI
from openai import APIError, BadRequestError

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vercel 环境通过平台设置环境变量，本地开发用 .env
if os.path.exists(".env"):
    from dotenv import load_dotenv
    load_dotenv()

app = FastAPI(title="先问春风 - AI故事创作")

# 初始化DeepSeek客户端
api_key = os.getenv("DEEPSEEK_API_KEY")
logger.info(f"DEEPSEEK_API_KEY 是否存在: {bool(api_key)}")
logger.info(f"DEEPSEEK_API_KEY 长度: {len(api_key) if api_key else 0}")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.deepseek.com"
)

class StoryRequest(BaseModel):
    prompt: str

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request):
    html_content = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>先问春风 - AI故事创作</title>
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+SC:wght@400;700&display=swap');
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Noto Serif SC', '宋体', serif;
                background: linear-gradient(135deg, #f5f0e8 0%, #e8dcc8 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: #fffef9;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                max-width: 800px;
                width: 100%;
                padding: 40px;
                border: 2px solid #d4c5a9;
            }
            
            .header {
                text-align: center;
                margin-bottom: 40px;
            }
            
            .header h1 {
                font-size: 42px;
                color: #2c1810;
                margin-bottom: 10px;
                font-weight: 700;
            }
            
            .header .subtitle {
                font-size: 16px;
                color: #8b7355;
                letter-spacing: 4px;
            }
            
            .divider {
                height: 2px;
                background: linear-gradient(90deg, transparent, #d4c5a9, transparent);
                margin: 30px 0;
            }
            
            .input-section {
                margin-bottom: 30px;
            }
            
            .input-section label {
                display: block;
                font-size: 18px;
                color: #2c1810;
                margin-bottom: 12px;
                font-weight: 700;
            }
            
            .input-section textarea {
                width: 100%;
                height: 120px;
                padding: 15px;
                font-size: 16px;
                font-family: 'Noto Serif SC', serif;
                border: 2px solid #d4c5a9;
                border-radius: 10px;
                background: #faf8f3;
                color: #2c1810;
                resize: vertical;
                transition: border-color 0.3s;
            }
            
            .input-section textarea:focus {
                outline: none;
                border-color: #8b7355;
            }
            
            .btn-generate {
                width: 100%;
                padding: 16px;
                font-size: 20px;
                font-family: 'Noto Serif SC', serif;
                background: linear-gradient(135deg, #2c1810 0%, #4a2c1a 100%);
                color: #f5f0e8;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                transition: transform 0.2s, box-shadow 0.2s;
                font-weight: 700;
                letter-spacing: 4px;
            }
            
            .btn-generate:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 20px rgba(44, 24, 16, 0.3);
            }
            
            .btn-generate:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
            }
            
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
                color: #8b7355;
                font-size: 16px;
            }
            
            .loading.active {
                display: block;
            }
            
            .result-section {
                margin-top: 30px;
                display: none;
            }
            
            .result-section.active {
                display: block;
            }
            
            .result-box {
                background: #faf8f3;
                border: 2px solid #d4c5a9;
                border-radius: 10px;
                padding: 25px;
                white-space: pre-wrap;
                font-size: 16px;
                line-height: 1.8;
                color: #2c1810;
                min-height: 200px;
            }
            
            .result-title {
                font-size: 18px;
                color: #2c1810;
                margin-bottom: 15px;
                font-weight: 700;
            }
            
            .examples {
                margin-top: 20px;
                padding: 20px;
                background: #faf8f3;
                border-radius: 10px;
                border: 1px solid #e8dcc8;
            }
            
            .examples h3 {
                font-size: 16px;
                color: #8b7355;
                margin-bottom: 12px;
            }
            
            .example-tag {
                display: inline-block;
                padding: 8px 16px;
                margin: 5px;
                background: #fffef9;
                border: 1px solid #d4c5a9;
                border-radius: 20px;
                cursor: pointer;
                font-size: 14px;
                color: #2c1810;
                transition: all 0.3s;
            }
            
            .example-tag:hover {
                background: #2c1810;
                color: #f5f0e8;
                border-color: #2c1810;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>先问春风</h1>
                <div class="subtitle">AI 故事创作助手</div>
            </div>
            
            <div class="divider"></div>
            
            <div class="input-section">
                <label>📝 请输入故事主题</label>
                <textarea id="prompt" placeholder="例如：一个侦探在沙漠中寻找失踪的科学家..."></textarea>
            </div>
            
            <button class="btn-generate" id="btn-generate" onclick="generateStory()">
                开始创作 ✨
            </button>
            
            <div class="loading" id="loading">
                ⏳ 正在创作中，请稍候...
            </div>
            
            <div class="examples">
                <h3>💡 灵感参考（点击使用）</h3>
                <span class="example-tag" onclick="useExample('一个时间旅行者试图阻止一场历史悲剧')">时间旅行</span>
                <span class="example-tag" onclick="useExample('在赛博朋克城市中，一个AI获得了自我意识')">赛博朋克</span>
                <span class="example-tag" onclick="useExample('一位老匠人临终前，将毕生秘密传授给陌生人')">温情故事</span>
                <span class="example-tag" onclick="useExample('外星生物降临地球，但只想学习人类的烹饪')">科幻喜剧</span>
                <span class="example-tag" onclick="useExample('一面能看见过去和未来的古镜，引发了一场家族纷争')">奇幻传说</span>
            </div>
            
            <div class="result-section" id="result-section">
                <div class="result-title">📖 创作结果</div>
                <div class="result-box" id="result-box"></div>
            </div>
        </div>
        
        <script>
            function useExample(text) {
                document.getElementById('prompt').value = text;
            }
            
            async function generateStory() {
                const prompt = document.getElementById('prompt').value.trim();
                
                if (!prompt) {
                    alert('请输入故事主题！');
                    return;
                }
                
                const btn = document.getElementById('btn-generate');
                const loading = document.getElementById('loading');
                const resultSection = document.getElementById('result-section');
                
                btn.disabled = true;
                loading.classList.add('active');
                resultSection.classList.remove('active');
                
                try {
                    const response = await fetch('/generate-outline', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ prompt: prompt })
                    });
                    
                    const data = await response.json();
                    
                    loading.classList.remove('active');
                    resultSection.classList.add('active');
                    
                    if (response.ok) {
                        document.getElementById('result-box').textContent = data.result;
                    } else {
                        // 显示详细错误信息
                        document.getElementById('result-box').innerHTML = 
                            `<span style="color: #d32f2f;">❌ 错误 (${response.status}): ${data.detail || '未知错误'}</span>`;
                    }
                    
                } catch (error) {
                    loading.classList.remove('active');
                    document.getElementById('result-box').innerHTML = 
                        `<span style="color: #d32f2f;">❌ 网络错误: ${error.message}</span>`;
                    console.error(error);
                } finally {
                    btn.disabled = false;
                }
            }
            
            // 按Enter键触发生成
            document.getElementById('prompt').addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    generateStory();
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

@app.post("/generate-outline")
def generate_outline(request: StoryRequest):
    user_prompt = request.prompt
    logger.info(f"收到用户请求: {user_prompt[:50]}...")
    
    # 检查 API Key 是否存在
    api_key = os.getenv("DEEPSEEK_API_KEY")
    if not api_key:
        logger.error("DEEPSEEK_API_KEY 环境变量未设置!")
        raise HTTPException(status_code=500, detail="API Key 未配置，请联系管理员")
    
    # 构造消息
    messages = [
        {
            "role": "system",
            "content": "你是一个专业编剧，请生成故事大纲（包含标题+三幕结构）。请用优美的中文回答。"
        },
        {
            "role": "user",
            "content": f"请根据这个主题创作故事：{user_prompt}"
        }
    ]
    
    logger.info(f"发送给 API 的消息: {messages}")
    logger.info(f"用户提示长度: {len(user_prompt)} 字符")
    
    try:
        logger.info("开始调用 DeepSeek API...")
        completion = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages
        )
        logger.info("DeepSeek API 调用成功")
        
        result = completion.choices[0].message.content
        return {"result": result}
        
    except BadRequestError as e:
        # 捕获 400 错误
        logger.error(f"BadRequestError: {str(e)}")
        logger.error(f"错误详情: {e.__dict__}")
        if hasattr(e, 'body') and e.body:
            logger.error(f"API 返回的错误体: {e.body}")
        raise HTTPException(status_code=400, detail=f"请求错误: {str(e)}")
        
    except APIError as e:
        # 捕获其他 API 错误
        logger.error(f"APIError: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        raise HTTPException(status_code=500, detail=f"API 错误: {str(e)}")
        
    except Exception as e:
        logger.error(f"调用 DeepSeek API 失败: {str(e)}")
        logger.error(f"错误类型: {type(e)}")
        import traceback
        logger.error(f"完整堆栈: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"生成失败: {str(e)}")
