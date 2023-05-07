import openai
from discord import Message

from tools import count_tokens

user_msg: dict = lambda data: {"role": "user", "content": data}
gpt_msg: dict = lambda data: {"role": "assistant", "content": data}


def generate_response(msg: Message, history: list) -> tuple[str, list]:
    history.append(user_msg(f"{msg.author.name}: {msg.content}"))
    while count_tokens(history) >= 1250:
        del history[15:17]
        print(f"trimmed prompt to {count_tokens(history)} tokens")
    print("Sending request to openai")
    rsp = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=history)
    rsp = rsp["choices"][0]["message"]["content"]
    if not isinstance(rsp, str):
        print(f"{msg.author.name}'s prompt made an invalid response:\n{rsp}")
        return None, None
    history.append(gpt_msg(rsp))
    return rsp, history
