#!/usr/bin/env python3
"""
测试图生图功能 - 使用人物图片生成分镜图片
"""

import asyncio
import sys
import os

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import generate_shot_image, generate_character_image

async def test_image_to_image():
    """测试图生图功能"""
    print("🧪 开始测试图生图功能...")
    
    # 1. 首先生成一个人物图片作为输入
    print("\n1️⃣ 生成人物图片作为输入...")
    character_result = await generate_character_image("Test Character", {
        "gender": "male",
        "age_range": "30s",
        "appearance": "英俊的面容，深邃的眼神",
        "personality": "成熟稳重"
    })
    
    if not character_result["success"]:
        print(f"❌ 人物图片生成失败: {character_result['error']}")
        return
    
    print(f"✅ 人物图片生成成功: {character_result['image_url']}")
    
    # 2. 使用人物图片生成分镜图片
    print("\n2️⃣ 使用人物图片生成分镜图片...")
    shot_content = "一个英俊的男性站在办公室窗前，阳光透过窗户洒在他身上，他正在思考着什么"
    
    shot_result = await generate_shot_image(
        shot_number=1,
        shot_content=shot_content,
        style="Realistic",
        aspect_ratio="16:9"
    )
    
    if shot_result["success"]:
        print(f"✅ 分镜图片生成成功: {shot_result['image_url']}")
        print(f"📝 分镜内容: {shot_content}")
    else:
        print(f"❌ 分镜图片生成失败: {shot_result['error']}")

async def test_multiple_shots():
    """测试多个分镜的图生图生成"""
    print("\n🧪 开始测试多个分镜的图生图生成...")
    
    # 模拟多个分镜
    shots = [
        "一个英俊的男性站在办公室窗前，阳光透过窗户洒在他身上",
        "男性坐在办公桌前，专注地看着电脑屏幕",
        "男性在会议室中发表演讲，手势自信有力",
        "男性在走廊中行走，西装笔挺，步伐稳健"
    ]
    
    for i, shot_content in enumerate(shots, 1):
        print(f"\n🎬 生成分镜 {i}: {shot_content[:30]}...")
        
        result = await generate_shot_image(
            shot_number=i,
            shot_content=shot_content,
            style="Realistic",
            aspect_ratio="16:9"
        )
        
        if result["success"]:
            print(f"✅ 分镜 {i} 生成成功: {result['image_url']}")
        else:
            print(f"❌ 分镜 {i} 生成失败: {result['error']}")
        
        # 等待一下再生成下一个
        if i < len(shots):
            print("⏳ 等待5秒...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    print("🚀 图生图功能测试")
    print("=" * 50)
    
    # 运行测试
    asyncio.run(test_image_to_image())
    
    print("\n" + "=" * 50)
    print("🎉 测试完成！")
