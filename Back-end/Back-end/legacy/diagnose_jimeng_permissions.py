#!/usr/bin/env python3
"""
即梦API权限诊断脚本
用于诊断图片生成API的权限和配置问题
"""

import requests
import json
import base64
import hashlib
import hmac
from datetime import datetime
import time

# 即梦文生图API 配置
JIMENG_ACCESS_KEY_ID = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
JIMENG_SECRET_ACCESS_KEY = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="

def decode_base64_secret(encoded_secret):
    """解码Base64编码的密钥"""
    try:
        decoded = base64.b64decode(encoded_secret).decode('utf-8')
        return decoded
    except Exception as e:
        print(f"解码密钥失败: {e}")
        return None

def test_api_connection():
    """测试API连接"""
    print("=== 即梦API连接测试 ===")
    
    # 解码密钥
    secret_key = decode_base64_secret(JIMENG_SECRET_ACCESS_KEY)
    if not secret_key:
        print("❌ 密钥解码失败")
        return False
    
    print(f"✅ Access Key ID: {JIMENG_ACCESS_KEY_ID}")
    print(f"✅ Secret Key (前10位): {secret_key[:10]}...")
    
    # 测试基本连接
    try:
        # 使用简单的GET请求测试连接
        url = "https://visual.volcengineapi.com"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ API端点连接成功: {response.status_code}")
        return True
        
    except Exception as e:
        print(f"❌ API连接失败: {e}")
        return False

def test_sdk_import():
    """测试SDK导入"""
    print("\n=== SDK导入测试 ===")
    
    try:
        from volcengine.visual.VisualService import VisualService
        print("✅ volcengine SDK导入成功")
        
        # 测试SDK初始化
        vs = VisualService()
        vs.set_ak(JIMENG_ACCESS_KEY_ID)
        vs.set_sk(JIMENG_SECRET_ACCESS_KEY)
        vs.set_host("visual.volcengineapi.com")
        print("✅ SDK初始化成功")
        
        return True
        
    except ImportError as e:
        print(f"❌ SDK导入失败: {e}")
        print("请安装: pip install volcengine")
        return False
    except Exception as e:
        print(f"❌ SDK初始化失败: {e}")
        return False

def test_simple_request():
    """测试简单请求"""
    print("\n=== 简单请求测试 ===")
    
    try:
        from volcengine.visual.VisualService import VisualService
        
        vs = VisualService()
        vs.set_ak(JIMENG_ACCESS_KEY_ID)
        vs.set_sk(JIMENG_SECRET_ACCESS_KEY)
        vs.set_host("visual.volcengineapi.com")
        
        # 构建最简单的请求
        body = {
            "req_key": "jimeng_high_aes_general_v21_L",
            "prompt": "一个简单的人物，白色背景",
            "width": 512,
            "height": 512
        }
        
        print(f"发送请求: {body}")
        
        # 提交任务
        submit_resp = vs.cv_sync2async_submit_task(body)
        print(f"提交响应: {submit_resp}")
        
        if submit_resp is None:
            print("❌ 提交响应为None")
            return False
            
        if not isinstance(submit_resp, dict):
            print(f"❌ 提交响应类型错误: {type(submit_resp)}")
            return False
            
        if submit_resp.get("code") != 10000:
            error_msg = submit_resp.get('message', 'Unknown error')
            error_code = submit_resp.get("code")
            print(f"❌ 提交失败 - 错误代码: {error_code}, 错误信息: {error_msg}")
            
            # 分析错误代码
            if error_code == 50400:
                print("🔍 错误分析: 50400 - Access Denied")
                print("可能原因:")
                print("1. API密钥权限不足")
                print("2. 需要在火山引擎控制台配置IAM权限")
                print("3. 服务未开通或已过期")
                print("4. 区域配置错误")
            
            return False
            
        print("✅ 提交成功")
        return True
        
    except Exception as e:
        print(f"❌ 请求测试失败: {e}")
        return False

def check_iam_permissions():
    """检查IAM权限配置"""
    print("\n=== IAM权限检查 ===")
    
    print("请检查以下权限配置:")
    print("1. 登录火山引擎控制台")
    print("2. 进入IAM管理 -> 用户管理")
    print("3. 找到对应的用户或创建新用户")
    print("4. 添加以下权限策略:")
    print("   - VisualServiceFullAccess (视觉服务完全访问权限)")
    print("   - 或者自定义策略包含以下Action:")
    print("     * visual:cv_sync2async_submit_task")
    print("     * visual:cv_sync2async_get_result")
    print("5. 确保用户有对应的AccessKey和SecretKey")
    print("6. 等待5-10分钟让权限生效")

def main():
    """主函数"""
    print("🔍 即梦API权限诊断工具")
    print("=" * 50)
    
    # 1. 测试API连接
    connection_ok = test_api_connection()
    
    # 2. 测试SDK导入
    sdk_ok = test_sdk_import()
    
    # 3. 测试简单请求
    if connection_ok and sdk_ok:
        request_ok = test_simple_request()
    else:
        request_ok = False
    
    # 4. 检查权限配置
    check_iam_permissions()
    
    # 5. 总结
    print("\n" + "=" * 50)
    print("📋 诊断总结:")
    print(f"API连接: {'✅ 正常' if connection_ok else '❌ 失败'}")
    print(f"SDK导入: {'✅ 正常' if sdk_ok else '❌ 失败'}")
    print(f"请求测试: {'✅ 正常' if request_ok else '❌ 失败'}")
    
    if not request_ok:
        print("\n🚨 问题解决建议:")
        print("1. 检查API密钥是否正确")
        print("2. 确认火山引擎服务已开通")
        print("3. 配置正确的IAM权限")
        print("4. 联系火山引擎技术支持")
        print("5. 考虑使用其他图片生成API作为备选方案")

if __name__ == "__main__":
    main()
