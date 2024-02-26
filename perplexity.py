import aiohttp
import asyncio
import os
import discord
from discord.ext import commands
import time

# ugly
def strip_dash(text: str):
    words = text.split()
    for i, word in enumerate(words):
        if word.startswith("-") and i != len(words)-1:
            words = words[:i] + words[i+1:]
            break
    return " ".join(words)

# i really love this function, improved
async def loopMsg(message: discord.Message):
    role = "assistant" if message.author.bot else "user"
    content = message.content if message.author.bot else strip_dash(message.content)
    content = "Hello!" if content == "" else content
    if not message.reference:
        return [{"role": role, "content": content}]
    repliedMessage = await message.channel.fetch_message(message.reference.message_id)
    previousMessages = await loopMsg(repliedMessage)
    return previousMessages + [{"role": role, "content": content}]

models = [
    "llama-2-70b-chat", # ll
    "codellama-70b-instruct", # cll
    "mistral-7b-instruct", # mis
    "mixtral-8x7b-instruct", # mix
    "sonar-small-chat", # ssc
    "sonar-small-online", # sso
    "sonar-medium-chat", # smc
    "sonar-medium-online", #smo
]

def help_perplexity() -> str:
    text  = f"`-ll`: {models[0]}\n"
    text += f"`-cll`: {models[1]}\n"
    text += f"`-mis`: {models[2]}\n"
    text += f"`-mix`: {models[3]}\n"
    text += f"`-ssc`: {models[4]}\n"
    text += f"`-sso`: {models[5]}\n"
    text += f"`-smc`: {models[6]}\n"
    text += f"`-smo`: {models[7]}\n"
    return text

async def make_request(model: str, messages: list):
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": "Be precise and concise."
            }
        ] + messages
    }
    headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Bearer {os.getenv('PERPLEXITY')}"
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload, headers=headers) as response:
            return await response.json()

async def main_perplexity(ctx: commands.Context, model: int):
    async with ctx.typing():  # Use async ctx.typing() to indicate the bot is working on it.
        msg = await ctx.reply("Generating response…")
        old = round(time.time() * 1000)
        response = await make_request(models[model], await loopMsg(ctx.message)) # spicy
        try: 
            text = response["choices"][0]["message"]["content"]
            if not text or text == "": return await msg.edit(content=f"**Error! :(**\nEmpty response.")
            chunks = [text[i:i+2000] for i in range(0, len(text), 2000)]
            replyFirst = True
            for chunk in chunks:
                if replyFirst: 
                    replyFirst = False
                    await ctx.reply(chunk)
                else: await ctx.send(chunk)
        except Exception as e: return await msg.edit(content=f"**Error! :(**\n{e}")
        await msg.edit(content=f"**Took {round(time.time() * 1000)-old}ms**")