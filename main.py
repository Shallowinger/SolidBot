import discord
from discord.ext import commands
import os
import json
import asyncio

# Load environment variables from .env file
from dotenv import load_dotenv

load_dotenv()

token = os.getenv('TOKEN')
owner_id = int(os.getenv('OWNER_ID'))

# Ensure that the 'images/' directory exists
if not os.path.exists('images'):
  os.makedirs('images')

intents = discord.Intents.default()
intents.messages = True  # Enable message events including attachments
intents.guilds = True  # Enable guild events
intents.guild_messages = True  # Enable message events in guilds
intents.message_content = True  # Enable message content intent

bot = commands.Bot(command_prefix='*', intents=intents)


# Load image channels from JSON file on bot startup
def load_image_channels():
  try:
    with open("config.json", "r") as f:
      return json.load(f)
  except FileNotFoundError:
    return {}


# Save image channels to JSON file on bot shutdown
def save_image_channels(image_channels):
  with open("config.json", "w") as f:
    json.dump(image_channels, f)


# Define the image channels dictionary
image_channels = load_image_channels()


# Event: Bot is ready
@bot.event
async def on_ready():
  print(f'We have logged in as {bot.user}')

  @bot.command()
  @commands.has_permissions(manage_messages=True)
  async def clear(ctx):
    try:
      await ctx.channel.purge(
          limit=100000)  # Set a large limit to clear the entire channel
      message = await ctx.send("Channel cleared.")
      await asyncio.sleep(5)
      await message.delete()
    except discord.errors.NotFound as e:
      print(f"Error deleting message: {e}")


# Command: Set image channel
@bot.command()
async def setimagechannel(ctx):
  if ctx.author.id != owner_id:
    await ctx.send("Only the bot owner can use this command.")
    return

  image_channels[str(ctx.guild.id)] = ctx.channel.id
  save_image_channels(image_channels)
  await ctx.send(f'Image channel set to {ctx.channel.mention} for this server.'
                 )


# Command: Send image to all servers with specified image channel
@bot.command()
async def sendimage(ctx):
  if ctx.author.id != owner_id:
    await ctx.send("Only the bot owner can use this command.")
    return

  if not ctx.message.attachments:
    await ctx.send("Error: No image attached.")
    return

  if str(ctx.guild.id) not in image_channels:
    await ctx.send("Error: No image channel set for this server.")
    return

  images_sent = 0
  for guild_id, channel_id in image_channels.items():
    guild = bot.get_guild(int(guild_id))
    if guild:
      channel = guild.get_channel(channel_id)
      if channel:
        try:
          for attachment in ctx.message.attachments:
            if attachment.content_type.startswith('image'):
              filename = f'images/{attachment.filename}'
              await attachment.save(filename)
              with open(filename, 'rb') as f:
                image = discord.File(f)
                await channel.send(file=image)
                images_sent += 1
              os.remove(filename)  # Delete the image after sending
        except Exception as e:
          print(f"Error sending images to {guild.name}: {e}")
      else:
        print(f"Error: Image channel not found for server: {guild.name}")

  await ctx.send(
      f"{images_sent} image(s) sent to all servers with designated image channel."
  )


# Start the bot
bot.run(token)
