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
memory = {}

def return_message(prompt, author, memoryDict):
	appended_prompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The wiki's technician (i.e., webmaster), Fizzyflapjack, is your creator. The Constructed Worlds Wiki (commonly shortened as just Conworlds) is an independently-hosted worldbuilding, althistory, and general creative writing wiki. As of November 2023, the Administrators of Conworlds are: Centrist16 (real name Justin), Fizzyflapjack (real name Jack), T0oxi22 (real name Toxi), Andy Irons (real name Andy), and WorldMaker18 (real name Liam). The following Discord user sent you a prompt:" + author  + "(END USERNAME); Here is a Python dictionary entry containing the messages that the user messaging you has sent you so far: " + memoryDict[author]  + "(END MESSAGE HISTORY); You have been given the following prompt to complete in 150 words or less. If you cannot complete a request: (do not mention that it is because you are an AI AND do your best to fulfil the request as literally as possible) OR (tell the user that you cannot complete the request and tell them to reach out to one of the aforementioned Administrators). Be concise with your answer and don't be too flowery: (you can ignore '$lore', that just triggers the Discord bot that you interact with users through) " + prompt + " (END PROMPT)"
	messages = [{"role": "system", "content": appended_prompt}]
	response = loreAI.chat.completions.create(
		model='gpt-3.5-turbo-1106',
		messages=messages,
		max_tokens=2000,
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
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList or "Patron" in roleNameList:
			if message.author.name in memory:
				retain = memory[message.author.name]
				concatenate = retain + "NEXT MESSAGE: " + message.content
			else:
				memory[message.author.name] = "FIRST MESSAGE: " + message.content
			lore_thinking = await message.channel.send("Thinking...")
			returnMessage = return_message(message.content, message.author.name, memory)
			await message.reply(returnMessage)
			await lore_thinking.delete()
		else:
			await message.reply("I'm sorry, but you do not have the required role to perform this command (Administrator or Patron).")
	if message.content.startswith("$helplore"):
		returnMessage = "At the moment, my only commands are '$lore', '$helplore', and '$wipelore'. Just use '$lore' at the beginning of your message and then ask me anything! Use '$wipelore' to clear my conversation history with you."
		await message.reply(returnMessage)
	if message.content.startswith("$wipelore"):
		if message.author.name in memory:
			memory[message.author.name] = ""
			await message.reply("I have wiped my conversation history with " + message.author.name)
		else:
			await message.reply("There is nothing for me to wipe!")

lore.run(DISCORD_TOKEN)
