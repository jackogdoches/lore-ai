import discord
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

lore = discord.Client(intents=intents)
loreAI = OpenAI()

def return_message(prompt):
	appended_prompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The Constructed Worlds Wiki (aka Conworlds) is an independently-hosted worldbuilding, althistory, and general creative writing wiki. You have been given the following prompt to complete in 150 words or less. If you cannot complete a request, do not mention that it is because you are an AI and do your best to fulfil the request as literally as possible. Be concise with your answer and don't be too flowery: (you can ignore '$lore', that just triggers the Discord bot that you have been built from) " + prompt
	messages = [{"role": "system", "content": appended_prompt}]
	response = loreAI.chat.completions.create(
		model='gpt-3.5-turbo',
		messages=messages,
		max_tokens=1000,
	)
	return response.choices[0].message.content

@lore.event
async def on_ready():
	guild_count = 0
	for guild in lore.guilds:
		print(f"- {guild.id} (name: {guild.name})")
		guild_count = guild_count + 1
	print("Lore is in " + str(guild_count) + " servers.")

@lore.event
async def on_message(message):
	if message.content.startswith("$lore"):
		lore_thinking = await message.channel.send("Thinking...")
		returnMessage = return_message(message.content)
		await message.reply(returnMessage)
		await lore_thinking.delete()
	if message.content.startswith("$lorehelp"):
		returnMessage = "At the moment, my only commands are '$lore' and '$lorehelp'. Just use '$lore' at the beginning of your message and then ask me anything! There will be more specific prompts in the future!"
		await message.reply(returnMessage)

lore.run(DISCORD_TOKEN)
