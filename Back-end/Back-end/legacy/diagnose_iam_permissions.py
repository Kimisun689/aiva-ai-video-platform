import json
import time
from datetime import datetime

def diagnose_iam_permissions():
    """
    诊断IAM权限配置问题
    根据火山引擎文档分析可能的权限问题
    """
    print("=== IAM权限配置诊断 ===")
    print(f"诊断时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 当前使用的AK/SK
    current_ak = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
    current_sk = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="
    
    print(f"\n当前使用的AK: {current_ak}")
    print(f"当前使用的SK: {current_sk[:10]}...")
    
    # 问题分析
    print("\n🔍 问题分析:")
    print("错误代码: 50400")
    print("错误信息: Access Denied: api forbidden")
    print("这表明是权限配置问题，不是服务未开通问题")
    
    # 可能的权限问题
    print("\n📋 可能的权限问题:")
    
    issues = [
        {
            "type": "Action权限不足",
            "description": "缺少Jimeng图像生成相关的Action权限",
            "required_actions": [
                "visual:SubmitTask",
                "visual:GetResult", 
                "visual:*"
            ],
            "solution": "在IAM策略中添加视觉智能服务的Action权限"
        },
        {
            "type": "Resource权限不足", 
            "description": "没有访问视觉智能服务资源的权限",
            "required_resources": [
                "arn:volcengine:visual:*:*:*",
                "arn:volcengine:visual:*:*:task/*"
            ],
            "solution": "在IAM策略中添加视觉智能服务的Resource权限"
        },
        {
            "type": "缓存问题",
            "description": "IAM策略配置后需要5-10分钟生效",
            "solution": "等待10分钟后重试，或清除缓存"
        },
        {
            "type": "AK/SK权限范围",
            "description": "当前AK/SK可能只配置了部分服务权限",
            "solution": "检查AK/SK的权限范围，确认包含视觉智能服务"
        }
    ]
    
    for i, issue in enumerate(issues, 1):
        print(f"\n{i}. {issue['type']}")
        print(f"   描述: {issue['description']}")
        if 'required_actions' in issue:
            print(f"   需要的Action: {', '.join(issue['required_actions'])}")
        if 'required_resources' in issue:
            print(f"   需要的Resource: {', '.join(issue['required_resources'])}")
        print(f"   解决方案: {issue['solution']}")
    
    # 解决步骤
    print("\n🛠️ 解决步骤:")
    steps = [
        "1. 登录火山引擎控制台",
        "2. 进入IAM管理 → 用户管理",
        "3. 找到当前AK对应的用户",
        "4. 检查该用户的权限策略",
        "5. 确认是否包含视觉智能服务权限",
        "6. 如缺少权限，添加以下策略:",
        "   - Action: visual:*",
        "   - Resource: arn:volcengine:visual:*:*:*",
        "7. 保存策略后等待5-10分钟",
        "8. 重新测试API调用"
    ]
    
    for step in steps:
        print(f"   {step}")
    
    # 推荐的IAM策略
    print("\n📝 推荐的IAM策略配置:")
    recommended_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": [
                    "visual:SubmitTask",
                    "visual:GetResult",
                    "visual:ListTasks"
                ],
                "Resource": [
                    "arn:volcengine:visual:*:*:*",
                    "arn:volcengine:visual:*:*:task/*"
                ]
            }
        ]
    }
    
    print(json.dumps(recommended_policy, indent=2, ensure_ascii=False))
    
    # 验证建议
    print("\n✅ 验证建议:")
    print("1. 配置权限后等待10分钟")
    print("2. 使用以下命令重新测试:")
    print("   python3 test_volcengine_doc_compliance.py")
    print("3. 如果仍有问题，检查:")
    print("   - 用户是否被禁用")
    print("   - 账户是否有欠费")
    print("   - 服务配额是否充足")

def check_alternative_solutions():
    """检查替代解决方案"""
    print("\n🔄 替代解决方案:")
    alternatives = [
        {
            "方案": "创建新的AK/SK",
            "步骤": [
                "1. 在控制台创建新的访问密钥",
                "2. 确保新密钥有完整的视觉智能权限",
                "3. 更新代码中的AK/SK",
                "4. 测试API调用"
            ]
        },
        {
            "方案": "使用STS临时凭证",
            "步骤": [
                "1. 获取STS临时访问凭证",
                "2. 使用临时凭证进行API调用",
                "3. 定期刷新临时凭证"
            ]
        },
        {
            "方案": "联系技术支持",
            "步骤": [
                "1. 提供错误代码50400",
                "2. 提供当前AK/SK信息",
                "3. 请求权限配置协助"
            ]
        }
    ]
    
    for alt in alternatives:
        print(f"\n📌 {alt['方案']}:")
        for step in alt['步骤']:
            print(f"   {step}")

if __name__ == "__main__":
    diagnose_iam_permissions()
    check_alternative_solutions() 