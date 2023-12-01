import discord
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

intents = discord.Intents.default()
intents.message_content = True

lore = discord.Client(intents=intents)
loreAI = OpenAI()
memory = {}
useCount = {}

def fetch_page(pageTitle, apiURL, author, memoryDict, hasPrivilege):
	params = {
		'action': 'query',
		'format': 'json',
		'titles': pageTitle,
		'prop': 'extracts',
		'exintro': True,
		'explaintext': True,
	}
	response = requests.get(apiURL, params=params)
	data = response.json()
	pages = data.get('query', {}).get('pages', {})
	page = next(iter(pages.values()))
	content = page.get('extract', '')
	appendedPrompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The user " + author + " has asked you to read a page. Here is the text content of that page: " + content + " (END PAGE CONTENT); Provide a summary in less than 1598 characters (strict limit), being concise but as specific about details as possible."
	messages = [{"role": "system", "content": appendedPrompt}]
	if hasPrivilege == True:
		response = loreAI.chat.completions.create(
			model='gpt-4-1106-preview',
			messages=messages,
		)
	else:
		response = loreAI.chat.completions.create(
			model='gpt-3.5-turbo-1106',
			messages=messages,
		)
	chatCompletion = response.choices[0].message.content
	if author in memory:
		retainMemory = memory[author]
		memory[author] = retainMemory + " (END); THE FOLLOWING MESSAGE SENT BY YOU (LORE) IS A SUMMARY OF THE PAGE TITLED " + pageTitle + ": " + chatCompletion
	else:
		memory[author] = "THE FIRST MESSAGE FROM " + author + " WAS A REQUEST TO READ THE WIKI PAGE TITLED " + pageTitle + ", HERE IS THE SUMMARY YOU WROTE: " + chatCompletion
	return chatCompletion

def return_message(prompt, author, memoryDict, hasPrivilege):
	appended_prompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The wiki's technician, Fizzyflapjack, is your creator. The Constructed Worlds Wiki (commonly shortened as just Conworlds) is an independently-hosted worldbuilding, althistory, and general creative writing wiki. As of November 2023, the Bureaucrats of Conworlds are: Centrist16 (real name Justin) and Fizzyflapjack (real name Jack) (BOTH BUREAUCRATS ARE EQUAL IN POWER AND LEAD THE WIKI). The Administrators (sysops) of Conworlds are: T0oxi22, Andy Irons, and WorldMaker18. The following Discord user sent you a prompt: " + author  + " (END USERNAME); Here is a Python dictionary entry containing your message history with this user so far: " + memoryDict[author]  + " (END MESSAGE HISTORY); You have been given the following prompt to complete in STRICTLY 799 characters or less, do your best to fulfil the request as literally as possible. Be concise with your answer but try and be specific with details: " + prompt + " (END PROMPT)"
	messages = [{"role": "system", "content": appended_prompt}]
	if hasPrivilege == True:
		response = loreAI.chat.completions.create(
			model='gpt-4-1106-preview',
			messages=messages,
			max_tokens=2000,
		)
	else:
		response = loreAI.chat.completions.create(
		model='gpt-3.5-turbo-1106',
		messages=messages,
		max_tokens=2000,
	)
	statementOut = response.choices[0].message.content
	retainMemory = memory[author]
	memory[author] = retainMemory + " (END); YOUR RESPONSE: " + statementOut
	return statementOut


@lore.event
async def on_ready():
	guild_count = 0
	for guild in lore.guilds:
		print(f"- {guild.id} (name: {guild.name})")
		guild_count = guild_count + 1
	print("Lore is in " + str(guild_count) + " servers.")

