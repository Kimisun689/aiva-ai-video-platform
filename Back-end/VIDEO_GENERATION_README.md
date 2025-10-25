# AI视频生成平台 - 视频生成功能说明

## 概述

本平台提供基于AI的视频生成功能，支持从用户提示词到完整视频的全流程生成。

## 功能特性

### ✅ 保留功能
- **人物画像生成**: 为剧本中的人物生成白底专业人像照片
- **分镜图片生成**: 为每个分镜生成第一帧图片
- **图生视频**: 基于分镜图片生成视频
- **数字人视频生成**: 基于分镜图片和音频生成数字人视频
- **视频合并**: 将多个分镜视频合并成完整视频
- **音频合成**: 为对话生成语音

## 视频生成流程

### 1. 用户输入提示词
用户输入视频创意描述

### 2. AI生成剧本
使用DeepSeek AI生成完整剧本

### 3. AI拆解分镜
将剧本拆解为多个分镜场景

### 4. 提取对话和人物
- 提取每个分镜中的对话内容
- 识别剧本中的人物角色

### 5. 生成人物画像
为每个识别出的人物生成白底专业人像照片

### 6. 生成分镜第一帧图片
为每个分镜生成高质量的第一帧图片（**使用图生图技术，基于人物画像生成**）

### 7. 基于图片生成视频
**基于分镜第一帧图片生成视频**，确保视频质量和一致性

### 8. 生成数字人视频
**基于分镜图片和音频生成数字人视频**，创建逼真的数字人说话效果

### 8.1. 对话数字人视频生成
**基于分镜图片和对话文本自动生成语音并创建数字人视频**，实现完整的对话到视频转换

### 9. 合并视频
将所有分镜视频按顺序合并成完整视频

### 10. 生成音频
为对话内容生成语音

## API端点

### 视频生成相关
- `POST /api/video/step1` - 生成AI剧本
- `POST /api/video/breakdown` - 拆解分镜
- `POST /api/video/generate-video` - 生成单个视频
- `POST /api/video/generate-shot-images` - 生成所有分镜图片
- `POST /api/video/generate-shot-video` - 生成单个分镜视频
- `POST /api/video/generate-all-shot-videos` - 批量生成所有分镜视频
- `POST /api/video/generate-digital-human-video` - 生成单个数字人视频
- `POST /api/video/generate-all-digital-human-videos` - 批量生成所有数字人视频
- `POST /api/video/generate-dialogue-digital-human` - 为指定对话生成数字人视频
- `POST /api/video/generate-all-dialogues-digital-human` - 为所有对话批量生成数字人视频
- `GET /api/video/generated-videos` - 获取生成的视频列表
- `GET /api/video/shot-images` - 获取分镜图片列表
- `GET /api/video/shot-images/latest` - 获取最新分镜图片
- `POST /api/video/combine-videos` - 合并视频

### 人物画像相关
- `POST /api/video/generate-character-images` - 生成所有人物画像
- `POST /api/video/generate-single-character-image` - 生成单个人物画像
- `GET /api/video/character-images` - 获取人物画像列表
- `GET /api/video/character-images/latest` - 获取最新人物画像

### 音频生成相关
- `POST /api/audio/generate` - 生成音频
- `POST /api/audio/generate-for-dialogues` - 为对话生成音频
- `GET /api/audio/files` - 获取音频文件列表

## 技术实现

### 分镜图片生成
- **模型**: Volcengine Jimeng `high_aes_general_v30l_zt2i` (图生图)
- **输入**: 人物画像URL + 分镜文本描述 + 风格和比例参数
- **输出**: 1024x1024高质量图片
- **技术**: 基于人物画像进行图生图，确保人物形象一致性

### 视频生成
- **模型**: ByteDance Jimeng `jimeng_vgfm_i2v_l20` (图生视频)
- **输入**: 分镜图片URL + 分镜文本描述
- **输出**: 5秒视频片段

### 数字人视频生成
- **模型**: 火山引擎数字人API
  - `realman_avatar_picture_create_role` (创建角色)
  - `realman_avatar_picture_loopyb` (生成视频)
- **输入**: 分镜图片URL + 音频URL
- **输出**: 数字人说话视频

### 对话数字人视频生成
- **语音合成**: 海螺AI语音合成API
  - `speech-2.5-hd-preview` 模型
  - 支持多种音色和语音参数
- **数字人视频**: 火山引擎数字人API
  - 自动语音与口型同步
- **输入**: 分镜图片URL + 对话文本
- **输出**: 带语音的数字人说话视频

