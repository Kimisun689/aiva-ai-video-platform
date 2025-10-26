"""
AI Service Integrations and Helper Functions
"""
import httpx
import json
import hashlib
import hmac
import base64
import re
import asyncio
from datetime import datetime

# API Keys and Configuration - imported from config
from backend.config import DEEPSEEK_API_KEY, DEEPSEEK_API_URL, JIMENG_ACCESS_KEY_ID, JIMENG_SECRET_ACCESS_KEY

BYTEDANCE_ACCESS_KEY_ID = "AKLTMTE0YWY5OTI3YThjNDNiMDlmNGRmNWY5YWY1Y2M5MDI"
BYTEDANCE_SECRET_ACCESS_KEY = "WlRobU9UaGlPREl6WlRNMk5HVmlZV0prWlRGa01tTXhOR1JsTURZNFpHRQ=="


SHOT_IMAGE_ACCESS_KEY_ID = "AKLTNzY0YTgxZjk1MmRlNDU3MDk2MDg1NGVmMDE3MGFlZjU"
SHOT_IMAGE_SECRET_ACCESS_KEY = "TkdOa1pXTXlZMkppTjJFMk5HUmlZbUprWWpnNU5UZGtOall4WW1OaU5HUQ=="

HAILUO_API_KEY = "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJHcm91cE5hbWUiOiLlrZnplKbmt7siLCJVc2VyTmFtZSI6IuWtmemUpua3uyIsIkFjY291bnQiOiIiLCJTdWJqZWN0SUQiOiIxOTUxMTE2MDg5NTk3MzcxMDQ0IiwiUGhvbmUiOiIxMzcwMTE2NDgxNiIsIkdyb3VwSUQiOiIxOTUxMTE2MDg5NTg4OTgyNDM2IiwiUGFnZU5hbWUiOiIiLCJNYWlsIjoiIiwiQ3JlYXRlVGltZSI6IjIwMjUtMDgtMTEgMTA6MTQ6MDIiLCJUb2tlblR5cGUiOjEsImlzcyI6Im1pbmltYXgifQ.ce-7TXB4JC9R31woacWZFx_ZChK35h-KpGriEljduvaYg0Ws-1ECVUnI9SCY_9QX6DzHXFbjNsN2cg-WBPPMJPdUoI4Ynf4jx1XXW6IzgIM4swKNfwMWOTCDJ9_VNKvTpUnEDK9gX4mfSFwkdB62zdMOUgDQONh1GditOurfGsT9UMG4w6jczypl7I4PBG4uO5E-vjRuvV9Hr3g9CGXPMk3iJ-A6-3Y5uZMX1XKWo_l5mPxWls_O8YudULhUPeVq8CJSA5lpLAgkcpj6_Nx8827uKbKyjpjJ1CW1oBt3lk5RxR6JgwichJKZnt0oMEkAGW2FMbbJJl3KK4-pKu282w"

# Try to import Volcengine SDK
try:
    from volcengine.visual.VisualService import VisualService
    BYTEDANCE_AVAILABLE = True
    print("✅ 火山引擎SDK导入成功")
except ImportError:
    BYTEDANCE_AVAILABLE = False
    print("⚠️ 警告: 火山引擎SDK未安装，字节跳动AI功能将被禁用")

# ==================== DeepSeek AI Functions ====================