@lore.event
async def on_message(message):
	if message.content.startswith("$lore.chat"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList or "Patron" in roleNameList:
			hasPrivilege = True
			if message.author.name in memory:
				retain = memory[message.author.name]
				concatenate = retain + "(END); NEXT MESSAGE FROM USER: " + message.content
			else:
				memory[message.author.name] = "FIRST MESSAGE FROM USER: " + message.content
			lore_thinking = await message.channel.send("Thinking...")
			returnMessage = return_message(message.content, message.author.name, memory, hasPrivilege)
			await message.reply(returnMessage)
			await lore_thinking.delete()
		else:
			hasPrivilege = False
			if message.author.name in useCount:
				if message.author.name in memory and useCount[message.author.name] <= 15:
					retain = memory[message.author.name]
					concatenate = retain + "(END); NEXT MESSAGE FROM USER: " + message.content
					useCount[message.author.name] = useCount[message.author.name] + 1
					lore_thinking = await message.channel.send("Thinking...")
					returnMessage = return_message(message.content, message.author.name, memory, hasPrivilege)
					await message.reply(returnMessage)
					await lore_thinking.delete()
				elif useCount[message.author.name] > 15:
					await message.reply("I am sorry, but you have reached your maximum usage for today. Please wait until midnight UTC for your use count to reset.")
				elif message.author.name not in memory and useCount[message.author.name] <= 15:
					memory[message.author.name] = "FIRST MESSAGE FROM USER: " + message.content
					lore_thinking = await message.channel.send("Thinking...")
					returnMessage = return_message(message.content, message.author.name, memory, hasPrivilege)
					await message.reply(returnMessage)
					await lore_thinking.delete()
			elif message.author.name not in useCount:
					useCount[message.author.name] = 1
					if message.author.name in memory:
						retain = memory[message.author.name]
						concatenate = retain + "(END); NEXT MESSAGE FROM USER: " + message.content
						lore_thinking = await message.channel.send("Thinking...")
						returnMessage = return_message(message.content, message.author.name, memory, hasPrivilege)
						await message.reply(returnMessage)
						await lore_thinking.delete()
					else:
						memory[message.author.name] = "FIRST MESSAGE FROM USER: " + message.content
						lore_thinking = await message.channel.send("Thinking...")
						returnMessage = return_message(message.content, message.author.name, memory, hasPrivilege)
						await message.reply(returnMessage)
						await lore_thinking.delete()
	if message.content.startswith("$lore.help"):
		returnMessage = "At the moment, my only commands are '$lore.chat', '$lore.help', '$lore.wipe', and '$lore.read'. To load page information into me, use '$lore.read' followed by exactly the name of the page as it appears on Conworlds (e.g., 'Sierra' will work but 'sierra' will not; NOTE: I am incapable of reading File: and Template: pages). Use '$lore.chat' at the beginning of a message and then ask me anything! Use '$lore.wipe' to clear my conversation history with you (it is recommended you do this somewhat frequently)."
		await message.reply(returnMessage)
	if message.content.startswith("$lore.wipe"):
		if message.author.name in memory:
			memory[message.author.name] = ""
			await message.reply("I have wiped my conversation history with " + message.author.name)
		else:
			await message.reply("There is nothing for me to wipe!")
	if message.content.startswith("$lore.purge"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList:
			if len(memory) != 0:
				memory.clear()
				await message.channel.send("All memories purged!")
			if len(useCount) != 0:
				useCount.clear()
				await message.channel.send("User counter purged!")
		else:
			await message.reply("I'm sorry, but only Administrators can use this command")
	if message.content.startswith("$lore.read"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList or "Patron" in roleNameList:
			hasPrivilege = True
			lore_thinking = await message.channel.send("Thinking...")
			pageTitle = message.content[len("$lore.read "):].strip()
			apiURL = 'https://wiki.conworld.org/api.php'
			pageRead = fetch_page(pageTitle, apiURL, message.author.name, memory, hasPrivilege)
			await message.reply(pageRead)
			await lore_thinking.delete()
		else:
			hasPrivilege = False
			lore_thinking = await message.channel.send("Thinking...")
			pageTitle = message.content[len("$lore.read "):].strip()
			apiURL = 'https://wiki.conworld.org/api.php'
			pageRead = fetch_page(pageTitle, apiURL, message.author.name, memory, hasPrivilege)
			await message.reply(pageRead)
			await lore_thinking.delete()

lore.run(DISCORD_TOKEN)
