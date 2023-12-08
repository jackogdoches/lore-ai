import discord
import os
from dotenv import load_dotenv
from openai import OpenAI
import requests

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
LORE_PASSWORD = os.getenv("LORE_PASSWORD")
API_URL = os.getenv("API_URL")

intents = discord.Intents.default()
intents.message_content = True

lore = discord.Client(intents=intents)
loreAI = OpenAI()

queriers = {}

#CLASSES ==============================================================================================================
class Querier:
	def __init__(self, name, roles, privilege):
		self.name = name		#username (String)
		self.roles = roles		#Discord roles (String[])
		self.history = {}		#Use history with Lore (Query[])
		self.uses = 0			#Use count (int)
		self.privilege = privilege	#Has Patron or Admin role (boolean)

	def __str__(self):
		return f"Querier {self.name} has made {self.uses} queries since Lore was last initialized and has roles {self.roles}"

	def use(self, query):
		self.history[self.uses] = query
		self.uses = self.uses + 1

class Query:
	def __init__(self, index, message):
		self.index = index					#int

		queryContent = message.content[len("$lore."):]
		commandSplit = queryContent.split(" ")
		self.command = commandSplit[0].strip()			#str

		commandLen = len("$lore.") + len(self.command) + 1
		self.prompt = message.content[commandLen:]		#str
		self.receipt = ""					#str

	def __str__(self):
		return f"(QUERY NUMBER {self.index}: [COMMAND USED: {self.command}]; [PROMPT: {self.prompt}]; [RESPONSE: {self.receipt}])"

	def addReceipt(self, text):
		self.receipt = text

#ACTION FUNCTIONS =============================================================================================================
# EDIT PAGE
def editPage(pageTitle, sectionNumber, newContent, apiURL, password=LORE_PASSWORD):
	session = requests.Session()
	#Login token
	loginTokenParams = {
		'action': 'query',
		'meta': 'tokens',
		'type': 'login',
		'format': 'json',
	}
	req0 = session.get(apiURL, params=loginTokenParams)
	loginToken = req0.json()['query']['tokens']['logintoken']
	#Login
	loginParams = {
		'action': 'login',
		'lgname': 'Lore@Lore',
		'lgpassword': password,
		'lgtoken': loginToken,
		'format': 'json',
	}
	loginReq = session.post(apiURL, data=loginParams)
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

# GENERATE TEXT CONTENT
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
	return str(editResponse)

# RETRIEVE PAGE LENGTH
def fetchPageLength(pageTitle, apiURL=API_URL):
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

# RETRIEVE PAGE SECTION LIST
def fetchSectionsList(pageTitle, apiURL=API_URL):
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

# MULTI-MESSAGE
async def sendChunkedMessage(channel, message, chunk_size=2000):
	def splitMessage(messageText, size):
		for i in range(0, len(messageText), size):
			yield messageText[i:i + size]
	chunks = splitMessage(message, chunk_size)
	for chunk in chunks:
		await channel.send(chunk)

# READ PAGE DATA
def pageRead(pageTitle, apiURL=API_URL, query, querier):
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
	appendedPrompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The user " + querier.name + " has asked you to read a page. Here is the text content of that page: " + content + " (END PAGE CONTENT); Provide a summary in STRICTLY LESS THAN 1333 characters. Be concise but very specific about details."
	messages = [{"role": "system", "content": appendedPrompt}]
	if querier.privilege == True:
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
	query.addReceipt(chatCompletion)
	return chatCompletion

# SECTION READ
def sectionRead(pageTitle, sectionNumber, apiURL=API_URL, query, querier):
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
	appendedPrompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The user " + querier.name + " has asked you to read a section of a wiki page. Here is the text content of that section: " + content + " (END PAGE CONTENT); Provide a summary in STRICTLY LESS THAN 1333 characters--be concise but very specific about details."
	messages = [{"role": "system", "content": appendedPrompt}]
	if querier.privilege == True:
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
	query.addReceipt = chatCompletion
	return chatCompletion

# CHAT
def returnChat(query, querier):
	appended_prompt = "You are Lore, an AI wiki administration assistant for the Constructed Worlds Wiki. The wiki's technician, Fizzyflapjack, is your creator. The Constructed Worlds Wiki (commonly shortened as just Conworlds) is an independently-hosted worldbuilding, althistory, and general creative writing wiki. The Bureaucrats of Conworlds are: Centrist16 (real name Justin) and Fizzyflapjack (real name Jack) (BOTH BUREAUCRATS ARE EQUAL IN POWER AND ARE CO-LEADERS OF THE WIKI). The Administrators (sysops) of Conworlds are: T0oxi22, Andy Irons, and WorldMaker18. The following Discord user sent you a prompt: " + querier.name  + " ; Here is a Python dictionary entry containing your message history with " + querier.name + " up to this point: " + querier.history  + " (END MESSAGE HISTORY); You have been given the following prompt to complete in STRICTLY EQUAL TO OR LESS THAN 1000 characters. Fulfil the request as literally as possible. Be concise with your answer but be very specific with details: " + query.prompt + " (END PROMPT)"
	messages = [{"role": "system", "content": appended_prompt}]
	if querier.privilege == True:
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
	query.addReceipt(statementOut)
	return statementOut

