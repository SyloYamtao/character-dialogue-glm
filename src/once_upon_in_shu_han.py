import os
import streamlit as st
import json
import datetime

from typing import Optional, List
from dotenv import load_dotenv
from logger import LOG
from functions import ZHIPU_API_KEY, verify_api_key_not_empty, get_chatglm_response_via_sdk, update_api_key, \
    get_characterglm_response, \
    generate_role_appearance, \
    generate_cogview_image, output_stream_response
from data_types import TextMsg, CharacterMeta

load_dotenv()
st.set_page_config(page_title="Character Dialogue GLM", page_icon="🤖", layout="wide")


def init_session():
    st.session_state["history"] = []
    st.session_state["meta"] = {
        "bot_name": "",
        "bot_info": "",
        "bot_image_path": "",
        "user_name": "",
        "user_info": "",
        "user_image_path": ""
    }


def verify_meta() -> bool:
    if st.session_state["meta"]["bot_name"] == "" or st.session_state["meta"]["bot_info"] == "" or \
            st.session_state["meta"]["user_name"] == "" or st.session_state["meta"]["user_info"] == "":
        st.error("角色名和角色人设不能为空")
        return False
    else:
        return True


def swap_roles(text_messages: List[TextMsg]) -> List[TextMsg]:
    result_messages = []
    for msg in text_messages:
        if msg["role"] == "user":
            new_role = "assistant"
        elif msg["role"] == "assistant":
            new_role = "user"
        new_msg = TextMsg({"role": new_role, "content": msg["content"]})
        result_messages.append(new_msg)
    return result_messages


def swap_character_meta(org: CharacterMeta) -> CharacterMeta:
    result = CharacterMeta(
        user_name=org['bot_name'],
        user_info=org['bot_info'],
        bot_name=org['user_name'],
        bot_info=org['user_info']
    )
    return result


def role1_chat():
    if not verify_meta():
        return
    if not ZHIPU_API_KEY:
        st.error("未设置API_KEY")

    text_messages = swap_roles(st.session_state["history"])
    response_stream = get_characterglm_response(text_messages, meta=swap_character_meta(st.session_state["meta"]))
    user_response = output_stream_response(response_stream)

    if not user_response:
        return
    else:
        st.session_state["history"].append(TextMsg({"role": "user", "content": user_response}))
        with st.chat_message(name="user", avatar=st.session_state["meta"]["user_image_path"]):
            st.markdown(st.session_state["meta"]["user_name"] + ":" + user_response)


def role2_chat():
    if not verify_meta():
        return
    if not ZHIPU_API_KEY:
        st.error("未设置API_KEY")

    text_messages = st.session_state["history"]
    # 反转message role
    response_stream = get_characterglm_response(text_messages, meta=st.session_state["meta"])
    bot_response = output_stream_response(response_stream)

    if not bot_response:
        return
    else:
        st.session_state["history"].append(TextMsg({"role": "assistant", "content": bot_response}))

        with st.chat_message(name="assistant", avatar=st.session_state["meta"]["bot_image_path"]):
            st.markdown(st.session_state["meta"]["bot_name"] + ":" + bot_response)


def init_user_first_question():
    meta = st.session_state["meta"]
    instruction = f"""
    阅读下面的角色人设。
    角色一:
    {meta['user_name']}的人设：
    {meta['user_info']}
    角色二:
    {meta["bot_name"]}的人设：
    {meta["bot_info"]}

    """.rstrip()

    instruction += """

    要求如下：
    1. 在符合角色一的人设的条件下,假如角色一和角色二即将开展对话,对话将有角色一开始,请生成角色一对于对话的第一句话，不要生成任何多余的内容
    2. 彼此之间的称呼应该满足相互尊重
    3. 描写不能包含敏感词，人物形象需得体,不要超过50字
    """.rstrip()
    LOG.debug(f'init_user_first_question instruction = {instruction}')

    question_content = get_chatglm_response_via_sdk(
        messages=[
            {
                "role": "user",
                "content": instruction.strip()
            }
        ]
    )
    st.session_state["history"].append(TextMsg({"role": "user", "content": question_content}))

    with st.chat_message(name="user", avatar=st.session_state["meta"]["user_image_path"]):
        st.markdown(meta["user_name"] + ":" + question_content)


