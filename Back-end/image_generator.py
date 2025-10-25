# coding:utf-8
from __future__ import print_function

from volcengine.visual.VisualService import VisualService

if __name__ == '__main__':
    visual_service = VisualService()

    # call below method if you don't set ak and sk in $HOME/.volc/config
    visual_service.set_ak('AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU')
    visual_service.set_sk('TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ==')
    
    # 请求Body(查看接口文档请求参数-请求示例，将请求参数内容复制到此)
    form = {
    "req_key": "high_aes_general_v30l_zt2i",
    "prompt": "千军万马",
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

    resp = visual_service.cv_process(form)
    print(resp)