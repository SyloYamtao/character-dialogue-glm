import requests
import time
import os
from typing import Generator
import jwt
from typing import Optional, Iterator
from data_types import TextMsgList, CharacterMeta
from logger import LOG
import streamlit as st

# 智谱开放平台API key，参考 https://open.bigmodel.cn/usercenter/apikeys
ZHIPU_API_KEY: str = os.getenv("ZHIPU_API_KEY")


class ApiKeyNotSet(ValueError):
    pass


def verify_api_key_not_empty():
    if not ZHIPU_API_KEY:
        raise ApiKeyNotSet


def update_api_key():
    current_input_api_key = st.session_state.zhipu_api_key or os.getenv("ZHIPU_API_KEY")
    if current_input_api_key:
        global ZHIPU_API_KEY
        ZHIPU_API_KEY = current_input_api_key


def generate_token(apikey: str, exp_seconds: int) -> str:
    # reference: https://open.bigmodel.cn/dev/api#nosdk
    try:
        id, secret = apikey.split(".")
    except Exception as e:
        raise Exception("invalid apikey", e)

    payload = {
        "api_key": id,
        "exp": int(round(time.time() * 1000)) + exp_seconds * 1000,
        "timestamp": int(round(time.time() * 1000)),
    }

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
        headers={"alg": "HS256", "sign_type": "SIGN"},
    )


def get_chatglm_response_via_sdk(messages: TextMsgList) -> Generator[str, None, None]:
    from zhipuai import ZhipuAI
    verify_api_key_not_empty()
    client = ZhipuAI(api_key=ZHIPU_API_KEY)
    response = client.chat.completions.create(
        model="glm-4",
        messages=messages,
        stream=False,
    )
    LOG.debug(response)

    return response.choices[0].message.content


def get_characterglm_response(messages: TextMsgList, meta: CharacterMeta) -> Generator[str, None, None]:
    """ 通过http调用characterglm """
    # Reference: https://open.bigmodel.cn/dev/api#characterglm
    verify_api_key_not_empty()
    url = "https://open.bigmodel.cn/api/paas/v3/model-api/charglm-3/sse-invoke"
    resp = requests.post(
        url,
        headers={"Authorization": generate_token(ZHIPU_API_KEY, 1800)},
        json=dict(
            model="charglm-3",
            meta=meta,
            prompt=messages,
            incremental=True)
    )
    resp.raise_for_status()
    # 解析响应（非官方实现）
    sep = b':'
    last_event = None
    for line in resp.iter_lines():
        if not line or line.startswith(sep):
            continue
        field, value = line.split(sep, maxsplit=1)
        if field == b'event':
            last_event = value
        elif field == b'data' and last_event == b'add':
            yield value.decode()


def generate_role_appearance(role_profile: str) -> Generator[str, None, None]:
    """ 用chatglm生成角色的外貌描写 """

    instruction = f"""
请从下列文本中，抽取人物的外貌描写。若文本中不包含外貌描写，请你推测人物的性别、年龄，并生成一段外貌描写。要求：
1. 只生成外貌描写，不要生成任何多余的内容。
2. 外貌描写不能包含敏感词，人物形象需得体。
3. 尽量用短语描写，而不是完整的句子。
4. 不要超过50字

文本：
{role_profile}
"""
    return get_chatglm_response_via_sdk(
        messages=[
            {
                "role": "user",
                "content": instruction.strip()
            }
        ]
    )


def generate_cogview_image(prompt: str) -> str:
    """ 调用cogview生成图片，返回url """
    # reference: https://open.bigmodel.cn/dev/api#cogview
    from zhipuai import ZhipuAI
    client = ZhipuAI(api_key=ZHIPU_API_KEY)

    response = client.images.generations(
        model="cogview-3",
        prompt=prompt
    )
    return response.data[0].url


def output_stream_response(response_stream: Iterator[str]):
    content = "".join(response_stream)
    return content
