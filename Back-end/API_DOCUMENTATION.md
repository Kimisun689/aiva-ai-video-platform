# AIVA AI视频生成平台 API 文档

## 🎭 人物识别功能 (第4步)

### 功能概述
AI从剧本中自动识别人物信息，包括姓名、性别、年龄、外观描述、性格特征和角色定位。

### API端点

#### 1. 提取人物信息
**POST** `/api/video/characters`

**请求体:**
```json
{
  "script": "完整的剧本文本"
}
```

**响应:**
```json
{
  "success": true,
  "characters": [
    {
      "name": "李小雨",
      "gender": "female",
      "age_range": "20s",
      "appearance": "长长的黑发，明亮的眼睛，穿着简约的白色衬衫和牛仔裤",
      "personality": "专注，惊喜的表情，激动",
      "role": "main character"
    },
    {
      "name": "王大力",
      "gender": "male", 
      "age_range": "30s",
      "appearance": "留着胡须，穿着休闲的格子衬衫，肩上挎着专业的相机包",
      "personality": "开朗，兴奋，总是能给人带来欢乐",
      "role": "supporting character"
    }
  ],
  "character_id": 1
}
```

#### 2. 获取所有人物提取记录
**GET** `/api/video/character-extracts`

**响应:**
```json
[
  {
    "id": 1,
    "script": "原始剧本文本",
    "characters": [
      {
        "name": "角色名",
        "gender": "性别",
        "age_range": "年龄范围",
        "appearance": "外观描述",
        "personality": "性格特征",
        "role": "角色定位"
      }
    ]
  }
]
```

### 人物信息字段说明

| 字段 | 类型 | 说明 | 示例 |
|------|------|------|------|
| name | string | 人物姓名 | "李小雨" |
| gender | string | 性别 | "male", "female", "other" |
| age_range | string | 年龄范围 | "20s", "30s", "40s", "50s" |
| appearance | string | 详细外观描述 | "长长的黑发，明亮的眼睛" |
| personality | string | 性格特征 | "开朗，兴奋，总是能给人带来欢乐" |
| role | string | 角色定位 | "main character", "supporting character" |

### 使用示例

#### Python示例
```python
import httpx
import asyncio

async def extract_characters():
    script = """
    在一个繁忙的咖啡厅里，年轻的作家李小雨正在专注地敲击着笔记本电脑的键盘。
    她是一个28岁的女性，有着长长的黑发和明亮的眼睛，穿着简约的白色衬衫和牛仔裤。
    """
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/api/video/characters",
            json={"script": script}
        )
        
        if response.status_code == 200:
            result = response.json()
            print("识别到的人物:", result["characters"])

asyncio.run(extract_characters())
```

#### JavaScript示例
```javascript
async function extractCharacters(script) {
    const response = await fetch('http://localhost:8000/api/video/characters', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ script })
    });
    
    const result = await response.json();
    if (result.success) {
        console.log('识别到的人物:', result.characters);
    }
}
```

### 错误处理

**错误响应格式:**
```json
{
  "success": false,
  "error": "错误描述信息"
}
```

**常见错误:**
- 网络连接失败
- AI服务暂时不可用
- 剧本格式不正确
- JSON解析错误

### 数据库存储

人物信息会存储在 `character_extracts` 表中：
- `id`: 主键
- `script`: 原始剧本文本
- `characters`: JSON格式的人物信息

### 注意事项

1. **AI识别准确性**: 人物识别的准确性取决于剧本的描述详细程度
2. **响应时间**: 通常需要5-10秒处理时间
3. **字符限制**: 建议剧本长度不超过5000字符
4. **语言支持**: 目前主要支持中文剧本

### 下一步计划

- [ ] 支持英文剧本识别
- [ ] 增加人物关系识别
- [ ] 支持人物情感状态识别
- [ ] 优化识别准确性 