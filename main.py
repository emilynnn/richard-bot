#imports
import discord
import csv
import pandas as pd
import os, os.path
from discord.ext import commands
from Ping import _ping
from discord.ext.commands import Bot, has_permissions, CheckFailure


#discord token in secrets  
discord_token = os.environ['TOKEN']
COGS = 'log.py'

client = discord.Client()
bot = commands.Bot(command_prefix="!", case_insensitive=True, help_command=None)

#blacklist words
with open('blacklist.txt', 'r') as file:
  blacklist = [line.strip() for line in file]

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
@commands.has_permissions(manage_messages = True)
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
async def on_message_delete(message, member:discord.Member):
  message_content = message.content.lower()
  secret = False
  if not message.author.bot:
    channel = bot.get_channel(903269861671723042)
    with open(f'{message.guild.id}blacklist.txt', 'r') as file:
      blacklist = [line.strip() for line in file]
    for i in range(len(blacklist)):
      if (str(blacklist[i]) in str(message_content)):
        secret = True
    if secret is True:	
      df = pd.read_csv('offenders.csv')
      
      with open('offenders.csv', 'r') as f:
        reader = csv.reader(f)

        counter=0
        for row in reader:
          if(message.author.id == row[1] and counter!=1):
            df.loc[i, 'strike'] = int(row[2])+1 
            counter=1
            
            if(row[2]==3):
              role = discord.utils.get(member.server.roles, name ='Muted')
              await bot.add_roles(member, role)
              embed = discord.Embed(title = "User muted", description="Offender has hit 3 stikes.")
              await bot.say(embed = embed)
            
        if (counter!=1):
          with open('offenders.csv', 'a'):
            writer = csv.write
            data = [message.author.id, 1]
            writer.writerow(data)
        
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