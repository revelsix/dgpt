from discord import Message
import openai


def bad_prompt(msg: Message):
    mod = openai.Moderation.create(input=msg.clean_content)
    if mod["results"][0]["flagged"]:
        print(f"This prompt was flagged by openai: \n {msg.author.name}: {msg.content}")
        return True
    return False