def draw_role_image(role_profile: str):
    img_url = "resources" + os.path.sep + "image" + os.path.sep + role_profile + ".png"
    if not generate_picture_switch:
        return img_url
    # 若没有对话历史，则根据角色人设生成图片
    current_role_profile = img_url
    current_role_name = '角色'
    if role_profile == 'role1_info':
        current_role_profile = st.session_state["meta"]['user_info']
        current_role_name = st.session_state["meta"]['user_name']
    elif role_profile == 'role2_info':
        current_role_profile = st.session_state["meta"]['bot_info']
        current_role_name = st.session_state["meta"]['bot_name']

    image_prompt = "".join(generate_role_appearance(current_role_profile))
    if not image_prompt:
        st.error("调用chatglm生成Cogview prompt出错")
        # 如果调用出错,使用默认的头像
        return img_url

    image_prompt = '二次元风格。' + image_prompt.strip()

    LOG.debug(f"image_prompt = {image_prompt}")

    n_retry = 3
    st.markdown(f"正在生成{current_role_name}的头像照片...")
    for i in range(n_retry):
        try:
            img_url = generate_cogview_image(image_prompt)
        except Exception as e:
            if i < n_retry - 1:
                st.error("遇到了一点小问题，重试中...")
            else:
                st.error("又失败啦，点击【生成图片】按钮可再次重试")
        else:
            break

    return img_url


def lets_chat(chat_round: int):
    # 生成角色1的肖像
    role1_info_image = draw_role_image("role1_info")
    # 保存角色1的肖像
    st.session_state["meta"].update(user_image_path=role1_info_image)
    # 生成角色2的肖像
    role2_info_image = draw_role_image("role2_info")
    # 保存角色2的肖像
    st.session_state["meta"].update(bot_image_path=role2_info_image)
    # 以角色1的身份生成一个开场白
    init_user_first_question()
    # 基于上面生成的开场白,角色2开始会话
    for _ in range(chat_round):
        # 角色2生成回话
        role2_chat()
        # 角色1生成回话
        role1_chat()

    # 保存本次会话到文件
    save_current_session_dialogue()


def save_current_session_dialogue():
    # 获取当前时间
    current_time = datetime.datetime.now()
    # 格式化当前时间为年月日时分秒的字符串形式
    time_str = current_time.strftime("%Y%m%d%H%M%S")
    text_messages_json = json.dumps(st.session_state["history"], ensure_ascii=False, indent=4)
    meta_json = json.dumps(st.session_state["meta"], ensure_ascii=False, indent=4)
    with open("resources" + os.path.sep + "perseverance_data" + os.path.sep + time_str + "_dialogue_perseverance.txt",
              "w", encoding="utf-8") as file:
        file.write('# 人物人设:' + "\n")
        file.write(meta_json + "\n")
        file.write('# 对话记录:' + "\n")
        file.write(text_messages_json)


# 设置API KEY
st.sidebar.text_input("ZHIPU_API_KEY", value=os.getenv("ZHIPU_API_KEY"), key="zhipu_api_key",
                      type="password",
                      on_change=update_api_key)

# 初始化
if "history" not in st.session_state:
    st.session_state["history"] = []
if "meta" not in st.session_state:
    st.session_state["meta"] = {
        "bot_name": "",
        "bot_info": "",
        "bot_image_path": "",
        "user_name": "",
        "user_info": "",
        "user_image_path": ""
    }

# 4个输入框，设置meta的4个字段
meta_labels = {
    "bot_name": "角色名",
    "user_name": "用户名",
    "bot_info": "角色人设",
    "user_info": "用户人设"
}