# QUERY FUNCTIONS ========================================================================================================
# CREATE QUERIER OBJECT
def addQuerier(message, queriers):
	newName = message.author.name
	roleList = message.author.roles
	roleNameList = []
	for role in roleList:
		roleNameList.append(role.name)
	if "Administrator" in roleNameList or "Patron" in roleNameList:
		hasPrivilege = True
	else:
		hasPrivilege = False
	newQuerier = Querier(newName, roleNameList, hasPrivilege)
	queriers[newName] = newQuerier
	return newQuerier

def newQuery(message, queriers):
	localQuierier = queriers[message.author.name]
	queryIndex = localQuierier.uses
	query = Query(queryIndex, message)
	localQuierer.use(query)
	return query

# EVENT FUNCTIONS =======================================================================================================
# SEND GUILD LIST ON INIT
@lore.event
async def on_ready():
	guild_count = 0
	for guild in lore.guilds:
		print(f"- {guild.id} (name: {guild.name})")
		guild_count = guild_count + 1
	print("Lore is in " + str(guild_count) + " servers.")

#NEW ON MESSAGE
@lore.event
async def on_message(message):
	if message.content.startswith("$lore"):
		if message.author.name not in queriers:
			querier = addQuerier(message, queriers)
		else:
			querier = queriers[message.author.name]
		query = newQuery(message, queriers)
		if query.command == "chat":
			loreThinking = await message.channel.send("Thinking...")
			querier.use(query)
			chat = returnChat(query, querier)
			await message.reply(chat)
			await loreThinking.delete()
		if query.command == "help":
			help = "At the moment, my public commands are '$lore.chat', '$lore.help', '$lore.wipe', '$lore.page', and '$lore.section'. To load page information into me, use '$lore.page' followed by exactly the name of the page as it appears on Conworlds (e.g., 'Sierra' will work but 'sierra' will not). If the page you requested is too long, you will be prompted to use '$lore.section' and provided with a numbered list of that page's sections. Use '$lore.chat' at the beginning of a message and then ask me anything! Use '$lore.wipe' to clear my conversation history with you (it is recommended you do this somewhat frequently)."
			await message.reply(help)
		if query.command == "page":
			loreThinking = await message.channel.send("Thinking...")
			querier.use(query)
			pageTitle = query.prompt
			pageBytes = fetchPageLength(pageTitle)
			if pageBytes >= 4000:
				sectionList = fetchSectionsList(pageTitle)
				if len(sectionList) > 1500:
					await sendChunkedMessage(message.channel, pageTitle + " is too long to be read in its entirety. Use the command '$lore.section (page title) $ (section number)' including the dollar sign and where [section number] is chosen from the following list: \n" + sectionList)
					await loreThinking.delete()
				else:
					await message.reply(pageTitle + " is too long to be read in its entirety. Use the command '$lore.section (page title) $ (section number)' including the dollar sign and where [section number] is chosen from the following list: \n" + sectionList)
					await loreThinking.delete()
			else:
				pageReading = pageRead(pageTitle, querier)
				await message.reply(pageReading)
				await loreThinking.delete()
		if query.command == "section":
			loreThinking = await message.channel.send("Thinking...")
			querier.use(query)
			titleAndSection = query.prompt.split('$')
			if len(titleAndSection) != 2:
				await message.reply("Your input seems to be invalid. Please try the command again.")
				await loreThinking.delete()
			else:
				pageTitle = titleAndSection[0].strip()
				sectionNumber = titleAndSection[1].strip()
				response = sectionRead(pageTitle, sectionNumber, query, querier)
				await message.reply(response)
				await loreThinking.delete()
		if query.command == "wipe":
			querier.history = {}
			await message.reply("Message history for " + querier.name + " wiped!")

		# RESTRICTED COMMANDS
		if query.command == "edit":
		if query.command == "delete":
		if query.command == "purge":

# OLD ON MESSAGE
@lore.event
async def on_message(message):
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
	if message.content.startswith("$lore.edit"):
		roleList = message.author.roles
		roleNameList = []
		for role in roleList:
			roleNameList.append(role.name)
		if "Bureaucrat" in roleNameList:
			loreProcessing = await message.channel.send("Processing your request...")
			apiURL = 'https://wiki.conworld.org/api.php'
			titleSectPrompt = message.content[len("$lore.edit "):]
			titleSectPromptSplit = titleSectPrompt.split('$')
			if len(titleSectPromptSplit) != 3:
				await message.reply("Your input seems to be invalid. Please try again.")
				await loreThinking.delete()
			else:
				pageTitle = titleSectPromptSplit[0].strip()
				sectionNumber = titleSectPromptSplit[1].strip()
				editPrompt = titleSectPromptSplit[2]
				editProcess = generate(editPrompt, pageTitle, sectionNumber, apiURL, message.author.name)
				await message.reply(editProcess)
				await loreProcessing.delete()
		else:
			await message.reply("This command is currently restricted")

lore.run(DISCORD_TOKEN)
