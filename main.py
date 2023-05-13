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


@tree.command(name="cost", description="How much has the bot cost so far?")
async def cost(ctx: discord.Interaction):
    amount = round(total_tokens / 1000 * 0.002, 4)
    await ctx.response.send_message(f"This bot has cost ${amount} to run so far this session lol")


@tree.command(name="wipe", description="Wipe the bot's history")
async def wipe(ctx: discord.Interaction):
    global history
    if not is_admin(ctx.user.id):
        await ctx.response.send_message("You don't have permission to use this!", ephemeral=True)
        return
    history = base_history()
    await ctx.response.send_message(f"Wiped history, tokens now at {count_tokens(history)}")


@tree.command(name="tokens", description="How many tokens has the bot used so far?")
async def tokens(ctx: discord.Interaction):
    await ctx.response.send_message(f"Current tokens: {count_tokens(history)}")


@tree.command(name="blacklist", description="Blacklist a user from using the bot")
async def bla(ctx: discord.Interaction, user: User):
    if not is_admin(ctx.user.id):
        await ctx.response.send_message("You don't have permission to use this!", ephemeral=True)
        return
    if user.id not in cfg["blacklist"]:
        cfg["blacklist"].append(user.id)
    save_cfg(cfg)
    ctx.response.send_message(f"{user.name} has been blacklisted")


@tree.command(name="unblacklist", description="Unblacklist a user from using the bot")
async def blr(ctx: discord.Interaction, user: User):
    if not is_admin(ctx.user.id):
        await ctx.response.send_message("You don't have permission to use this!", ephemeral=True)
        return
    if user.id in cfg["blacklist"]:
        cfg["blacklist"].remove(user.id)
    else:
        await ctx.response.send_message(f"{user.name} is not blacklisted")
        return
    save_cfg(cfg)
    ctx.response.send_message(f"{user.name} has been unblacklisted")


@tree.command(name="cooldown", description="Change the bot's cooldown")
async def cd(ctx: discord.Interaction, seconds: str):
    global cooldown
    try:
        cooldown = int(seconds)
    except ValueError:
        ctx.response.send_message(f"That's not an integer!", ephemeral=True)
        return
    ctx.response.send_message(f"Changed the cooldown to {cooldown}s")


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
        async with msg.channel.typing():
            await gpt_respond(msg)


if __name__ == "__main__":
    client.run(discord_token)
