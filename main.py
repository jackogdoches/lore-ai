import discord
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LORE_PASSWORD = os.getenv("LORE_PASSWORD")

intents = discord.Intents.default()
intents.message_content = True

lore = discord.Client(intents=intents)
loreAI = OpenAI()
memory = {}
useCount = {}

def editPage(pageTitle, sectionNumber, newContent, apiURL, password=LORE_PASSWORD):
	#Login
	session = requests.Session()
	loginParams = {
		'action': 'login',
		'lgname': Lore,
		'lgpassword': password,
		'format': 'json',
	}
	req1 = session.post(apiURL, data=loginParams)
	loginToken = re1.json()['login']['token']
	loginParams['lgtoken'] = loginToken
	session.post(apiURL, loginParams)
	#Get edit token
	tokenParams = {
		'action': 'query',
		'meta': 'tokens',
		'format': 'json',
	}
	req2 = session.get(apiURL, params=tokenParams)
	editToken = req2.json()['query']['tokens']['csrftoken']
	#Perform edit
	editParams = {
		'action': 'edit',
		'title': pageTitle,
		'section': sectionNumber,
		'text': newContent,
		'token': editToken,
		'format': 'json',
	}
	req3 = session.post(apiURL, data=editParams)
	return req3.json()

def generate(prompt, pageTitle, sectionNumber, apiURL, author):
	params = {
		'action': 'parse',
		'format': 'json',
		'page': pageTitle,
		'prop': 'text',
		'section': sectionNumber,
		'disabletoc': True,
	}
	response = requests.get(apiURL, params=params)
	data = response.json()
	content = data.get('parse', {}).get('text', {}).get('*', '')
	appendedPrompt = "You are Lore, an AI wiki assistant for the Constructed Worlds Wiki. The user " + author + " has asked you to edit a section of a page. Here is the current text content of that section: " + content + " (END PAGE CONTENT); The user has given you this prompt: " + prompt + " (END PROMPT); Your output should be formatted in wikitext and written in an encylopeadic, neutral-pov style."
	messages = [{"role": "system", "content": appendedPrompt}]
	response = loreAI.chat.completions.create(
		model='gpt-4-1106-preview',
		messages=messages,
	)
	chatCompletion = response.choices[0].message.content
	editResponse = editPage(pageTitle, sectionNumber, chatCompletion, apiURL)
	editResponseContext = "You are Lore, an AI wiki assistant for the Constructed Worlds Wiki. The user " + author + " has asked you to edit a section of a page. You have performed the edit API request and have received this response from the website: " + editResponse + " (END JSON RESPONSE); Please provide a human-understandable interpretation of the json response, being as brief as possible without skipping details."
	editResponseMessage = [{"role": "system", "content": responseContext}]
	editResponseCompletion = loreAI.chat.complestions.create(
		model='gpt-4-1106-preview',
		messages=messages,
	)
	editResponseProcessed = editResponseCompletion.choices[0].message.content
	return editResponseProcessed

def fetchPageLength(pageTitle, apiURL):
	params = {
		'action': 'query',
		'format': 'json',
		'titles': pageTitle,
		'prop': 'info',
	}
	response = requests.get(apiURL, params=params)
	data = response.json()
	pages = data.get('query', {}).get('pages', {})
	page = next(iter(pages.values()))
	lengthKB = page.get('length', 0)
	return lengthKB

def fetchPageSections(pageTitle, apiURL):
	params = {
		'action': 'parse',
		'format': 'json',
		'page': pageTitle,
		'prop': 'sections',
	}
	response = requests.get(apiURL, params=params)
	data = response.json()
	if 'parse' in data and 'sections' in data['parse']:
		sections = data['parse']['sections']
		sectionList = [f"{section['index']}. {section['line']}" for section in sections]
		numberedList = "\n".join(sectionList)
		return numberedList
	else:
		return "No sections found or an error occurred."

async def sendChunkedMessage(channel, message, chunk_size=2000):
	def splitMessage(messageText, size):
		for i in range(0, len(messageText), size):
			yield messageText[i:i + size]
	chunks = splitMessage(message, chunk_size)
	for chunk in chunks:
		await channel.send(chunk)

def pageRead(pageTitle, apiURL, author, memoryDict, hasPrivilege):
	params = {
		'action': 'query',
		'format': 'json',
		'titles': pageTitle,
		'prop': 'extracts',
		'explaintext': True,
	}
	response = requests.get(apiURL, params=params)
	data = response.json()
	pages = data.get('query', {}).get('pages', {})
	page = next(iter(pages.values()))
	content = page.get('extract', '')
	appendedPrompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The user " + author + " has asked you to read a page. Here is the text content of that page: " + content + " (END PAGE CONTENT); Provide a summary in STRICTLY LESS THAN 1333 characters, being concise but specific about details."
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

