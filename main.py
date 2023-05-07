from typing import Callable
from datetime import datetime, timedelta

import discord
from discord import app_commands, User, Message
import openai

from moderation import bad_prompt
from tools import read_cfg, save_cfg, base_history, count_tokens
from gpt import generate_response

cfg = read_cfg()
openai.api_key = cfg["openai_key"]
discord_token = cfg["discord_token"]

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

is_admin: Callable[[Message], bool] = lambda msg: msg.author.id in cfg["admins"]

last_sent = datetime.now() - timedelta(seconds=60)
history = base_history()
print(f"base tokens: {count_tokens(history)}")
cooldown = 2
daily_messages = 15
total_tokens = 0
message_count = {}


def pre_msg_check(msg: Message):
    global message_count
    if msg.author.id not in message_count:
        message_count[msg.author.id] = 0
    if is_admin(msg):
        return True
    if (datetime.now() - last_sent).seconds < cooldown:
        print("on cooldown")
        return False
    if msg.author.id in cfg["blacklist"]:
        print(f"{msg.author.name} is blacklisted")
        return False
    if bad_prompt(msg):
        return False
    if message_count[msg.author.id] > daily_messages:
        msg.reply("You have reached your daily limit!")
        return False
    return True


async def gpt_respond(msg: Message):
    global history, total_tokens, last_sent, message_count
    last_sent = datetime.now()
    rsp = generate_response(msg, history)
    if rsp[0] is None:
        return
    response = rsp[0]
    print(response)
    for i in range(0, len(response), 2000):
        await msg.reply(response[i : i + 2000])
    history = rsp[1]
    total_tokens += count_tokens(history)
    print(f"current tokens: {total_tokens}")
    message_count[msg.author.id] += 1

# COMING SOON I JUST WANNA GO TO BED GOODNIGHT
# @tree.command()
# async def cost(msg: Message):
#     amount = round(total_tokens / 1000 * 0.002, 4)
#     msg.reply(f"Revel has lost ${amount} so far LULW")


# @tree.command()
# async def wipe(msg: Message):
#     global history
#     history = base_history()
#     msg.reply(f"PepOk wiped history, tokens now at {count_tokens(history)}")


# @tree.command()
# async def tokens(msg: Message):
#     msg.reply(f"PepoTurkey current tokens: {count_tokens(history)}")


# @tree.command()
# async def bla(msg: Message, name: str, *_):
#     if name not in cfg["blacklist"]:
#         cfg["blacklist"].append(name)
#     save_cfg(cfg)
#     msg.reply(f"PepOk {name} blacklisted")


# @tree.command()
# async def blr(msg: Message, key: str, *_):
#     if key in cfg["blacklist"]:
#         cfg["blacklist"].remove(key)
#     save_cfg(cfg)
#     msg.reply(f"PepOk {key} unblacklisted")


# @tree.command()
# async def cd(msg: Message, seconds: str, *_):
#     global cooldown
#     try:
#         cooldown = int(seconds)
#     except ValueError:
#         msg.reply(f"that's not an integer MMMM")
#         return
#     msg.reply(f"PepOk changed the cooldown to {cooldown}s")


@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    await tree.sync()


@client.event
async def on_message(msg: Message):
    global message_count
    if msg.author == client.user: 
        return
    if last_sent.day != datetime.now().day:
        message_count.clear()
    if client.user.mentioned_in(msg):
        if not pre_msg_check(msg):
            return
        await gpt_respond(msg)


if __name__ == "__main__":
    client.run(discord_token)
