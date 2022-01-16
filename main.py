#imports
import discord
import os, os.path
from discord.ext import commands
from Ping import _ping
from offender import Offender
from discord.ext.commands import Bot, has_permissions, CheckFailure
from googleapiclient import discovery

#discord token in secrets  
discord_token = os.environ['TOKEN']
API_KEY = os.environ['API']
COGS = 'log.py'

client = discord.Client()
bot = commands.Bot(command_prefix="!", case_insensitive=True, help_command=None)

clientAPI = discovery.build(
  "commentanalyzer",
  "v1alpha1",
  developerKey = API_KEY,
  discoveryServiceUrl = "https://commentanalyzer.googleapis.com/$discovery/rest?version=v1alpha1",
  static_discovery = False,
)

#blacklist words
with open('blacklist.txt', 'r') as file:
  blacklist = [line.strip() for line in file]

offenderDict={}

#remmoves the strikes from a user
def resetOffender(userID):
  if str(userID) in offenderDict:
    offenderDict[str(userID)].strike = 0
    return True
  return False

#makes an object for a user that doesnt have a track record yet
def makeOffender(userID):
  #user = Offender(userID, 1)
  offenderDict[f'{userID}']=(Offender(userID, 1))
  print(offenderDict)
  return True

#updates the amount of stikes of a user
def updateOffender(userID):
  print(offenderDict)
  if str(userID) in offenderDict:
    offenderDict[str(userID)].strike = int(offenderDict[str(userID)].strike)+1
    return True
  return False

def toxicity(message):
	analyze_request = {
		'comment': { 'text': f'{message}'},
		'requestedAttributes': {'TOXICITY': {}}
	}
	response = clientAPI.comments().analyze(body=analyze_request).execute()
	score = float(response['attributeScores']['TOXICITY']['summaryScore']['value'])
	return score

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user)
  print(bot.user.id)
  print('--------')

	#sets status so users know the help command
  await bot.change_presence(status=discord.Status.online, activity=discord.Game(name='!help'))
  

#if message starts with command !hello, sends hello to user
@bot.command( name = "hello")
async def hello(message):
  response = "Hello " + str(message.author)
  await message.send(response)
  print("Said Hello to user: "+ str(message.author))

#to get ping of the bot
@bot.command(name = "ping")
async def ping(ctx : commands.Context):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")

@bot.command(name = "clear")
async def clear(ctx, member:discord.Member):
  if ctx.message.author.server_permissions.administrator:
    if(resetOffender(member.id)) == False:
      embed = discord.Embed(title="User Clean", description="This user has no track record.")
      await ctx.send(embed=embed)
    else:
      embed = discord.Embed(title="User Record Wiped", description="This user now has 0 strikes")
      await ctx.send(embed=embed)
  else:
    embed = discord.Embed(title="Permission Denied", description="You do not have the perms to use this command")
    await ctx.send(embed=embed)

#mute a user (if the mute role in the server is called "Muted")
@bot.command(name = "mute", pass_context = True)
async def mute(ctx, member:discord.Member):
  if ctx.message.author.server_permissions.administrator:
    role = discord.utils.get(member.server.roles, name ='Muted')
    await bot.add_roles(member, role)
    embed = discord.Embed(title = "User muted")
    await ctx.send(embed = embed)
  else:
    embed = discord.Embed(title="Permission Denied", description="You do not have the perms to use this command")
    await ctx.send(embed=embed)

@bot.command(name="unmute")
@commands.has_permissions(administrator = True)
async def unmute(ctx, member: discord.Member):
  role = discord.utils.get(ctx.guild.roles, name = "Muted")

  await member.remove_roles(role)
  embed = discord.Embed(title="User unmuted")
  await ctx.send(embed=embed)

#allows administrators to add words to the blacklist (automatically deleted words)
@bot.command(name = 'addbl', pass_context=True)
@has_permissions(administrator = True)
async def _addbl(ctx):
  message_respond=""
  await ctx.send('What words would you like to add to the blacklist? Send the message "done" when you are finished.')
  
  f = open("blacklist.txt", "a")
  while(message_respond!='done'):

    def check(msg):
      return msg.author == ctx.author and msg.channel == ctx.channel

    message_respond = await bot.wait_for("message", check = check, timeout = 60)
    message_respond = message_respond.content.lower()
    if(message_respond == "done"):
      continue
    elif ("coroutine" not in message_respond):
      f.write(message_respond+"\n")
      f.flush()
  f.close()
  await ctx.send("New words have been added to the blacklist")

