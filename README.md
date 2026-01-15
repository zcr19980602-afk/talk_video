# AI 语音对话系统 (AI Voice Conversation Demo)

本项目是一个实时 AI 语音对话系统，集成了语音识别 (ASR)、大语言模型 (LLM) 和语音合成 (TTS) 技术，支持自然的语音交互和打断功能。

## ✨ 主要功能

- **实时语音对话**：按住说话，松开即发送，体验流畅的语音交互。
- **智能打断 (Barge-in)**：当 AI 正在说话时，用户开始录音会立即打断 AI 的回应，实现更自然的对话节奏。
- **自动音频转码**：后端自动处理 WebM 等格式的音频，确保与 ASR 服务的兼容性。
- **安全配置**：基于 `.env` 的环境变量管理，确保密钥安全。

## 🛠️ 技术栈

- **后端**: Python 3.10+, FastAPI, Uvicorn
- **前端**: 原生 JavaScript, CSS3
- **AI 服务**:
  - **LLM**: MiniMax (mimo-v2-flash)
  - **ASR/TTS**: 智谱 AI (GLM-ASR/TTS)
- **工具**: FFmpeg (音频处理)

## 🚀 快速开始

### 1. 环境准备

确保您的系统已安装：
- Python 3.10 或更高版本
- Conda (推荐)
- FFmpeg (用于音频转码)

```bash
# macOS 安装 FFmpeg
brew install ffmpeg
```

### 2. 获取代码

```bash
git clone https://github.com/your-username/talk_demo.git
cd talk_demo
```

### 3. 配置环境变量

**重要**：本项目依赖 API 密钥运行。请复制示例配置文件并填入您的真实密钥。

```bash
cp .env.example .env
```

编辑 `.env` 文件，填入您的 API Key：
```ini
LLM_API_KEY=sk-xxxx
ZHIPU_API_KEY=xxxx.xxxx
# ... 其他配置
```

### 4. 安装依赖并运行

本项目提供了一键启动脚本 `run.sh`，它会自动激活 Conda 环境、安装依赖并启动服务。

```bash
./run.sh
```

或者手动运行：
```bash
conda activate talk_demo_env
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload
```

### 5. 开始对话

服务启动后，浏览器访问地址通常为：
[http://localhost:8000](http://localhost:8000)

1. 点击 **[开始对话]**。
2. 授予浏览器麦克风权限。
3. **按住 [按住说话] 按钮** 进行语音输入，松开后系统会自动回复。

## 📁 目录结构

```text
.
├── backend/                # 后端代码
│   ├── app/
│   │   ├── clients/        # AI 客户端 (ASR, LLM, TTS)
│   │   ├── utils/          # 工具函数 (如音频转换)
│   │   ├── main.py         # FastAPI 入口
│   │   └── config.py       # 配置加载
│   └── requirements.txt    # Python 依赖
├── frontend/               # 前端代码
│   ├── js/                 # 业务逻辑 (App, Media, AudioPlayer)
│   ├── styles.css          # 样式表
│   └── index.html          # 主页
├── .env.example            # 环境变量模板
├── run.sh                  # 启动脚本
└── README.md               # 项目文档
```

## 📝 许可证

MIT License