def sectionRead(pageTitle, sectionNumber, apiURL, author, memoryDict, hasPrivilege):
	params = {
		'action': 'parse',
		'format': 'json',
		'page': pageTitle,
		'prop': 'text',
		'section': sectionNumber,
		'disabletoc': True,
	}
	response = requests.get(apiURL, params=params)
	data = response.json()
	content = data.get('parse', {}).get('text', {}).get('*', '')
	appendedPrompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The user " + author + " has asked you to read a section of a page. Here is the text content of that section: " + content + " (END PAGE CONTENT); Provide a summary in STRICTLY LESS THAN 1333 characters, being concise but specific about details."
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
		memory[author] = retainMemory + " (END); THE FOLLOWING MESSAGE SENT BY YOU (LORE) IS AN EXCERPT FROM THE PAGE TITLED " + pageTitle + ": " + chatCompletion
	else:
		memory[author] = "THE FIRST MESSAGE FROM " + author + " WAS A REQUEST TO READ A SECTION OF THE WIKI PAGE TITLED " + pageTitle + ", HERE IS THE SUMMARY OF THE SECTION YOU WROTE: " + chatCompletion
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
		returnMessage = "At the moment, my commands are '$lore.chat', '$lore.help', '$lore.wipe', '$lore.page', and '$lore.section'. To load page information into me, use '$lore.page' followed by exactly the name of the page as it appears on Conworlds (e.g., 'Sierra' will work but 'sierra' will not). If the page you requested is too long, you will be prompted to use '$lore.section' and provided with a numbered list of that page's sections. Use '$lore.chat' at the beginning of a message and then ask me anything! Use '$lore.wipe' to clear my conversation history with you (it is recommended you do this somewhat frequently)."
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
	if message.content.startswith("$lore.page"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList or "Patron" in roleNameList:
			hasPrivilege = True
		else:
			hasPrivilege = False
		lore_thinking = await message.channel.send("Thinking...")
		pageTitle = message.content[len("$lore.page "):].strip()
		apiURL = 'https://wiki.conworld.org/api.php'
		pageBytes = fetchPageLength(pageTitle, apiURL)
		if pageBytes >= 4000:
			sectionList = fetchPageSections(pageTitle, apiURL)
			if len(sectionList) > 1500:
				await sendChunkedMessage(message.channel, pageTitle + " is too long to be read in its entirety. Use the command '$lore.section (page title) $ (section number)' including the dollar sign and where [section number] is chosen from the following list: \n" + sectionList)
				await lore_thinking.delete()
			else:
				await message.reply(pageTitle + " is too long to be read in its entirety. Use the command '$lore.section (page title) $ (section number)' including the dollar sign and where [section number] is chosen from the following list: \n" + sectionList)
				await lore_thinking.delete()
		else:
			pageReading = pageRead(pageTitle, apiURL, message.author.name, memory, hasPrivilege)
			await message.reply(pageReading)
			await lore_thinking.delete()
	if message.content.startswith("$lore.section"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList or "Patron" in roleNameList:
			hasPrivilege = True
		else:
			hasPrivilege = False
		loreThinking = await message.channel.send("Thinking...")
		apiURL = 'https://wiki.conworld.org/api.php'
		titleAndSection = message.content[len("lore.section "):]
		titleAndSectionSplit = titleAndSection.split('$')
		if len(titleAndSectionSplit) != 2:
			await message.reply("Your input seems to be invalid. Please try the command again.")
			await loreThinking.delete()
		else:
			pageTitle = titleAndSectionSplit[0].strip()
			sectionNumber = titleAndSectionSplit[1].strip()
			sectionReading = sectionRead(pageTitle, sectionNumber, apiURL, message.author.name, memory, hasPrivilege)
			await message.reply(sectionReading)
			await loreThinking.delete()
	if message.content.startswith("$lore.edit"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Administrator" in roleNameList or "Patron" in roleNameList:
			loreProcessing = await message.channel.send("Processing your request...")
			apiURL = 'https://wiki.conworld.org/api.php'
			titleSectPrompt = message.content[len("$lore.edit "):]
			titleSectPromptSplit = titleAndPrompt.split('$')
			if len(titleAndSectionSplit) != 3:
				await message.reply("Your input seems to be invalid. Please try again.")
				await loreThinking.delete()
			else:
				pageTitle = titleSectPromptSplit[0].strip()
				sectionNumber = titleSectPromptSplit[1].strip()
				editPrompt = titleSectPromptSplit[2]
				editProcess = generate(editPrompt, pageTitle, sectionNumber, apiURL, message.author.name)
				await message.reply(editProcess)
				await loreThinking.delete()
		else:
			await message.reply("This command is currently restricted")

lore.run(DISCORD_TOKEN)
