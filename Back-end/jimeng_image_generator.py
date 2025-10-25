#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
火山引擎即梦图像生成器
基于官方文档: https://www.volcengine.com/docs/85621/1537648
"""

import json
import time
import base64
import os
from datetime import datetime
from volcengine.visual.VisualService import VisualService

class JimengImageGenerator:
    """火山引擎即梦图像生成器"""
    
    def __init__(self):
        """初始化服务"""
        # 你的AK/SK
        self.AK = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
        self.SK = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="
        
        # 初始化视觉服务
        self.visual_service = VisualService()
        self.visual_service.set_ak(self.AK)
        self.visual_service.set_sk(self.SK)
        self.visual_service.set_host("visual.volcengineapi.com")
        
        print(f"✅ 初始化完成 - AK: {self.AK[:10]}...")
    
    def generate_image(self, prompt, **kwargs):
        """
        生成图像
        
        Args:
            prompt (str): 图像描述文本
            **kwargs: 其他参数
                - req_key (str): 模型版本，默认 'jimeng_high_aes_general_v21_L'
                - width (int): 图片宽度，默认 512
                - height (int): 图片高度，默认 512
                - seed (int): 随机种子，可选
                - use_sr (bool): 是否使用超分辨率，默认 False
                - use_pre_llm (bool): 是否使用预处理，默认 False
                - return_url (bool): 是否返回URL，默认 False
        
        Returns:
            dict: 生成结果
        """
        # 默认参数
        default_params = {
            "req_key": "jimeng_high_aes_general_v21_L",
            "prompt": prompt,
            "width": kwargs.get('width', 512),
            "height": kwargs.get('height', 512),
            "use_sr": kwargs.get('use_sr', False),
            "use_pre_llm": kwargs.get('use_pre_llm', False),
            "return_url": kwargs.get('return_url', True)  # 默认返回URL
        }
        
        # 添加可选参数
        if 'seed' in kwargs:
            default_params['seed'] = kwargs['seed']
        
        print(f"🎨 开始生成图像...")
        print(f"📝 提示词: {prompt}")
        print(f"📐 尺寸: {default_params['width']}x{default_params['height']}")
        print(f"🔧 参数: {json.dumps(default_params, ensure_ascii=False, indent=2)}")
        
        try:
            # 提交任务
            print("\n⏳ 正在提交生成任务...")
            submit_result = self.visual_service.cv_sync2async_submit_task(default_params)
            
            print(f"📤 提交响应: {json.dumps(submit_result, ensure_ascii=False, indent=2)}")
            
            if submit_result.get('code') != 10000:
                error_msg = submit_result.get('message', 'Unknown error')
                print(f"❌ 任务提交失败: {error_msg}")
                return None
            
            # 获取任务ID
            task_id = submit_result.get('data', {}).get('task_id')
            if not task_id:
                print("❌ 未获取到任务ID")
                return None
            
            print(f"✅ 任务提交成功，任务ID: {task_id}")
            
            # 轮询获取结果
            return self._poll_result(task_id, default_params['req_key'])
            
        except Exception as e:
            print(f"❌ 生成图像时发生异常: {str(e)}")
            if "50400" in str(e) and "Access Denied" in str(e):
                print("\n🔍 这是权限问题！请检查:")
                print("1. 火山引擎控制台是否已开通视觉智能服务")
                print("2. IAM权限是否包含 visual:* 权限")
                print("3. 账户是否有欠费")
                print("4. AK/SK是否正确且有效")
            return None
    
    def _poll_result(self, task_id, req_key, max_attempts=30, interval=2):
        """
        轮询获取结果
        
        Args:
            task_id (str): 任务ID
            req_key (str): 请求键
            max_attempts (int): 最大尝试次数
            interval (int): 轮询间隔(秒)
        
        Returns:
            dict: 最终结果
        """
        print(f"\n🔄 开始轮询结果，最多尝试 {max_attempts} 次...")
        
        for attempt in range(max_attempts):
            try:
                time.sleep(interval)
                
                query_params = {
                    "task_id": task_id,
                    "req_key": req_key
                }
                
                result = self.visual_service.cv_sync2async_get_result(query_params)
                
                print(f"📊 第 {attempt + 1} 次查询: {result.get('code')} - {result.get('message')}")
                
                if result.get('code') != 10000:
                    print(f"⚠️ 查询失败: {result.get('message')}")
                    continue
                
                data = result.get('data', {})
                status = data.get('status')
                
                if status == 'done' or status == 2:
                    print("✅ 图像生成完成!")
                    return self._process_success_result(data)
                elif status == 'failed' or status == 3:
                    print("❌ 图像生成失败")
                    print(f"失败原因: {data.get('reason', 'Unknown')}")
                    return None
                elif status == 'pending' or status == 1:
                    print(f"⏳ 生成中... (第{attempt + 1}次查询)")
                    continue
                else:
                    print(f"🤔 未知状态: {status}")
                    continue
                    
            except Exception as e:
                print(f"⚠️ 第 {attempt + 1} 次查询异常: {str(e)}")
                continue
        
        print(f"⏰ 轮询超时，已尝试 {max_attempts} 次")
        return None
    
    def _process_success_result(self, data):
        """
        处理成功结果
        
        Args:
            data (dict): 结果数据
        
        Returns:
            dict: 处理后的结果
        """
        result = {
            'success': True,
            'task_id': data.get('task_id'),
            'status': data.get('status'),
            'image_urls': [],
            'base64_images': [],
            'saved_files': []
        }
        
        # 处理图片URL
        image_urls = data.get('image_urls', [])
        if image_urls:
            result['image_urls'] = image_urls
            print(f"🖼️ 获得图片URL: {len(image_urls)} 张")
            for i, url in enumerate(image_urls, 1):
                print(f"   {i}. {url}")
        
        # 处理base64图片数据（如果有的话）
        binary_data_base64_list = data.get('binary_data_base64', [])
        if binary_data_base64_list:
            result['base64_images'] = binary_data_base64_list
            print(f"📦 获得base64图片: {len(binary_data_base64_list)} 张")
            
            # 保存base64图片到文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            for i, base64_data in enumerate(binary_data_base64_list, 1):
                filename = f"generated_image_{timestamp}_{i}.png"
                filepath = self._save_base64_image(base64_data, filename)
                if filepath:
                    result['saved_files'].append(filepath)
                    print(f"💾 已保存: {filepath}")
        
        # 如果既没有URL也没有base64，输出警告
        if not image_urls and not binary_data_base64_list:
            print("⚠️ 未获得图片URL或base64数据")
        
        return result
    
    def _save_base64_image(self, base64_data, filename):
        """
        保存base64图片到文件
        
        Args:
            base64_data (str): base64编码的图片数据
            filename (str): 文件名
        
        Returns:
            str: 保存的文件路径，失败返回None
        """
        try:
            # 创建images目录
            images_dir = "generated_images"
            os.makedirs(images_dir, exist_ok=True)
            
            # 解码base64数据
            image_data = base64.b64decode(base64_data)
            
            # 保存文件
            filepath = os.path.join(images_dir, filename)
            with open(filepath, 'wb') as f:
                f.write(image_data)
            
            return filepath
            
        except Exception as e:
            print(f"❌ 保存图片失败: {str(e)}")
            return None
    
    def generate_character_image(self, character_name, character_description, background="white"):
        """
        生成角色图像（专用于角色一致性）
        
        Args:
            character_name (str): 角色名称
            character_description (str): 角色描述
            background (str): 背景颜色，默认白色
        
        Returns:
            dict: 生成结果
        """
        # 构建专用于角色的提示词
        prompt = f"A portrait of {character_name}, {character_description}, {background} background, high quality, detailed, professional photography style"
        
        print(f"👤 生成角色图像: {character_name}")
        
        return self.generate_image(
            prompt=prompt,
            width=512,
            height=512,
            use_sr=True,  # 角色图像使用超分辨率
            use_pre_llm=True,  # 使用预处理优化提示词
            return_url=True  # 返回URL而不是base64
        )
    
    def test_connection(self):
        """
        测试连接和权限
        
        Returns:
            bool: 连接是否成功
        """
        print("🔧 测试连接和权限...")
        
        test_prompt = "a simple red apple on white background"
        result = self.generate_image(test_prompt, width=256, height=256, return_url=True)
        
        if result and result.get('success'):
            print("✅ 连接测试成功!")
            return True
        else:
            print("❌ 连接测试失败!")
            return False

def main():
    """主函数 - 演示使用"""
    print("=== 火山引擎即梦图像生成器 ===")
    print("基于官方文档实现")
    print()
    
    # 初始化生成器
    generator = JimengImageGenerator()
    
    # 测试连接
    if not generator.test_connection():
        print("\n❌ 连接测试失败，请检查权限配置")
        return
    
    # 示例1: 生成简单图像
    print("\n" + "="*50)
    print("示例1: 生成简单图像")
    result1 = generator.generate_image(
        prompt="a beautiful sunset over mountains, digital art style",
        width=512,
        height=512,
        return_url=True
    )
    
    if result1:
        print(f"✅ 生成成功: {len(result1.get('saved_files', []))} 张图片已保存")
    
    # 示例2: 生成角色图像
    print("\n" + "="*50)
    print("示例2: 生成角色图像")
    result2 = generator.generate_character_image(
        character_name="Alice",
        character_description="young woman with long brown hair, wearing a blue dress, friendly smile"
    )
    
    if result2:
        print(f"✅ 角色生成成功: {len(result2.get('saved_files', []))} 张图片已保存")

if __name__ == "__main__":
    main()
