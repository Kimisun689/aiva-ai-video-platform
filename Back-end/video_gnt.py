# coding:utf-8
from __future__ import print_function

from volcengine.visual.VisualService import VisualService

if __name__ == '__main__':
    visual_service = VisualService()

    # call below method if you don't set ak and sk in $HOME/.volc/config
    visual_service.set_ak('your ak')
    visual_service.set_sk('your sk')
    
    # 请求Body(查看接口文档请求参数-请求示例，将请求参数内容复制到此)
    form = {
    "req_key": "jimeng_vgfm_t2v_l20",
    "prompt": "镜头：黑底金粒子汇聚成Virtec Logo，炸裂成星轨"
}

    resp = visual_service.cv_process(form)
    print(resp)