### 人物画像生成
- **模型**: Volcengine Jimeng `high_aes_general_v30l_zt2i`
- **输入**: 人物描述 + 白底人像提示词
- **输出**: 1024x1024白底人像照片

### 音频生成
- **模型**: Hailuo AI TTS
- **输入**: 对话文本
- **输出**: 语音文件

## 数据库模型

### 核心表
- `prompts` - 用户提示词
- `ai_scripts` - AI生成的剧本
- `shot_breakdowns` - 分镜拆解
- `dialogue_extracts` - 对话提取
- `character_extracts` - 人物识别
- `character_images` - 人物画像
- `shot_images` - 分镜图片
- `generated_videos` - 生成的视频
- `audio_files` - 生成的音频

## 测试

### 运行测试
```bash
# 测试分镜图片生成
python3 test_shot_image_generation.py

# 测试数字人视频生成
python3 test_digital_human_video.py

# 测试对话数字人视频生成
python3 test_dialogue_digital_human.py

# 测试白底人物画像生成
python3 test_white_background_character.py
```

### 测试内容
1. **单个分镜图片生成测试**
2. **多个分镜图片生成测试**
3. **批量分镜图片生成测试**
4. **不同风格和比例测试**
5. **单个数字人视频生成测试**
6. **批量数字人视频生成测试**
7. **数字人视频工作流测试**
8. **对话数字人视频生成测试**
9. **语音合成功能测试**
10. **对话到视频完整流程测试**
8. **人物画像生成测试**
9. **功能完整性验证**

## 配置要求

### API密钥
- `DEEPSEEK_API_KEY` - DeepSeek AI API密钥
- `BYTEDANCE_ACCESS_KEY_ID` - 字节跳动视频生成API密钥
- `BYTEDANCE_SECRET_ACCESS_KEY` - 字节跳动视频生成API密钥
- `JIMENG_ACCESS_KEY_ID` - 火山引擎人物画像生成API密钥
- `JIMENG_SECRET_ACCESS_KEY` - 火山引擎人物画像生成API密钥
- `HAILUO_API_KEY` - Hailuo AI音频生成API密钥

### 依赖包
```bash
pip install fastapi uvicorn sqlalchemy httpx volcengine websockets
```

## 优势

### 高质量生成
- 为每个分镜生成高质量的第一帧图片
- 基于图片生成视频，确保视觉质量
- 支持多种风格和比例选择
- 数字人视频生成，创建逼真的说话效果
- 对话数字人视频生成，自动语音与视频同步

### 保持一致性
- 人物画像功能保留，确保人物视觉一致性
- 分镜图片确保场景视觉一致性
- 数字人视频确保人物说话效果一致性
- 对话数字人视频确保语音与口型同步一致性
- 整体用户体验保持一致

### 完整流程
- 完整的图片到视频生成流程
- 数字人视频生成流程（图片+音频→数字人视频）
- 对话数字人视频生成流程（图片+对话→语音→数字人视频）
- 确保每个步骤的质量控制
- 提供更好的视觉效果和交互体验

## 注意事项

1. **人物一致性**: 通过保留人物画像功能，确保人物在视频中的视觉一致性
2. **场景一致性**: 通过分镜图片生成，确保每个场景的视觉一致性
3. **数字人一致性**: 通过数字人视频生成，确保人物说话效果的一致性
4. **对话一致性**: 通过对话数字人视频生成，确保语音与口型同步的一致性
4. **视频质量**: 基于图片生成视频，确保高质量的视频输出
5. **音频同步**: 数字人视频需要音频与口型同步，确保自然效果
6. **API限制**: 注意各API的调用频率限制和并发限制
7. **错误处理**: 完善的错误处理机制，确保单个失败不影响整体流程

## 更新日志

### v4.0 (当前版本)
- ✅ 恢复分镜图片生成功能
- ✅ 恢复图生视频功能
- ✅ 新增数字人视频生成功能
- ✅ 新增对话数字人视频生成功能
- ✅ 优化为图片到视频的完整流程
- ✅ 保留人物画像生成功能
- ✅ 支持多种风格和比例
- ✅ 提高视频生成质量
- ✅ 支持音频与数字人视频同步
- ✅ 支持对话文本自动生成语音
- ✅ 支持语音与数字人视频自动同步

### v3.0 (历史版本)
- 恢复分镜图片生成功能
- 恢复图生视频功能
- 优化为图片到视频的完整流程

### v2.0 (历史版本)
- 移除分镜图片生成功能
- 优化为直接文本生视频
- 简化视频生成流程

### v1.0 (历史版本)
- 包含完整的分镜图片生成和图生视频功能