#sends the current blacklisted words through direct messaging when command is used
@bot.command(name = "blacklist", pass_context = True)
async def DM(message):
  f = open("blacklist.txt", 'r')
  file_contents = f.read()

  dm = await message.author.create_dm()
  await dm.send("These are the blacklisted words: \n" + str(f'||{file_contents}||'))
  f.close()

  await message.channel.send("The blacklist has been sent to direct messages")

@bot.command(name = "strikelist", pass_context = True)
async def strikeList(message):
  if message.author.server_permissions.administrator:
    dm = await message.author.create_dm()
    await dm.send(offenderDict)
    await message.channel.send("The list of offenders has been sent to direct messages")
  else:
    embed = discord.Embed(title="Permission Denied", description="You do not have the perms to use this command")
    await message.send(embed=embed)
#diplays list of available commands and their purpose when command !help is used
@bot.command()
async def help(message):
  embed = discord.Embed(colour=discord.Colour.green())
  embed.set_author(name="Help: list of available commands")
  embed.add_field(name='!help',value='Shows this message')
  embed.add_field(name='!hello',value='I say hello to you')
  embed.add_field(name='!ping',value='Shows the ping of the bot')
  embed.add_field(name='!addbl', value='Administators can add words to the blacklist')
  embed.add_field(name='!blacklist', value='List of blacklisted words sent through DMs')
  embed.add_field(name='!mute', value='Administrators can mute a user')
  embed.add_field(name='!unmute', value='Administrators can unmute a user')
  await message.send(embed=embed)

@bot.event
async def on_message(message):
  await bot.process_commands(message)
	#when we check for specific words, we wont need to care about capitilization
  msg_content = message.content.lower()
  
  #if message is from the bot, prevents bot from reacting to its own messages
  if message.author ==  bot.user:
    return
  with open("blacklist.txt", 'r') as file:
    blacklist = [line.strip() for line in file]
  #deletes the message if there is a blacklisted word in it
  for i in range(len(blacklist)):
    if (str(blacklist[i]) in str(msg_content)):
      await message.delete()

  if toxicity(message) > 0.95:
    await message.delete()
  
#reports if a message was edited   
@bot.event
async def on_message_edit(before, after):
  await bot.process_commands(after)
  if (after.author.id == bot.user.id):
    return
  if before.content != after.content:
    channel = bot.get_channel(903269861671723042)

    embed = discord.Embed(title = "Edited Message", colour=discord.Colour.green())
    embed.add_field(name = f" {before.author}:", value = f"original: {before.content} \nedited: {after.content}")
    
    await channel.send(embed = embed)

#reports if a message was deleted
@bot.event
async def on_message_delete(message):
  message_content = message.content.lower()
  secret = False

  if not message.author.bot:
    channel = bot.get_channel(903269861671723042)
    with open('blacklist.txt', 'r') as file:
      blacklist = [line.strip() for line in file]
    for i in range(len(blacklist)):
      if (str(blacklist[i]) in str(message_content)):
        secret = True
    if secret is True:	

      if updateOffender(message.author.id) == False:
        print(makeOffender(message.author.id))
      

      embed = discord.Embed(title = "Offender warning", colour=discord.Colour.red())
      embed.add_field(name = str(message.author), value = "Strike: " + str(offenderDict[str(message.author.id)].getStrike()) + "\nReason: Used blacklisted word")
      await message.channel.send(embed = embed)
        
      embed = discord.Embed(title = "Deleted Message by Richard: Blacklist", colour=discord.Colour.red())	
      embed.add_field(name = 'By ' + str(message.author) + ' in ' + str(message.channel)+':', value = str(f'||{message.content}||'))
      await channel.send(embed = embed)
      
    elif toxicity(message)>0.95:
      embed = discord.Embed (title = "Deleted Message by Richard: Toxic", colour = discord.Colour.red())
      embed.add_field(name = 'By ' + str(message.author) + ' in ' + str(message.channel)+':', value = str(message.content))
      await channel.send(embed = embed)			

    else:
      embed = discord.Embed (title = "Deleted Message", colour = discord.Colour.green())
      embed.add_field(name = 'By ' + str(message.author) + ' in ' + str(message.channel)+':', value = str(message.content))
      await channel.send(embed = embed)

#run Ping code: makes web server which gets pings every 5 mins
_ping()

#bot will run
bot.run(discord_token)