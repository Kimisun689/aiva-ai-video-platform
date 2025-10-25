#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
海螺AI语音合成API简化测试
只测试同步HTTP API
"""

import requests
import json
import time
import base64
from pathlib import Path

# 海螺AI配置
HAILUO_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLlrZnplKbmt7siLCJVc2VyTmFtZSI6IuWtmemUpua3uyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTUxMTE2MDg5NTk3MzcxMDQ0IiwiUGhvbmUiOiIxMzcwMTE2NDgxNiIsIkdyb3VwSUQiOiIxOTUxMTE2MDg5NTg4OTgyNDM2IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDgtMTEgMTA6MTQ6MDIiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.ce-7TXB4JC9R31woacWZFx_ZChK35h-KpGriEljduvaYg0Ws-1ECVUnI9SCY_9QX6DzHXFbjNsN2cg-WBPPMJPdUoI4Ynf4jx1XXW6IzgIM4swKNfwMWOTCDJ9_VNKvTpUnEDK9gX4mfSFwkdB62zdMOUgDQONh1GditOurfGsT9UMG4w6jczypl7I4PBG4uO5E-vjRuvV9Hr3g9CGXPMk3iJ-A6-3Y5uZMX1XKWo_l5mPxWls_O8YudULhUPeVq8CJSA5lpLAgkcpj6_Nx8827uKbKyjpjJ1CW1oBt3lk5RxR6JgwichJKZnt0oMEkAGW2FMbbJJl3KK4-pKu282w"

def extract_group_id_from_token(token):
    """从JWT token中提取GroupId"""
    try:
        # JWT token由三部分组成，用.分隔
        parts = token.split('.')
        if len(parts) == 3:
            # 解码payload部分（第二部分）
            payload = parts[1]
            # 添加padding
            payload += '=' * (4 - len(payload) % 4)
            decoded = base64.b64decode(payload)
            payload_data = json.loads(decoded.decode('utf-8'))
            return payload_data.get('GroupID', '')
    except Exception as e:
        print(f"提取GroupId失败: {e}")
    return ''

def test_hailuo_tts(text="你好，这是海螺AI语音合成测试。", voice_id="male-qn-qingse"):
    
    # 提取GroupId
    group_id = extract_group_id_from_token(HAILUO_API_KEY)
    print(f"GroupId: {group_id}")
    
    # API配置
    url = f"https://api.minimaxi.com/v1/t2a_v2?GroupId={group_id}"
    headers = {
        "Authorization": f"Bearer {HAILUO_API_KEY}",
        "Content-Type": "application/json"
    }
    
    # 请求数据
    data = {
        "model": "speech-2.5-hd-preview",
        "text": text,
        "stream": False,
        "language_boost": "Chinese",
        "output_format": "hex",
        "voice_setting": {
            "voice_id": voice_id,
            "speed": 1.0,
            "vol": 1.0,
            "pitch": 0,
            "emotion": "happy"
        },
        "audio_setting": {
            "sample_rate": 32000,
            "bitrate": 128000,
            "format": "mp3",
            "channel": 1
        }
    }
    
    try:
        print(f"📝 合成文本: {text}")
        print(f"🎤 音色: {voice_id}")
        print(f"🌐 API地址: {url}")
        
        # 发送请求
        print("⏳ 正在发送请求...")
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📊 响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ 请求成功!")
            
            # 检查响应结构
            if 'data' in result and 'audio' in result['data']:
                audio_hex = result['data']['audio']
                print(f"🎵 音频数据长度: {len(audio_hex)} 字符")
                
                # 保存音频文件
                timestamp = int(time.time())
                filename = f"hailuo_test_{timestamp}.mp3"
                
                # 将hex转换为二进制
                audio_bytes = bytes.fromhex(audio_hex)
                
                with open(filename, 'wb') as f:
                    f.write(audio_bytes)
                
                print(f"💾 音频已保存: {filename}")
                print(f"📁 文件大小: {len(audio_bytes)} 字节")
                
                # 显示额外信息
                if 'extra_info' in result:
                    extra = result['extra_info']
                    print(f"📈 音频长度: {extra.get('audio_length', 'N/A')} 毫秒")
                    print(f"🎵 采样率: {extra.get('audio_sample_rate', 'N/A')} Hz")
                    print(f"📊 比特率: {extra.get('audio_bitrate', 'N/A')} bps")
                    print(f"📝 字符数: {extra.get('word_count', 'N/A')}")
                
                return {
                    "success": True,
                    "filename": filename,
                    "audio_size": len(audio_bytes),
                    "response": result
                }
            else:
                print("❌ 响应中没有音频数据")
                print(f"📄 完整响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                return {"success": False, "error": "No audio data in response"}
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"📄 错误响应: {response.text}")
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        print(f"❌ 请求异常: {e}")
        return {"success": False, "error": str(e)}

def main():
    """主测试函数"""
    print("🚀 海螺AI语音合成API测试")
    print("=" * 60)
    
    # 检查API Key
    if not HAILUO_API_KEY:
        print("❌ 请设置HAILUO_API_KEY")
        return
    
    # 测试基础功能
    test_text = "你好，这是海螺AI语音合成测试。我们正在测试语音合成功能。"
    result = test_hailuo_tts(test_text, "male-qn-qingse")
    
    if result["success"]:
        print(f"\n✅ 测试成功! 音频文件: {result['filename']}")
    else:
        print(f"\n❌ 测试失败: {result['error']}")

if __name__ == "__main__":
    main()