async def get_deepseek_script(prompt: str) -> str:
    """
    使用DeepSeek AI生成视频剧本

    Args:
        prompt (str): 用户输入的提示词

    Returns:
        str: AI生成的完整剧本内容

    Raises:
        Exception: 当API调用失败时抛出异常
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "You are a AI video script writer, you will be given a video prompt and you will need to generate a long video prompt that will be used for anouther ai to generate a video, this script may but not must contain the detail of the image, the background, the communication, ect.Just give the script, don't give any other text like of course or would you like to adjust."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]

async def get_deepseek_breakdown(script: str) -> dict:
    """
    使用DeepSeek AI将剧本拆解成分镜列表和对话列表

    Args:
        script (str): 完整的剧本内容

    Returns:
        dict: 包含分镜列表和对话列表的字典
            {
                "shots": [...],      # 分镜列表
                "dialogues": [...]   # 对话列表
            }
    """
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content":
                "You are a professional video director and script analyst. "
                "You are given a script an you need to break it down into a list of shot-by-shot prompts. Each shot should contain the background, the action, the emotion. if there are dialoges involved inthe shot, just output someone said something. "
                "Return your answer in strict JSON format: {\"shots\": [...], \"dialogues\": [...]} . Do not add any extra explanation or text."
            },
            {"role": "user", "content": script}
        ],
        "temperature": 0.5
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"]
        # 解析 JSON
        try:
            parsed = json.loads(content)
            shots = parsed.get("shots", [])
            dialogues = parsed.get("dialogues", [])
        except Exception:
            # fallback: 只拆分 shots
            shots = [s.strip("- ").strip() for s in content.strip().split("\n") if s.strip()]
            dialogues = []
        return {"shots": shots, "dialogues": dialogues}

# ==================== Volcengine Signature Generation ====================

# ==================== HaiLuo AI Helper ====================

def extract_hailuo_group_id_from_token(token):
    """
    从海螺AI JWT token中提取GroupId

    海螺AI使用JWT token进行认证，其中包含了GroupId信息。
    此函数解析JWT token的payload部分，提取GroupId用于API调用。

    Args:
        token (str): 海螺AI的JWT token

    Returns:
        str: 提取到的GroupId，如果提取失败则返回空字符串

    Note:
        JWT token由三部分组成：header.payload.signature
        我们只需要解析payload部分来获取GroupId
    """
    try:
        import base64
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
        print(f"提取海螺AI GroupId失败: {e}")
    return ''

async def get_deepseek_characters_only(script: str) -> list:
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content":
                "You are a professional script analyst. Given a full video script, identify all characters and extract their information. "
                "For each character, provide: name, gender, age range, appearance description, personality traits, and role in the story. "
                "Output as a JSON array of objects with the following structure: "
                "[{\"name\": \"character_name\", \"gender\": \"male/female/other\", \"age_range\": \"20s/30s/etc\", "
                "\"appearance\": \"detailed appearance description\", \"personality\": \"personality traits\", "
                "\"role\": \"main character/supporting character/etc\"}]. "
                "Output only the JSON array, no extra text, no markdown, no explanation."
            },
            {"role": "user", "content": script}
        ],
        "temperature": 0.3
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(DEEPSEEK_API_URL, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        content = result["choices"][0]["message"]["content"].strip()

        # Remove markdown/code block if present
        if content.startswith("```") and content.endswith("```"):
            content = re.sub(r"^```[a-zA-Z]*", "", content)
            content = content.rstrip("`").strip()

        # Try to parse as JSON array
        try:
            characters = json.loads(content)
            if not isinstance(characters, list):
                characters = []
        except Exception as e:
            print(f"Error parsing characters JSON: {e}")
            print(f"Raw content: {content}")
            characters = []

        return characters

async def generate_character_image(character_name: str, character_info: dict) -> dict:
    """为单个人物生成白色背景图片"""
    try:
        # 构建文生图提示词
        gender = character_info.get('gender', '')
        age_range = character_info.get('age_range', '')
        appearance = character_info.get('appearance', '')
        personality = character_info.get('personality', '')

        # 性别中文转换
        gender_cn = '男性' if gender == 'male' else '女性' if gender == 'female' else '人物'

        # 年龄中文转换
        age_cn = age_range.replace('s', '多岁') if age_range else ''

        # 构建提示词
        prompt = f"一个{age_cn}的{gender_cn}，{appearance}，{personality}"

        print(f"生成人物图片提示词: {prompt}")

        # 使用HTTP方式调用火山引擎API，按照官方文档要求
        try:
            import hashlib
            import hmac
            from datetime import datetime

            # API端点
            api_url = "https://visual.volcengineapi.com?Action=CVProcess&Version=2022-08-31"

            # 构建请求数据
            data = {
                "req_key": "high_aes_general_v30l_zt2i",  # 即梦高画质通用模型
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

            # 构建规范请求参数
            http_method = 'POST'
            canonical_uri = '/'
            canonical_querystring = 'Action=CVProcess&Version=2022-08-31'

            # 时间戳 - 使用Unix时间戳格式（符合火山引擎要求）
            timestamp = str(int(datetime.utcnow().timestamp()))
            canonical_headers = f'accept:application/json\ncontent-type:application/json\nhost:visual.volcengineapi.com\nuser-agent:AIVA-Video-Platform/1.0\nx-date:{timestamp}\n'
            signed_headers = 'accept;content-type;host;user-agent;x-date'

            # 计算请求体哈希
            payload_hash = hashlib.sha256(json.dumps(data, separators=(',', ':')).encode('utf-8')).hexdigest()

            # 生成签名
            authorization_header = generate_volc_signature(
                JIMENG_ACCESS_KEY_ID,
                JIMENG_SECRET_ACCESS_KEY,
                http_method,
                canonical_uri,
                canonical_querystring,
                canonical_headers,
                signed_headers,
                payload_hash
            )

            headers = {
                "Authorization": authorization_header,
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "AIVA-Video-Platform/1.0",
                "X-Date": timestamp,
                "Host": "visual.volcengineapi.com"
            }

            print(f"调用即梦API生成人物图片: {character_name}")
            print(f"请求URL: {api_url}")
            print(f"提示词: {data['prompt']}")

            # 发送请求
            print(f"🔍 REQUEST DETAILS:")
            print(f"   URL: {api_url}")
            print(f"   Headers: {json.dumps(headers, indent=2, default=str)}")
            print(f"   Data: {json.dumps(data, indent=2)}")

            async with httpx.AsyncClient(timeout=60) as client:
                response = await client.post(api_url, headers=headers, json=data)

            print(f"🔍 RESPONSE DETAILS:")
            print(f"   Status: {response.status_code}")
            print(f"   Headers: {dict(response.headers)}")
            print(f"   Body: {response.text[:2000]}...")

            response.raise_for_status()
            resp = response.json()

            print(f"✅ 即梦API响应: {json.dumps(resp, indent=2)}")

            # 检查响应
            if not isinstance(resp, dict):
                return {"success": False, "error": f"API返回格式错误: {type(resp)}"}

            # 检查结果
            if "Result" not in resp:
                return {"success": False, "error": f"API响应中缺少Result字段: {resp}"}

            result = resp["Result"]

            # 检查任务ID
            if "task_id" not in result:
                return {"success": False, "error": f"响应中缺少task_id: {result}"}

            task_id = result["task_id"]
            print(f"任务ID: {task_id}")

            # 轮询任务状态，最多等待300秒
            max_wait_time = 300
            wait_time = 0
            poll_interval = 5

            while wait_time < max_wait_time:
                try:
                    # 查询任务状态 - 需要重新签名
                    query_timestamp = str(int(datetime.utcnow().timestamp()))
                    query_canonical_headers = f'accept:application/json\ncontent-type:application/json\nhost:visual.volcengineapi.com\nuser-agent:AIVA-Video-Platform/1.0\nx-date:{query_timestamp}\n'
                    query_signed_headers = 'accept;content-type;host;user-agent;x-date'

                    query_data = {"task_id": task_id}
                    query_payload_hash = hashlib.sha256(json.dumps(query_data, separators=(',', ':')).encode('utf-8')).hexdigest()

                    query_authorization = generate_volc_signature(
                        JIMENG_ACCESS_KEY_ID,
                        JIMENG_SECRET_ACCESS_KEY,
                        'POST',
                        '/',
                        'Action=GetImgResponse&Version=2022-08-31',
                        query_canonical_headers,
                        query_signed_headers,
                        query_payload_hash,
                        query_timestamp
                    )

                    query_headers = {
                        "Authorization": query_authorization,
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "User-Agent": "AIVA-Video-Platform/1.0",
                        "X-Date": query_timestamp,
                        "Host": "visual.volcengineapi.com"
                    }

                    query_url = "https://visual.volcengineapi.com?Action=GetImgResponse&Version=2022-08-31"

                    print(f"🔍 POLLING REQUEST:")
                    print(f"   URL: {query_url}")
                    print(f"   Data: {json.dumps(query_data, indent=2)}")

                    async with httpx.AsyncClient(timeout=30) as client:
                        status_response = await client.post(query_url, headers=query_headers, json=query_data)

                    print(f"🔍 POLLING RESPONSE:")
                    print(f"   Status: {status_response.status_code}")
                    print(f"   Body: {status_response.text[:1000]}...")

                    status_response.raise_for_status()
                    status_resp = status_response.json()

                    print(f"任务状态查询响应: {status_resp}")

                    if status_resp and isinstance(status_resp, dict) and "Result" in status_resp:
                        result_data = status_resp["Result"]

                        if result_data.get("task_status") == "SUCCEEDED":
                            # 任务完成
                            images = result_data.get("image_urls", [])
                            if images and len(images) > 0:
                                image_url = images[0]
                                print(f"人物 {character_name} 图片生成成功: {image_url}")
                                return {
                                    "success": True,
                                    "image_url": image_url,
                                    "task_id": task_id
                                }
                            else:
                                return {"success": False, "error": "未获取到图片URL"}
                        elif result_data.get("task_status") == "FAILED":
                            # 任务失败
                            return {"success": False, "error": f"任务失败: {result_data.get('task_status_msg', '未知错误')}"}
                        else:
                            # 任务进行中，继续等待
                            print(f"任务状态: {result_data.get('task_status', 'UNKNOWN')}，等待中...")
                    else:
                        print(f"无效的状态响应: {status_resp}")

                except Exception as e:
                    print(f"查询任务状态时出错: {e}")

                # 等待后重试
                await asyncio.sleep(poll_interval)
                wait_time += poll_interval

            # 超时
            return {"success": False, "error": f"任务超时 (等待{wait_time}秒)"}

        except Exception as e:
            print(f"HTTP方式生成人物图片失败: {e}")
            return {"success": False, "error": str(e)}

    except Exception as e:
        print(f"生成人物 {character_name} 图片时发生异常: {e}")
        return {"success": False, "error": str(e)}

async def generate_character_image_http(character_name: str, character_info: dict, prompt: str) -> dict:
    """HTTP方式生成人物图片（备用方法）"""
    try:
        # 构建请求体
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

        print(f"HTTP方式调用即梦API生成人物图片: {character_name}")
        print(f"请求参数: {form}")

        # 这里应该实现HTTP调用逻辑，但由于复杂的签名认证，先返回错误
        return {"success": False, "error": "HTTP方式暂未实现，请安装火山引擎SDK"}

    except Exception as e:
        print(f"HTTP方式生成人物图片失败: {e}")
        return {"success": False, "error": str(e)}

async def generate_all_character_images() -> dict:
    """为所有识别出的人物生成图片 - 顺序生成，每次一张，间隔5秒"""
    try:
        # 获取最新的人物识别结果
        from backend.models import CharacterExtract
        from backend.config import async_session
        from sqlalchemy.future import select

        async with async_session() as session:
            result = await session.execute(
                select(CharacterExtract).order_by(CharacterExtract.id.desc()).limit(1)
            )
            latest_extract = result.scalar_one_or_none()

            if not latest_extract:
                return {"success": False, "error": "没有找到人物识别结果"}

            characters = json.loads(latest_extract.characters)
            print(f"找到 {len(characters)} 个人物需要生成图片")

            results = []
            for i, character in enumerate(characters):
                character_name = character.get('name', '')
                print(f"正在处理第 {i+1}/{len(characters)} 个人物: {character_name}")

                # 检查是否已经生成过图片（只检查最新的成功记录）
                from backend.models import CharacterImage
                existing_result = await session.execute(
                    select(CharacterImage)
                    .where(CharacterImage.character_name == character_name)
                    .where(CharacterImage.status == 'success')
                    .order_by(CharacterImage.id.desc())
                    .limit(1)
                )
                existing_image = existing_result.scalar_one_or_none()

                if existing_image:
                    print(f"人物 {character_name} 已有成功图片，跳过生成")
                    results.append({
                        "character_name": character_name,
                        "status": "already_exists",
                        "image_url": existing_image.image_url
                    })
                    continue

                # 生成新图片 - 重试直到成功
                max_retries = 3
                retry_count = 0
                image_result = None

                while retry_count < max_retries:
                    try:
                        print(f"开始生成人物 {character_name} 的图片... (尝试 {retry_count + 1}/{max_retries})")
                        image_result = await generate_character_image(character_name, character)

                        if image_result['success']:
                            print(f"人物 {character_name} 图片生成成功")
                            break
                        else:
                            print(f"人物 {character_name} 图片生成失败: {image_result.get('error', '未知错误')}")
                            retry_count += 1
                            if retry_count < max_retries:
                                print(f"等待5秒后重试...")
                                await asyncio.sleep(5)

                    except Exception as e:
                        print(f"生成人物 {character_name} 图片时发生异常: {e}")
                        retry_count += 1
                        if retry_count < max_retries:
                            print(f"等待5秒后重试...")
                            await asyncio.sleep(5)

                # 保存到数据库
                if image_result and image_result['success']:
                    character_image = CharacterImage(
                        character_name=character_name,
                        character_info=json.dumps(character, ensure_ascii=False),
                        image_url=image_result.get('image_url', ''),
                        task_id=image_result.get('task_id', ''),
                        status='success',
                        error_message=''
                    )

                    session.add(character_image)
                    await session.commit()

                    results.append({
                        "character_name": character_name,
                        "status": "success",
                        "image_url": image_result.get('image_url', ''),
                        "error": ""
                    })
                else:
                    # 保存失败记录
                    character_image = CharacterImage(
                        character_name=character_name,
                        character_info=json.dumps(character, ensure_ascii=False),
                        image_url='',
                        task_id='',
                        status='failed',
                        error_message=image_result.get('error', '生成失败') if image_result else '未知错误'
                    )

                    session.add(character_image)
                    await session.commit()

                    results.append({
                        "character_name": character_name,
                        "status": "failed",
                        "image_url": "",
                        "error": image_result.get('error', '生成失败') if image_result else '未知错误'
                    })

                # 如果不是最后一个人物，等待5秒再处理下一个
                if i < len(characters) - 1:
                    print(f"等待5秒后处理下一个人物...")
                    await asyncio.sleep(5)

            successful_count = len([r for r in results if r['status'] == 'success'])
            total_count = len(characters)

            print(f"所有人物图片生成完成，成功: {successful_count}/{total_count}")

            # If no characters were successfully generated, consider it a failure
            if successful_count == 0:
                return {
                    "success": False,
                    "error": f"Failed to generate images for any of the {total_count} characters",
                    "results": results,
                    "total_characters": total_count
                }

            return {
                "success": True,
                "results": results,
                "total_characters": total_count
            }

    except Exception as e:
        print(f"生成所有人物图片错误: {e}")
        return {"success": False, "error": str(e)}

def generate_volc_signature(access_key_id, secret_access_key, http_method, canonical_uri, canonical_querystring, canonical_headers, signed_headers, payload_hash, timestamp):
    """
    生成火山引擎API签名 - 基于AWS4签名算法

    Args:
        access_key_id (str): 访问密钥ID
        secret_access_key (str): 秘密访问密钥
        http_method (str): HTTP方法（GET, POST等）
        canonical_uri (str): 规范化的URI路径
        canonical_querystring (str): 规范化的查询字符串
        canonical_headers (str): 规范化的请求头
        signed_headers (str): 已签名的请求头列表
        payload_hash (str): 请求体的哈希值
        timestamp (str): Unix时间戳字符串

    Returns:
        str: 完整的授权头
    """
    from datetime import datetime

    # 1. 创建规范请求 - 按照AWS4标准格式化请求
    canonical_request = http_method + '\n' + canonical_uri + '\n' + canonical_querystring + '\n' + canonical_headers + '\n' + signed_headers + '\n' + payload_hash

    # 2. 创建待签名字符串 - 包含算法、时间戳、凭证范围等
    algorithm = 'AWS4-HMAC-SHA256'
    # timestamp is passed in as Unix timestamp string, convert to datetime for date extraction
    timestamp_int = int(timestamp)
    date = datetime.utcfromtimestamp(timestamp_int).strftime('%Y%m%d')  # Extract YYYYMMDD for credential scope
    credential_scope = date + '/cn-north-1/cv/aws4_request'  # 火山引擎的凭证范围

    string_to_sign = algorithm + '\n' + timestamp + '\n' + credential_scope + '\n' + hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()

    # 3. 计算签名密钥 - 使用HMAC-SHA256算法生成签名密钥
    k_date = hmac.new(('AWS4' + secret_access_key).encode('utf-8'), date.encode('utf-8'), hashlib.sha256).digest()
    k_region = hmac.new(k_date, 'cn-north-1'.encode('utf-8'), hashlib.sha256).digest()
    k_service = hmac.new(k_region, 'cv'.encode('utf-8'), hashlib.sha256).digest()
    k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
    signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

    # 4. 创建授权头 - 组合所有签名信息
    authorization_header = algorithm + ' ' + 'Credential=' + access_key_id + '/' + credential_scope + ', ' + 'SignedHeaders=' + signed_headers + ', ' + 'Signature=' + signature

    return authorization_header

# Additional service functions will be extracted from main.py here