# 2x2 layout
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        st.text_input(label="角色1名", value="姜维", key="user_name", max_chars=20,
                      on_change=lambda: st.session_state["meta"].update(bot_name=st.session_state["user_name"]),
                      help="角色1的名字，不可以为空")

        st.text_area(label="角色1人设",
                     value="姜维是一个智勇双全、忠诚孝顺、胆大心细、勇往直前的英雄人物。他在诸葛亮的培养下成为了全面性的人才，具备了统帅能力和战略智慧。"
                           "他对诸葛亮和国家怀有深厚的感恩之情。他谦虚谨慎，虚心向诸葛亮学习，并在战场上勇敢果断地运用计策取得胜利。"
                           "他勇往直前，矢志不渝地为了国家和理想而奋斗，即使面临失败和绝境也不退缩。姜维的精神力量和坚定信念使他成为了一个不朽的英雄。"
                           "重要人设: 蜀汉后期最高的军事指挥者，官职为大将军。兴复汉室的理想的继任者，但是从来没有见过理想的提出人刘备。该理想传承于诸葛亮。",
                     key="user_info",
                     max_chars=255,
                     on_change=lambda: st.session_state["meta"].update(bot_info=st.session_state["user_info"]),
                     help="角色1的详细人设信息，不可以为空")
    with col2:
        st.text_input(label="角色2名", value="刘备", key="bot_name", max_chars=20,
                      on_change=lambda: st.session_state["meta"].update(user_name=st.session_state["bot_name"]),
                      help="角色2的名字，不可以为空")

        st.text_area(label="角色2人设",
                     value="刘备是一个有着高尚品德和宽厚胸怀的人。他待人宽容，重视人才，善于倾听和接纳不同的意见。他勇敢坚毅，不屈不挠，面对困难和挑战从不退缩。"
                           "他善于组织和管理，能够团结人心，赢得人们的尊敬和支持。他有着广阔的胸怀和远大的抱负，努力争取自己的利益，但也懂得避免冲突和害人之处。"
                           "刘备弘毅宽厚，知人待士，百折不挠，其临死前举国托付给诸葛亮的行为被陈寿称赞为“古今之盛轨”"
                           "总的来说，刘备是一个仁德兼备、有智有勇、受人尊敬的人物。"
                           "重要人设: 蜀汉的开国皇帝，谥号昭烈皇帝，临终前将自己兴复汉室的理想托付给诸葛亮。从来没有见过姜维。",
                     key="bot_info",
                     max_chars=255,
                     on_change=lambda: st.session_state["meta"].update(user_info=st.session_state["bot_info"]),
                     help="角色2的详细人设信息，不可以为空")

        st.session_state["meta"].update(user_name=st.session_state["user_name"])
        st.session_state["meta"].update(user_info=st.session_state["user_info"])
        st.session_state["meta"].update(bot_name=st.session_state["bot_name"])
        st.session_state["meta"].update(bot_info=st.session_state["bot_info"])

button_labels = {
    "clear_meta": "清空人设",
    "clear_history": "清空对话历史",
    "chat_start": "开始会话",
    "show_api_key": "查看API_KEY",
    "show_meta": "查看meta",
    "show_history": "查看历史"
}

# 在同一行排列按钮
with st.container():
    n_button = len(button_labels)
    cols = st.columns(n_button)
    button_key_to_col = dict(zip(button_labels.keys(), cols))

    with button_key_to_col["clear_meta"]:
        clear_meta = st.button(button_labels["clear_meta"], key="clear_meta")
        if clear_meta:
            st.session_state["meta"] = {
                "bot_name": "",
                "bot_info": "",
                "bot_image_path": "",
                "user_name": "",
                "user_info": "",
                "user_image_path": ""
            }
            st.rerun()

    with button_key_to_col["clear_history"]:
        clear_history = st.button(button_labels["clear_history"], key="clear_history")
        if clear_history:
            init_session()
            st.rerun()

    number = st.number_input("对话的轮次", min_value=3, max_value=20, placeholder="请输入一个整数", step=1,
                             key="chat_round")

    generate_picture_switch = st.toggle("是否根据人设生成人物头像", value=False, disabled=True,
                                        help='请确保apiKey拥有智谱CogView生成图的权限并且余额充足,否则将会使用默认头像')

    with button_key_to_col["chat_start"]:
        chat_start = st.button(button_labels["chat_start"], key="chat_start")

    with button_key_to_col["show_api_key"]:
        show_api_key = st.button(button_labels["show_api_key"], key="show_api_key")
        if show_api_key:
            LOG.debug(f"ZHIPU_API_KEY = {ZHIPU_API_KEY}")
            print(f"ZHIPU_API_KEY = {ZHIPU_API_KEY}")

    with button_key_to_col["show_meta"]:
        show_meta = st.button(button_labels["show_meta"], key="show_meta")
        if show_meta:
            LOG.debug(f"meta = {json.dumps(st.session_state['meta'], ensure_ascii=False, indent=4)}")

    with button_key_to_col["show_history"]:
        show_history = st.button(button_labels["show_history"], key="show_history")
        if show_history:
            format_messages = json.dumps(st.session_state["history"], ensure_ascii=False, indent=4)
            LOG.debug(f"history = {format_messages}")

if chat_start:
    verify_api_key_not_empty()

    lets_chat(number)
