# 实现计划: AI语音对话系统

## 概述

本实现计划将AI语音对话系统分解为可执行的编码任务，采用增量开发方式，确保每个步骤都能验证核心功能。

## 任务

- [x] 1. 项目初始化和基础设施
  - [x] 1.1 创建项目目录结构
    - 创建 `backend/` 和 `frontend/` 目录
    - 创建 `backend/app/`, `backend/tests/` 子目录
    - 创建 `config.py` 配置文件模板
    - _Requirements: 10.5_

  - [x] 1.2 创建Python依赖文件
    - 创建 `requirements.txt` 包含: fastapi, uvicorn, httpx, pydantic, python-multipart
    - 添加测试依赖: pytest, pytest-asyncio, hypothesis
    - _Requirements: 10.4_

  - [x] 1.3 创建启动脚本
    - 创建 `run.sh` 包含conda环境激活和uvicorn启动命令
    - _Requirements: 10.1, 10.2_

- [x] 2. 后端数据模型和配置
  - [x] 2.1 实现数据模型
    - 创建 `backend/app/models.py`
    - 实现 Message, ConversationSession, AudioChunk, ConversationEvent 模型
    - 实现 MessageRole, ConversationEventType, ErrorType 枚举
    - _Requirements: 4.3, 8.1_

  - [x] 2.2 实现API配置模块
    - 创建 `backend/app/config.py`
    - 实现 APIConfig 类，包含LLM、ASR、TTS配置
    - 从环境变量或配置文件加载密钥
    - _Requirements: 9.1, 9.2, 9.3, 9.4_

  - [ ]* 2.3 编写数据模型属性测试
    - **Property 3: 对话历史一致性**
    - **Validates: Requirements 4.3**

- [ ] 3. 对话状态机
  - [x] 3.1 实现对话状态机
    - 创建 `backend/app/state_machine.py`
    - 实现 ConversationState 枚举 (IDLE, LISTENING, PROCESSING, SPEAKING)
    - 实现状态转换逻辑和打断处理
    - _Requirements: 6.5, 5.5, 6.2, 6.3_

  - [ ]* 3.2 编写状态机属性测试
    - **Property 5: 对话状态机有效性**
    - **Validates: Requirements 5.5, 6.2, 6.3, 6.5**

- [ ] 4. Checkpoint - 确保基础模块测试通过
  - 运行所有测试，确保通过
  - 如有问题，询问用户

- [x] 5. ASR客户端实现
  - [x] 5.1 实现ASR客户端
    - 创建 `backend/app/clients/asr_client.py`
    - 实现 ASRClient 类
    - 实现 `transcribe_stream()` 异步生成器方法
    - 解析智谱AI ASR的SSE响应流
    - _Requirements: 3.2, 9.2, 9.5_

  - [ ]* 5.2 编写ASR解析属性测试
    - **Property 1: ASR流式响应解析正确性**
    - **Validates: Requirements 3.2, 3.4**

- [x] 6. LLM客户端实现
  - [x] 6.1 实现LLM客户端
    - 创建 `backend/app/clients/llm_client.py`
    - 实现 LLMClient 类
    - 实现 `chat_stream()` 异步生成器方法
    - 使用OpenAI兼容格式调用mimo-v2-flash
    - _Requirements: 4.1, 4.2, 9.1, 9.5_

  - [ ]* 6.2 编写LLM解析属性测试
    - **Property 2: LLM流式响应处理正确性**
    - **Validates: Requirements 4.1, 4.2**

- [x] 7. TTS客户端实现
  - [x] 7.1 实现TTS客户端
    - 创建 `backend/app/clients/tts_client.py`
    - 实现 TTSClient 类
    - 实现 `synthesize_stream()` 异步生成器方法
    - 解析智谱AI TTS的SSE响应流，提取base64音频
    - _Requirements: 5.1, 9.3, 9.5, 9.6, 9.7_

  - [ ]* 7.2 编写TTS解析属性测试
    - **Property 4: TTS流式响应解析正确性**
    - **Validates: Requirements 5.1**

- [ ] 8. Checkpoint - 确保API客户端测试通过
  - 运行所有测试，确保通过
  - 如有问题，询问用户

