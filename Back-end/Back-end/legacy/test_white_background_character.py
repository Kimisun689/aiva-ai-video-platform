#!/usr/bin/env python3
"""
白底人物图片生成测试脚本
用于测试修改后的人物图片生成功能
"""

import asyncio
import json
from main import generate_character_image

async def test_white_background_character():
    """测试白底人物图片生成"""
    print("=== 测试白底人物图片生成 ===")
    
    # 测试人物信息
    character_info = {
        "name": "测试人物",
        "gender": "male",
        "age_range": "30s",
        "appearance": "英俊的面容，深邃的眼神，穿着正装",
        "personality": "成熟稳重，有领导气质",
        "role": "主角"
    }
    
    character_name = "测试人物"
    
    print(f"人物信息: {character_info}")
    print(f"人物姓名: {character_name}")
    
    # 生成图片
    result = await generate_character_image(character_name, character_info)
    
    print(f"生成结果: {result}")
    
    if result["success"]:
        print(f"✅ 白底人物图片生成成功!")
        print(f"   图片URL: {result['image_url']}")
        print(f"   人物姓名: {result['character_name']}")
    else:
        print(f"❌ 白底人物图片生成失败: {result.get('error', 'Unknown error')}")
    
    return result

async def test_multiple_characters():
    """测试多个人物图片生成"""
    print("\n=== 测试多个人物图片生成 ===")
    
    characters = [
        {
            "name": "女主角",
            "gender": "female",
            "age_range": "25s",
            "appearance": "美丽的面容，长发飘逸，穿着优雅的连衣裙",
            "personality": "温柔善良，聪明机智",
            "role": "女主角"
        },
        {
            "name": "男主角",
            "gender": "male",
            "age_range": "28s",
            "appearance": "英俊的面容，短发利落，穿着休闲装",
            "personality": "阳光开朗，幽默风趣",
            "role": "男主角"
        },
        {
            "name": "反派角色",
            "gender": "male",
            "age_range": "35s",
            "appearance": "严肃的面容，眼神锐利，穿着黑色西装",
            "personality": "冷酷无情，野心勃勃",
            "role": "反派"
        }
    ]
    
    results = []
    
    for i, character_info in enumerate(characters):
        print(f"\n正在生成第 {i+1}/{len(characters)} 个人物: {character_info['name']}")
        
        result = await generate_character_image(character_info['name'], character_info)
        results.append(result)
        
        if result["success"]:
            print(f"✅ {character_info['name']} 图片生成成功!")
        else:
            print(f"❌ {character_info['name']} 图片生成失败: {result.get('error', 'Unknown error')}")
        
        # 等待5秒再生成下一个
        if i < len(characters) - 1:
            print("等待5秒后继续...")
            await asyncio.sleep(5)
    
    # 统计结果
    success_count = len([r for r in results if r["success"]])
    print(f"\n=== 生成结果统计 ===")
    print(f"总人物数: {len(characters)}")
    print(f"成功数量: {success_count}")
    print(f"失败数量: {len(characters) - success_count}")
    
    return results

async def main():
    """主函数"""
    print("🎬 白底人物图片生成测试")
    print("=" * 50)
    
    # 测试单个白底人物图片生成
    single_result = await test_white_background_character()
    
    # 等待10秒
    print("\n等待10秒后测试多个人物...")
    await asyncio.sleep(10)
    
    # 测试多个人物图片生成
    multiple_results = await test_multiple_characters()
    
    # 总结
    print("\n" + "=" * 50)
    print("📋 测试总结:")
    print(f"单个生成: {'✅ 成功' if single_result['success'] else '❌ 失败'}")
    print(f"批量生成: {'✅ 成功' if all(r['success'] for r in multiple_results) else '❌ 部分失败'}")

if __name__ == "__main__":
    asyncio.run(main())
