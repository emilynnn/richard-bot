import discord
import os
from discord.ext import commands
from Ping import _ping
#from discord_slash import SlashCommand

#discord token in secrets  
discord_token = os.environ['TOKEN']
COGS = 'log.py'

client = discord.Client()
bot = commands.Bot(command_prefix="!", case_insensitive=True, help_command=None)

#slash = SlashCommand(client, sync_commands=True)

with open('blacklist.txt', 'r') as file:
  blacklist = [line.strip() for line in file]

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user)
  print(bot.user.id)
  print('--------')

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

@bot.command()
async def help(message):
  embed = discord.Embed(colour=discord.Colour.green())
  embed.set_author(name="Help: list of available commands")
  embed.add_field(name='!help',value='Shows this message')
  embed.add_field(name='!hello',value='I say hello to you')
  embed.add_field(name='!ping',value='Shows the ping of the bot')
  await message.send(embed=embed)

@bot.event
async def on_message(message):
  await bot.process_commands(message)
	#when we check for specific words, we wont need to care about capitilization
  msg_content = message.content.lower()
  
  #if message is from the bot, prevents bot from reacting to its own messages
  if message.author ==  bot.user:
    return

  #deletes the message if there is a blacklisted word in it
  for i in range(len(blacklist)):
    if (str(blacklist[i]) in str(msg_content)):
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
    for i in range(len(blacklist)):
      if (str(blacklist[i]) in str(message_content)):
        secret = True
    if secret is True:	
      embed = discord.Embed(title = "Deleted Message by Richard", colour=discord.Colour.red())	
      embed.add_field(name = 'By ' + str(message.author) + ' in ' + str(message.channel)+':', value = str(f'||{message.content}||'))
      await channel.send(embed = embed)
    else:
      embed = discord.Embed (title = "Deleted Message", colour = discord.Colour.green())
      embed.add_field(name = 'By ' + str(message.author) + ' in ' + str(message.channel)+':', value = str(message.content))
      await channel.send(embed = embed)
    
#run Ping code: makes web server which gets pings every 5 mins
_ping()

#bot will run
bot.run(discord_token)