- [x] 9. 流处理器和对话管理器
  - [x] 9.1 实现流处理器
    - 创建 `backend/app/stream_processor.py`
    - 实现 StreamProcessor 类
    - 实现 `merge_streams()` 和 `format_sse_event()` 方法
    - _Requirements: 7.2_

  - [ ]* 9.2 编写流处理器属性测试
    - **Property 6: 流式数据传递完整性**
    - **Validates: Requirements 7.2**

  - [x] 9.3 实现对话管理器
    - 创建 `backend/app/conversation_manager.py`
    - 实现 ConversationManager 类
    - 实现 `create_session()`, `process_audio()`, `start_conversation()` 方法
    - 协调ASR、LLM、TTS的流式调用
    - _Requirements: 4.3, 6.1_

- [x] 10. 错误处理模块
  - [x] 10.1 实现错误处理
    - 创建 `backend/app/error_handler.py`
    - 实现错误类型定义和错误消息生成
    - 实现日志记录功能
    - 实现重试机制
    - _Requirements: 8.1, 8.4, 3.5, 4.5_

  - [ ]* 10.2 编写错误处理属性测试
    - **Property 7: 错误处理一致性**
    - **Validates: Requirements 8.1, 8.4**

  - [ ]* 10.3 编写API密钥安全属性测试
    - **Property 9: API密钥安全性**
    - **Validates: Requirements 9.4**

- [x] 11. FastAPI应用和路由
  - [x] 11.1 实现FastAPI应用
    - 创建 `backend/app/main.py`
    - 实现 `/api/conversation/audio` POST端点
    - 实现 `/api/conversation/stream` SSE端点
    - 实现 `/api/conversation/start` POST端点
    - 实现 `/health` 健康检查端点
    - 配置CORS中间件
    - _Requirements: 4.1, 5.1, 6.1_

  - [ ]* 11.2 编写API配置属性测试
    - **Property 8: API配置正确性**
    - **Validates: Requirements 9.5, 9.7**

- [ ] 12. Checkpoint - 确保后端测试通过
  - 运行所有后端测试，确保通过
  - 如有问题，询问用户

- [x] 13. 前端基础结构
  - [x] 13.1 创建HTML页面
    - 创建 `frontend/index.html`
    - 实现左右分栏布局
    - 左侧AI机器人图标区域
    - 右侧视频显示区域
    - 状态指示器和文本显示区域
    - _Requirements: 1.1, 1.2, 1.4_

  - [x] 13.2 创建CSS样式
    - 创建 `frontend/styles.css`
    - 实现响应式布局
    - 实现状态指示器样式
    - _Requirements: 1.3_

- [ ] 14. 前端JavaScript模块
  - [x] 14.1 实现UIController
    - 创建 `frontend/js/ui-controller.js`
    - 实现状态显示、错误显示、文本更新方法
    - _Requirements: 1.4, 2.4, 2.5_

  - [x] 14.2 实现MediaCaptureManager
    - 创建 `frontend/js/media-capture.js`
    - 实现权限请求、视频流启动、音频录制方法
    - 使用MediaRecorder API
    - _Requirements: 2.1, 2.2, 2.3, 3.1_

  - [x] 14.3 实现ConversationClient
    - 创建 `frontend/js/conversation-client.js`
    - 实现音频发送和SSE监听方法
    - 使用EventSource API
    - _Requirements: 3.4, 4.1_

  - [x] 14.4 实现AudioStreamPlayer
    - 创建 `frontend/js/audio-player.js`
    - 实现Web Audio API音频播放
    - 实现base64 PCM解码和流式播放
    - _Requirements: 5.2_

  - [x] 14.5 实现主应用逻辑
    - 创建 `frontend/js/app.js`
    - 整合所有模块
    - 实现对话流程控制
    - 实现打断逻辑
    - _Requirements: 6.1, 6.2, 6.3, 6.4_

- [x] 15. 最终集成和测试
  - [x] 15.1 集成测试
    - 验证前后端通信
    - 验证完整对话流程
    - _Requirements: 7.1, 7.3_

- [ ] 16. Final Checkpoint - 确保所有测试通过
  - 运行所有测试，确保通过
  - 如有问题，询问用户

## 备注

- 标记 `*` 的任务为可选任务，可跳过以加快MVP开发
- 每个任务都引用了具体的需求以便追溯
- Checkpoint确保增量验证
- 属性测试验证通用正确性属性
- 单元测试验证具体示例和边界情况
