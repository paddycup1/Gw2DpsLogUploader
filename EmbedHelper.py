import discord  #python -m pip install -U git+https://github.com/Rapptz/discord.py@rewrite
from discord.ext import commands
import json
import sys

bot = commands.Bot(command_prefix="!", description="Discord Embed Helper")

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print(bot.user.id)
  print('------')

@bot.command()
async def embed(ctx):
  if len(sys.argv) > 1:
    with open(sys.argv[1], "r") as inputFile:
      embed = json.load(inputFile)
  else:
    embed = json.loads(ctx.message.content[7:])
  if "author" not in embed:
    embed["author"] = dict()
    embed["author"]["name"] = ctx.message.author.display_name
    embed["author"]["icon_url"] = ctx.message.author.avatar_url        
  await ctx.message.delete()        
  await ctx.send(embed = discord.Embed.from_data(embed))

with open("Config.json") as configFile:
  config = json.load(configFile)
if "DiscordBotToken" not in config:
  print("Can't find \"DiscordBotToken\" in Config.json!")

bot.run(config["DiscordBotToken"])