from __future__ import print_function

from volcengine.visual.VisualService import VisualService

def generate_white_background_person_image():
    """
    用于生成白底人物图片的简单演示脚本
    """
    # 初始化视觉服务
    visual_service = VisualService()

    # 设置API密钥（请替换为你自己的AK/SK）
    visual_service.set_ak('AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU')
    visual_service.set_sk('TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ==')

    # 构建请求体 - 专门用于生成白底人物照片
    prompt = "一个穿着正装的男人，英俊的面容，深邃的眼神，穿着正装"
    form = {
    "req_key": "high_aes_general_v30l_zt2i",
    "prompt": f"{prompt}, 白色背景, 高清人像摄影, 正面角度, 自然表情, 专业人像, 全身像",
    "seed": -1,
    "scale": 2.5,
    "width": 1328,
    "height": 1328,
    "return_url": True,
    "logo_info": {
        "add_logo": False,
        "position": 0,
        "language": 0,
        "opacity": 0.3,
        "logo_text_content": "这里是明水印内容"
    }
}

    print(f"调用即梦API生成白底人物照片: {prompt}")
    print(f"请求参数: {form}")

    # 提交任务
    resp = visual_service.cv_process(form)
    print(f"即梦API响应: {resp}")

if __name__ == '__main__':
    generate_white_background_person_image()
            