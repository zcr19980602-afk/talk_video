# 需求文档

## 简介

AI语音对话系统是一个实时交互应用，允许用户通过摄像头和麦克风与AI机器人进行自然语音对话。系统采用流式处理架构，实现低延迟的语音识别、智能回复生成和语音合成。

## 术语表

- **System**: AI语音对话系统
- **AI_Agent**: AI对话机器人组件
- **Speech_Recognizer**: 语音识别模块（使用智谱AI的glm-asr-2512模型）
- **LLM_Service**: 大语言模型服务（使用mimo-v2-flash模型）
- **TTS_Engine**: 文本转语音引擎（使用智谱AI的glm-tts模型）
- **Audio_Stream**: 音频流处理器
- **Video_Capture**: 视频捕获组件
- **User**: 使用系统的人
- **API_Config**: API配置信息，包含密钥和端点

## 需求

### 需求 1: 用户界面布局

**用户故事:** 作为用户，我希望看到清晰的界面布局，以便我能够同时看到AI机器人和自己的视频画面。

#### 验收标准

1. WHEN 应用启动时，THE System SHALL 在左侧显示AI机器人图标或数字人界面
2. WHEN 应用启动时，THE System SHALL 在右侧显示用户的摄像头实时画面
3. THE System SHALL 保持界面布局响应式，适应不同屏幕尺寸
4. THE System SHALL 提供视觉反馈指示当前对话状态（监听中、思考中、说话中）

### 需求 2: 摄像头和麦克风访问

**用户故事:** 作为用户，我希望系统能够访问我的摄像头和麦克风，以便进行视频和语音交互。

#### 验收标准

1. WHEN 应用首次启动时，THE System SHALL 请求用户授权访问摄像头和麦克风
2. WHEN 用户授权后，THE Video_Capture SHALL 开始捕获并显示实时视频流
3. WHEN 用户授权后，THE Audio_Stream SHALL 开始监听麦克风输入
4. IF 用户拒绝授权，THEN THE System SHALL 显示友好的错误提示并说明如何授权
5. THE System SHALL 在用户摄像头或麦克风不可用时提供明确的错误信息

### 需求 3: 流式语音识别

**用户故事:** 作为用户，我希望系统能够实时识别我的语音，以便快速响应我的问题。

#### 验收标准

1. WHEN 用户开始说话时，THE Speech_Recognizer SHALL 实时捕获音频流
2. WHEN 音频流被捕获时，THE Speech_Recognizer SHALL 以流式方式将语音转换为文本
3. WHEN 用户停止说话时，THE Speech_Recognizer SHALL 检测语音结束并完成识别
4. THE Speech_Recognizer SHALL 在识别过程中提供实时文本反馈
5. IF 识别失败或音频质量差，THEN THE System SHALL 提示用户重新说话

### 需求 4: AI对话生成

**用户故事:** 作为用户，我希望AI能够理解我的问题并给出智能回复，以便进行自然的对话交互。

#### 验收标准

1. WHEN Speech_Recognizer 完成语音识别时，THE System SHALL 将识别文本发送给 LLM_Service
2. WHEN LLM_Service 收到用户输入时，THE LLM_Service SHALL 以流式方式生成回复内容
3. THE LLM_Service SHALL 保持对话上下文，实现多轮对话
4. THE System SHALL 在AI思考时显示视觉指示器
5. IF LLM_Service 调用失败，THEN THE System SHALL 提供友好的错误提示并允许重试

### 需求 5: 流式语音合成

**用户故事:** 作为用户，我希望AI的回复能够以自然的语音播放出来，以便获得沉浸式的对话体验。

#### 验收标准

1. WHEN LLM_Service 生成回复文本时，THE TTS_Engine SHALL 以流式方式将文本转换为语音
2. WHEN TTS_Engine 生成音频片段时，THE System SHALL 立即开始播放，无需等待完整生成
3. THE TTS_Engine SHALL 使用自然流畅的语音合成
4. THE System SHALL 在AI说话时提供视觉反馈（如动画或指示器）
5. THE System SHALL 允许用户在AI说话时打断并开始新的提问

### 需求 6: 对话流程控制

**用户故事:** 作为用户，我希望系统能够智能管理对话流程，以便实现流畅的交互体验。

#### 验收标准

1. WHEN 应用启动后，THE AI_Agent SHALL 主动提出第一个问题
2. WHEN AI说话完成后，THE System SHALL 自动开始监听用户回复
3. WHEN 用户说话时，THE System SHALL 暂停AI的语音输出
4. THE System SHALL 防止语音识别和TTS播放之间的回声干扰
5. THE System SHALL 维护清晰的对话状态机（空闲、监听、处理、说话）

### 需求 7: 流式数据处理

**用户故事:** 作为用户，我希望系统响应迅速，以便获得接近实时的对话体验。

#### 验收标准

1. THE System SHALL 采用流式架构处理所有数据流（语音识别、LLM生成、TTS合成）
2. WHEN 任何流式组件产生数据时，THE System SHALL 立即传递给下游组件
3. THE System SHALL 最小化端到端延迟（从用户说话结束到AI开始回复）
4. THE System SHALL 使用异步处理避免阻塞用户界面
5. THE System SHALL 在网络延迟或处理延迟时提供适当的加载指示

### 需求 8: 错误处理和恢复

**用户故事:** 作为用户，我希望系统能够优雅地处理错误，以便在出现问题时仍能继续使用。

#### 验收标准

1. IF 任何服务调用失败，THEN THE System SHALL 显示清晰的错误消息
2. WHEN 网络连接中断时，THE System SHALL 提示用户并尝试重新连接
3. WHEN 错误恢复后，THE System SHALL 允许用户继续对话
4. THE System SHALL 记录错误日志以便调试
5. THE System SHALL 在关键错误时提供重启或重置选项

### 需求 9: API服务集成

**用户故事:** 作为开发者，我希望系统能够正确集成各个API服务，以便实现完整的对话功能。

#### 验收标准

1. THE LLM_Service SHALL 使用mimo-v2-flash模型，通过https://api.xiaomimimo.com/v1端点访问
2. THE Speech_Recognizer SHALL 使用智谱AI的glm-asr-2512模型进行流式语音识别
3. THE TTS_Engine SHALL 使用智谱AI的glm-tts模型进行流式语音合成
4. THE System SHALL 安全存储和管理API密钥
5. THE System SHALL 对所有API调用使用流式处理（stream=true）
6. THE TTS_Engine SHALL 使用PCM格式和base64编码输出音频
7. THE TTS_Engine SHALL 支持配置语音参数（voice、speed、volume）

### 需求 10: 环境配置

**用户故事:** 作为开发者，我希望系统能够使用指定的conda环境，以便确保依赖一致性。

#### 验收标准

1. THE System SHALL 在 talk_demo_env conda环境中运行
2. THE System SHALL 在启动脚本中包含环境激活指令
3. THE System SHALL 提供清晰的环境设置文档
4. THE System SHALL 列出所有必需的Python包依赖
5. THE System SHALL 提供配置文件模板用于API密钥管理
