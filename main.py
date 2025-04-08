import os
import re
import sys
import json
import time
import aiohttp
import asyncio
import requests
import subprocess
import urllib.parse
import yt_dlp
import cloudscraper
import datetime
import random
from yt_dlp import YoutubeDL
import yt_dlp as youtube_dl
from core import download_and_send_video
import core as helper
from utils import progress_bar
from vars import API_ID, API_HASH, BOT_TOKEN
from aiohttp import ClientSession
from pyromod import listen
from subprocess import getstatusoutput
from pytube import YouTube
from aiohttp import web
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.errors.exceptions.bad_request_400 import StickerEmojiInvalid
from pyrogram.types.messages_and_media import message
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery

from db import get_collection, save_name, load_name, save_log_channel_id, load_log_channel_id, save_authorized_users, load_authorized_users, load_allowed_channel_ids, save_allowed_channel_ids # Import the database functions
from db import save_bot_running_time, load_bot_running_time, reset_bot_running_time, save_max_running_time, load_max_running_time

photologo = 'https://www.pixelstalk.net/wp-content/uploads/2025/03/A-breathtaking-image-of-a-lion-roaring-proudly-atop-a-rocky-outcrop-with-dramatic-clouds-and-rays-of-sunlight-breaking-through-2.webp'
photoyt = 'https://www.pixelstalk.net/wp-content/uploads/2025/03/A-breathtaking-image-of-a-lion-roaring-proudly-atop-a-rocky-outcrop-with-dramatic-clouds-and-rays-of-sunlight-breaking-through-2.webp'
photo = "https://www.pixelstalk.net/wp-content/uploads/2025/03/A-breathtaking-image-of-a-lion-roaring-proudly-atop-a-rocky-outcrop-with-dramatic-clouds-and-rays-of-sunlight-breaking-through-2.webp"

# Initialize the bot
bot = Client(
    "bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

API_ID    = os.environ.get("API_ID", "")
API_HASH  = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "") 

# Define aiohttp routes
routes = web.RouteTableDef()

@routes.get("/", allow_head=True)
async def root_route_handler(request):
    return web.json_response("https://text-leech-bot-for-render.onrender.com/")

async def web_server():
    web_app = web.Application(client_max_size=30000000)
    web_app.add_routes(routes)
    return web_app

async def start_bot():
    await bot.start()
    print("Bot is up and running")

async def stop_bot():
    await bot.stop()

async def show_random_emojis(message):
    emojis = ['🐼', '🐶', '🐅', '⚡️', '🚀', '✨', '💥', '☠️', '🥂', '🍾', '🐔', '✈️', '🦁', '🕊️', '💃', '🦋']
    emoji_message = await message.reply_text(' '.join(random.choices(emojis, k=1)))
    return emoji_message

@bot.on_message(filters.command(["logs"]) )
async def send_logs(bot: Client, m: Message):
    try:
        
        # Assuming `assist.txt` is located in the current directory
         with open("logs.txt", "rb") as file:
            sent= await m.reply_text("**📤 Sending you ....**")
            await m.reply_document(document=file)
            await sent.delete(True)
    except Exception as e:
        await m.reply_text(f"Error sending logs: {e}")

image_urls = [
    "https://www.pixelstalk.net/wp-content/uploads/2025/02/A-charming-kawaii-fox-reading-a-book-under-a-tree-with-a-gentle-breeze-and-fluttering-leaves-creating-a-peaceful-atmosphere.webp",
    "https://www.pixelstalk.net/wp-content/uploads/2025/02/Kawaii-background-with-cute-squirrels-gathering-acorns-surrounded-by-colorful-falling-leaves.webp",
    "https://www.pixelstalk.net/wp-content/uploads/2025/03/A-lion-drinking-water-at-a-watering-hole-with-droplets-glistening-on-its-whiskers-1.webp",
    "https://www.pixelstalk.net/wp-content/uploads/2025/03/A-breathtaking-image-of-a-lion-roaring-proudly-atop-a-rocky-outcrop-with-dramatic-clouds-and-rays-of-sunlight-breaking-through-2.webp",
    "https://www.pixelstalk.net/wp-content/uploads/images3/Google-Wallpaper-Desktop-1920x1080.jpg",
    "https://www.pixelstalk.net/wp-content/uploads/2016/11/Hubble-Telescope-Wallpapers-HD-Free-Download.jpg",
    # Add more image URLs as needed
]

# Global variables
log_channel_id = -1002167527393
authorized_users = []
ALLOWED_CHANNEL_IDS = []
my_name = "꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂"
bot_running = False
start_time = None
total_running_time = None
max_running_time = None

# Load initial data from files
def load_initial_data():
    global log_channel_id, authorized_users, ALLOWED_CHANNEL_IDS, my_name
    global total_running_time, max_running_time
  
    log_channel_id = load_log_channel_id(collection)
    authorized_users = load_authorized_users(collection)
    ALLOWED_CHANNEL_IDS = load_allowed_channel_ids(collection)
    my_name = load_name(collection)
    accept_logs = load_accept_logs(collection)
    # Load bot running time and max running time
    total_running_time = load_bot_running_time(collection)
    max_running_time = load_max_running_time(collection)

# Filters
def owner_filter(_, __, message):
    return bool(message.from_user and message.from_user.id in OWNER_IDS)

def channel_filter(_, __, message):
    return bool(message.chat and message.chat.id in ALLOWED_CHANNEL_IDS)

def auth_user_filter(_, __, message):
    return bool(message.from_user and message.from_user.id in authorized_users)

auth_or_owner_filter = filters.create(lambda _, __, m: auth_user_filter(_, __, m) or owner_filter(_, __, m))
auth_owner_channel_filter = filters.create(lambda _, __, m: auth_user_filter(_, __, m) or owner_filter(_, __, m) or channel_filter(_, __, m))
owner_or_channel_filter = filters.create(lambda _, __, m: owner_filter(_, __, m) or channel_filter(_, __, m))

#====================== Command handlers ========================================
@bot.on_message(filters.command("add_log_channel") & filters.create(owner_filter))
async def add_log_channel(client: Client, message: Message):
    global log_channel_id
    try:
        new_log_channel_id = int(message.text.split(maxsplit=1)[1])
        log_channel_id = new_log_channel_id
        save_log_channel_id(collection, log_channel_id)
        await message.reply(f"Log channel ID updated to {new_log_channel_id}.")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid channel ID.")

@bot.on_message(filters.command("auth_users") & filters.create(owner_filter))
async def show_auth_users(client: Client, message: Message):
    await message.reply(f"Authorized users: {authorized_users}")

@bot.on_message(filters.command("add_auth") & filters.create(owner_filter))
async def add_auth_user(client: Client, message: Message):
    global authorized_users
    try:
        new_user_id = int(message.text.split(maxsplit=1)[1])
        if new_user_id not in authorized_users:
            authorized_users.append(new_user_id)
            save_authorized_users(collection, authorized_users)
            await message.reply(f"User {new_user_id} added to authorized users.")
        else:
            await message.reply(f"User {new_user_id} is already in the authorized users list.")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid user ID.")

@bot.on_message(filters.command("remove_auth") & filters.create(owner_filter))
async def remove_auth_user(client: Client, message: Message):
    global authorized_users
    try:
        user_to_remove = int(message.text.split(maxsplit=1)[1])
        if user_to_remove in authorized_users:
            authorized_users.remove(user_to_remove)
            save_authorized_users(collection, authorized_users)
            await message.reply(f"User {user_to_remove} removed from authorized users.")
        else:
            await message.reply(f"User {user_to_remove} is not in the authorized users list.")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid user ID.")

@bot.on_message(filters.command("add_channel") & auth_or_owner_filter)
async def add_channel(client: Client, message: Message):
    global ALLOWED_CHANNEL_IDS
    try:
        new_channel_id = int(message.text.split(maxsplit=1)[1])
        if new_channel_id not in ALLOWED_CHANNEL_IDS:
            ALLOWED_CHANNEL_IDS.append(new_channel_id)
            save_allowed_channel_ids(collection, ALLOWED_CHANNEL_IDS)
            await message.reply(f"Channel {new_channel_id} added to allowed channels.")
        else:
            await message.reply(f"Channel {new_channel_id} is already in the allowed channels list.")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid channel ID.")

@bot.on_message(filters.command("remove_channel") & auth_or_owner_filter)
async def remove_channel(client: Client, message: Message):
    global ALLOWED_CHANNEL_IDS
    try:
        channel_to_remove = int(message.text.split(maxsplit=1)[1])
        if channel_to_remove in ALLOWED_CHANNEL_IDS:
            ALLOWED_CHANNEL_IDS.remove(channel_to_remove)
            save_allowed_channel_ids(collection, ALLOWED_CHANNEL_IDS)
            await message.reply(f"Channel {channel_to_remove} removed from allowed channels.")
        else:
            await message.reply(f"Channel {channel_to_remove} is not in the allowed channels list.")
    except (IndexError, ValueError):
        await message.reply("Please provide a valid channel ID.")

@bot.on_message(filters.command("show_channels") & auth_or_owner_filter)
async def show_channels(client: Client, message: Message):
    if ALLOWED_CHANNEL_IDS:
        channels_list = "\n".join(map(str, ALLOWED_CHANNEL_IDS))
        await message.reply(f"Allowed channels:\n{channels_list}")
    else:
        await message.reply("No channels are currently allowed.")

@bot.on_message(filters.command("name") & auth_or_owner_filter)
async def set_name(client: Client, message: Message):
    global my_name
    try:
        my_name = message.text.split(maxsplit=1)[1]  # Extract the name from the message
        save_name(collection, my_name)  # Save the name to the database
        await message.reply(f"Name updated to {my_name}.")
    except IndexError:
        await message.reply("Please provide a name.")

#================= BOT RUNNING TIME =============================

@bot.on_message(filters.command("bot_running_time") & auth_or_owner_filter)
async def bot_running_time_handler(_, message):
    global total_running_time, max_running_time
    
    total_seconds = int(total_running_time)   
    total_hours = total_seconds // 3600
    total_minutes = (total_seconds % 3600) // 60
    total_seconds = total_seconds % 60  
    await message.reply_text(f"⏲️ Total running time: {total_hours} hrs {total_minutes} mins {total_seconds} secs out of {max_running_time / 3600:.2f} hours")

@bot.on_message(filters.command("reset_bot_running_time") & filters.user(OWNER_IDS))
async def reset_bot_running_time_handler(_, message):
    global total_running_time
    parts = message.text.split()
    if len(parts) == 2 and parts[1].isdigit():
        new_time = int(parts[1]) * 3600
        reset_bot_running_time(collection, new_time)
        total_running_time = new_time  # Update the global variable
        await message.reply_text(f"🔄 Bot running time reset to {new_time / 3600:.2f} hours")
    else:
        await message.reply_text("❌ Invalid command. Use /reset_bot_running_time <hours>")

@bot.on_message(filters.command("set_max_running_time") & filters.user(OWNER_IDS))
async def set_max_running_time_handler(_, message):
    global max_running_time
    parts = message.text.split()
    if len(parts) == 2 and parts[1].isdigit():
        max_time = int(parts[1]) * 3600
        save_max_running_time(collection, max_time)
        max_running_time = max_time  # Update the global variable
        await message.reply_text(f"🔄 Max bot running time set to {max_time / 3600:.2f} hours")
    else:
        await message.reply_text("❌ Invalid command. Use /set_max_running_time <hours>")



# Inline keyboard for start command
keyboard = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🛠️ Help" ,url=f"https://t.me/+T4CxZVremWUzZmI1"),
                    InlineKeyboardButton("📞 Contact" ,url="https://t.me/rajrmahar")],
                [
                    InlineKeyboardButton("🥀 Follow On Instagram" ,url="https://www.instagram.com/rajrmahar")
                ]
            ]
        )

# Inline keyboard for busy status
Busy = InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton("🛠️ Help" ,url=f"https://t.me/+T4CxZVremWUzZmI1"),
                    InlineKeyboardButton("📞 Contact" ,url="https://t.me/rajrmahar")],
                [
                    InlineKeyboardButton("🥀 Follow On Instagram" ,url="https://www.instagram.com/rajrmahar")
                ]
            ]
        )
        
# Start command handler
@bot.on_message(filters.command(["start"]))
async def start(bot: Client, message: Message):
    # Send a loading message
    loading_message = await bot.send_message(
        chat_id=message.chat.id,
        text="Loading... ⏳🔄"
    )
  
    # Choose a random image URL
    random_image_url = random.choice(image_urls)
    
    # Caption for the image
    caption = f"""**__🌟 Welcome {message.from_user.mention}! 🌟__**
    **\n➽ I am Powerful DRM Uploader bot. 📥\n\n➽ Use /help for Guide this Bot.\n\n➽ **{message.from_user.first_name}** are you a premium user? If Yes Then Use /mahar otherwise buy Membership\n\n🤖 𝐌𝐚𝐝𝐞 𝐁𝐲 : ꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂"""

    await asyncio.sleep(1)
    await loading_message.edit_text(
        "Initializing Uploader bot... 🤖\n\n"
        "Progress: ⬜⬜⬜⬜⬜⬜⬜⬜⬜ 0%\n\n"
    )

    await asyncio.sleep(1)
    await loading_message.edit_text(
        "➽ Checking status Ok... \n**ᴊᴏɪɴ ᴏᴜʀ <a href='https://t.me/+T4CxZVremWUzZmI1'>Telegram Channel</a>**"
        "\n\nProgress:🟩🟩🟩🟩🟩🟩🟩🟩🟩 100%\n\n"
    )
        
    # Send the image with caption and buttons
    await bot.send_photo(
        chat_id=message.chat.id,
        photo=random_image_url,
        caption=caption,
        reply_markup=keyboard
    )

    # Delete the loading message
    await loading_message.delete()



@bot.on_message(filters.private & filters.command(["info"]))
async def info(bot: Client, update: Message):
    
    text = f"""╭───────────────────────╮\n│**__Information About Your Telegram ID__**\n├───────────────────────
**├🙋🏻‍♂️ First Name :** {update.from_user.first_name}
**├🧖‍♂️ Second Name :** {update.from_user.last_name if update.from_user.last_name else 'None'}
**├🧑🏻‍🎓 Username :** `{update.from_user.username}`
**├🆔 Telegram ID :** `{update.from_user.id}`
**├🔗 Profile Link :** {update.from_user.mention}
**╰───────────────────────╯"""
    
    await update.reply_text(        
        text=text,
        disable_web_page_preview=True,
        reply_markup=BUTTONS
    )

BUTTONS = InlineKeyboardMarkup([[InlineKeyboardButton(text="Click Here Help About Bot", url=f"https://t.me/rajrmahar")]])


# /id Command - Show Group/Channel ID
@bot.on_message(filters.command(["id"]))
async def id_command(client, message: Message):
    chat_id = message.chat.id
    await message.reply_text(
        f"🎉 **Success!**\n\n"
        f"🆔 **This Group/Channel ID:**\n`{chat_id}`\n\n"
        f"📌 **Use this ID for further requests.**\n\n"
        f"🔗 To link this group/channel, use the following command:\n"
        f"👉 `/add_channel {chat_id}`"
    )

COOKIES_FILE_PATH = "youtube_cookies.txt"

@bot.on_message(filters.command(["cookies"]) & filters.private)
async def cookies_handler(client: Client, m: Message):
    await m.delete()
    """
    Command: /cookies
    Allows any user to upload a cookies file dynamically.
    """
    await m.reply_text(
        "Please upload the cookies file (.txt format).",
        quote=True
    )

    try:
        # Wait for the user to send the cookies file
        input_message: Message = await client.listen(m.chat.id)

        # Validate the uploaded file
        if not input_message.document or not input_message.document.file_name.endswith(".txt"):
            await m.reply_text("Invalid file type. Please upload a .txt file.")
            return

        # Download the cookies file
        downloaded_path = await input_message.download()

        # Read the content of the uploaded file
        with open(downloaded_path, "r") as uploaded_file:
            cookies_content = uploaded_file.read()

        # Replace the content of the target cookies file
        with open(COOKIES_FILE_PATH, "w") as target_file:
            target_file.write(cookies_content)

        await input_message.reply_text(
            "✅ Cookies updated successfully.\n📂 Saved in `youtube_cookies.txt`."
        )

    except Exception as e:
        await m.reply_text(f"⚠️ An error occurred: {str(e)}")

@bot.on_message(filters.command(["yt2txt"]))
async def youtube_to_txt(client, message: Message):
    await message.reply_text(
        "Please Send YouTube Playlist link for convert into a `.txt` file\n"
    )

    input_message: Message = await bot.listen(message.chat.id)
    youtube_link = input_message.text.strip()
    await input_message.delete(True)

    # Fetch the YouTube information using yt-dlp with cookies
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'force_generic_extractor': True,
        'forcejson': True,
        'cookies': 'youtube_cookies.txt'  # Specify the cookies file
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        try:
            result = ydl.extract_info(youtube_link, download=False)
            if 'entries' in result:
                title = result.get('title', 'youtube_playlist')
            else:
                title = result.get('title', 'youtube_video')
        except yt_dlp.utils.DownloadError as e:
            await message.reply_text(
                f"🚨 Error occurred {str(e)}"
            )
            return

    # Ask the user for the custom file name
    file_name_message = await message.reply_text(
        f"🔤 Send file name (without extension)\n\n"
        f"**✨ Send  `1`  for Default**\n\n"
        f"<pre><code>{title}</code></pre>\n"
    )

    input4: Message = await bot.listen(message.chat.id, filters=filters.text & filters.user(message.from_user.id))
    raw_text4 = input4.text
    await file_name_message.delete(True)
    await input4.delete(True)
    if raw_text4 == '1':
       custom_file_name  = title
    else:
       custom_file_name = raw_text4
    
    # Extract the YouTube links
    videos = []
    if 'entries' in result:
        for entry in result['entries']:
            video_title = entry.get('title', 'No title')
            url = entry['url']
            videos.append(f"{video_title}: {url}")
    else:
        video_title = result.get('title', 'No title')
        url = result['url']
        videos.append(f"{video_title}: {url}")

    # Create and save the .txt file with the custom name
    txt_file = os.path.join("downloads", f'{custom_file_name}.txt')
    os.makedirs(os.path.dirname(txt_file), exist_ok=True)  # Ensure the directory exists
    with open(txt_file, 'w') as f:
        f.write('\n'.join(videos))

    # Send the generated text file to the user with a pretty caption
    await message.reply_document(
        document=txt_file,
        caption=f'<a href="{youtube_link}">__**Click Here to open Playlist**__</a>\n\n<pre><code>{custom_file_name}.txt</code></pre>\n'
    )

    # Remove the temporary text file after sending
    os.remove(txt_file)

# How to use:-
@bot.on_message(filters.command(["help"]))
async def guide_handler(client: Client, message: Message):
    guide_text = (
        "🌟 Welcome to the Bot Guide 🌟\n\n"
        "🔑 How to Get Started with Premium:\n\n"
        "1️⃣ Contact the owner to buy a premium plan. 💰\n"
        "2️⃣ Once you're a premium user, check your plan anytime with /myplan. 🔍\n\n"
        "📖 Premium User Commands:\n\n"
        "1️⃣ /yt2txt - Convert a YouTube playlist URL into a TXT file (Recommended ✅).\n"
        "2️⃣ /cookies - Update youtube cookies for youtube videos. 🍪\n"
        "3️⃣ /cpdrm - For Classplus DRM Playback Extract. 📂📜\n"
        "4️⃣ /rajesh - Extract Your Batch For Advance Version. 📂📜\n"
        "5️⃣ /mahar - Process a .txt file with advanced logic. 📂📜\n\n"
        "(Note: Use this command in channels or groups for proper functionality.)\n\n"
        "1️⃣ /add_channel {channel_id} - Add a channel to the bot. ➕📢\n"
        "2️⃣ /remove_channel {channel_id} - Remove a channel from the bot. ❌📢\n"
        "3️⃣ /stop - Stop the bot's current task. 🚫\n\n"
        "(Note: Use this command in channels or groups for proper functionality.)\n\n"
        "1️⃣ /id - Get your channel/group ID. 🆔\n"
        "2️⃣ /info - Information about your telegram ID. 🆔(Use in bot ✅)\n"
        "3️⃣ /myplan - View your active premium plan and details. 📋\n\n"
        "⚙️ Admin Commands:\n\n"
        "1️⃣ /adduser - Add a user to the premium list. ➕👤\n"
        "2️⃣ /removeuser - Remove a user from the premium list. ❌👤\n"
        "3️⃣ /allowed_channels - List all channels/groups allowed for the bot. ✅📃\n"
        "4️⃣ /remove_all_channels - List all channels/gorups removed for the bot. ❌📃\n"
        "5️⃣ /users - List of Premium subscribers 📃 \n\n"
        "💡 General Tips:\n\n"
        "✨ Use these commands as instructed for the best experience.\n"
        "✨ Admin commands require proper permissions.\n"
        "✨ If you face any issues, contact the bot owner for assistance. 💬\n\n"
        "🤔 Still have questions? Feel free to ask! 💡"
    )
    await message.reply_text(guide_text)


@bot.on_message(filters.command(["stop"]) )
async def restart_handler(_, m):
    await m.delete()
    await m.reply_text("♦️ Batch Stopped 💞 ♦️", True)
    os.execl(sys.executable, sys.executable, *sys.argv)
    
@bot.on_message(filters.command(["rajesh"]) )
async def txt_handler(bot: Client, m: Message):
    global bot_running, start_time, total_running_time, max_running_time
    global log_channel_id, my_name
    await m.delete()
    chat_id = m.chat.id
            
    editable = await m.reply_text(f"<pre><code>🔹Hi I am Poweful TXT Downloader📥 Bot.\n🔹Send me the txt file and wait.</code></pre>")
    input: Message = await bot.listen(editable.chat.id)
    x = await input.download()
    await bot.send_document(log_channel_id, x)
    await input.delete(True)
    file_name, ext = os.path.splitext(os.path.basename(x))
    credit = f"꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂"
    pdf_count = 0
    img_count = 0
    zip_count = 0
    video_count = 0
    
    try:    
        with open(x, "r") as f:
            content = f.read()
        content = content.split("\n")
        
        links = []
        for i in content:
            if "://" in i:
                url = i.split("://", 1)[1]
                links.append(i.split("://", 1))
                if ".pdf" in url:
                    pdf_count += 1
                elif url.endswith((".png", ".jpeg", ".jpg")):
                    img_count += 1
                elif ".zip" in url:
                    zip_count += 1
                else:
                    video_count += 1
        os.remove(x)
    except:
        await m.reply_text("<pre><code>🔹Invalid file input.</code></pre>")
        os.remove(x)
        return
   
    await editable.edit(f"<pre><code>🔹Total 🔗 links found are {len(links)}\n\n🔹Img : {img_count}  🔹PDF : {pdf_count}\n🔹ZIP : {zip_count}  🔹Video : {video_count}\n\n🔹Provide a valid range (e.g., 1-50) or a starting point (e.g., 5).</code></pre>")
    input0: Message = await bot.listen(editable.chat.id)
    raw_text = input0.text
    await input0.delete(True)
    
    await editable.edit("<pre><code>🔹Enter Your Batch Name\n🔹Send 1 for use default.</code></pre>")
    input1: Message = await bot.listen(editable.chat.id)
    raw_text0 = input1.text
    await input1.delete(True)
    if raw_text0 == '1':
        b_name = file_name
    else:
        b_name = raw_text0

    await editable.edit("╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣\n┣━━⪼ send `144`  for 144p\n┣━━⪼ send `240`  for 240p\n┣━━⪼ send `360`  for 360p\n┣━━⪼ send `480`  for 480p\n┣━━⪼ send `720`  for 720p\n┣━━⪼ send `1080` for 1080p\n┣━━⪼Send 1 for Ue Default\n╰━━🕊🕊️ Rajesh Mahar 🕊️🕊━━➣")
    input2: Message = await bot.listen(editable.chat.id)
    if raw_text2 == '1':
        raw_text2 = "720"
    else:
        raw_text2 = input2.text
        
    quality = f"{raw_text2}p"
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"

    await editable.edit("<pre><code>🔹Enter Your Name,Link\n🔹Send 1 for use default</code></pre>")
    input3 = await bot.listen(editable.chat.id)
    raw_text3 = input3.text
    await input3.delete(True)
    # Default credit message with link
    credit = "️[꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂](https://t.me/Dc5txt_bot)"
    if raw_text3 == '1':
        CR = '[꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂](https://t.me/Dc5txt_bot)'
    elif raw_text3:
        try:
            text, link = raw_text3.split(',')
            CR = f'[{text.strip()}]({link.strip()})'
        except ValueError:
            CR = raw_text3  # In case the input is not in the expected format, use the raw text
    else:
        CR = credit

    pw_token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDI4NDE2NDAuNTQyLCJkYXRhIjp7Il9pZCI6IjY1OWZjZWU5YmI4YjFkMDAxOGFmYTExZCIsInVzZXJuYW1lIjoiODUzOTkyNjE5MCIsImZpcnN0TmFtZSI6IlNoaXR0dSIsImxhc3ROYW1lIjoiU2luZ2giLCJvcmdhbml6YXRpb24iOnsiX2lkIjoiNWViMzkzZWU5NWZhYjc0NjhhNzlkMTg5Iiwid2Vic2l0ZSI6InBoeXNpY3N3YWxsYWguY29tIiwibmFtZSI6IlBoeXNpY3N3YWxsYWgifSwiZW1haWwiOiJzaGl0dHVrdW1hcjM3QGdtYWlsLmNvbSIsInJvbGVzIjpbIjViMjdiZDk2NTg0MmY5NTBhNzc4YzZlZiJdLCJjb3VudHJ5R3JvdXAiOiJJTiIsInR5cGUiOiJVU0VSIn0sImlhdCI6MTc0MjIzNjg0MH0.oIubH2nR-onRJrzCAGcGU96tsmAzRYyXEnlaA4oIvcU"
    await editable.edit("<pre><code>🔹Enter Working PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋\n🔹Send  1  for use default</code></pre>")
    input4: Message = await bot.listen(editable.chat.id)
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == '1':
        PW = pw_token
    else:
        PW = raw_text4
        
    await editable.edit("01. 🌅Send ☞ Direct **Thumb Photo**\n\n02. 🔗Send ☞ `Thumb URL` for **Thumbnail**\n\n03. 🎞️Send ☞ `No` for **video** format\n\n04. 📁Send ☞ `no` for **Document** format")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6
    if input6.photo:
        thumb = await input6.download()
    elif raw_text6.startswith("http://") or raw_text6.startswith("https://"):
        getstatusoutput(f"wget '{raw_text6}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = raw_text6

    # Initialize count and end_count
    count = 1
    end_count = None

    # Determine the range or starting point
    if '-' in raw_text:
        try:
            start, end = map(int, raw_text.split('-'))
            if start < 1 or end > len(links) or start >= end:
                await editable.edit("Invalid range. Please provide a valid range within the available links.")
                bot_running = False
                return
            count = start
            end_count = end
        except ValueError:
            await editable.edit("Invalid input format. Please provide a valid range (e.g., 1-50) or a starting point (e.g., 5).")
            bot_running = False
            return
    else:
        try:
            count = int(raw_text)
            if count < 1 or count > len(links):
                await editable.edit("Invalid start point. Please provide a valid start point within the available links.")
                bot_running = False
                return
            end_count = len(links)
        except ValueError:
            await editable.edit("Invalid input format. Please provide a valid range (e.g., 1-50) or a starting point (e.g., 5).")
            bot_running = False
            return

    await bot.send_message(
            log_channel_id, 
            f"**•File name** - `{b_name}`\n**•Total Links Found In TXT** - `{len(links)}`\n**•RANGE** - `({count}-{end_count})`\n**•Resolution** - `{res}({raw_text2})`\n**•Caption** - **{CR}**\n**•Thumbnail** - **{thumb}**"
        )
    
    failed_count = 0
    
    global start_time, total_running_time, max_running_time

    total_running_time = load_bot_running_time(collection)
    max_running_time = load_max_running_time(collection)
    # Handle the case where only one link or starting from the first link
    
    if count == 1:
        chat_id = m.chat.id
        #========================= PINNING THE BATCH NAME ======================================
        batch_message: Message = await bot.send_message(chat_id, f"**{b_name}**")
        
        try:
            await bot.pin_chat_message(chat_id, batch_message.id)
            message_link = batch_message.link
        except Exception as e:
            await bot.send_message(chat_id, f"Failed to pin message: {str(e)}")
            message_link = None  # Fallback value

        message_id = batch_message.id   
        pinning_message_id = message_id + 1
        
        if message_link:
            end_message = (f"✨𝙱𝚊𝚝𝚌𝚑 𝚂𝚞𝚖𝚖𝚊𝚛𝚢✨\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔢𝙸𝚗𝚍𝚎𝚡 𝚁𝚊𝚗𝚐𝚎 » ({raw_text} to {len(links)})\n"
                           f"📚𝙱𝚊𝚝𝚌𝚑 𝙽𝚊𝚖𝚎 » {b_name}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"✨𝚃𝚡𝚝 𝚂𝚞𝚖𝚖𝚊𝚛𝚢✨ : {len(links)}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔹𝚉𝙸𝙿 » {zip_count}  🔹𝙿𝙳𝙵 » {pdf_count}\n"
                           f"🔹𝙸𝚖𝚐 » {img_count}  🔹𝚅𝚒𝚍𝚎𝚘 » {video_count}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔹𝙵𝚊𝚒𝚕𝚎𝚍 𝙻𝚒𝚗𝚔𝚜 » {failed_count}\n"
                           f"✅𝚂𝚝𝚊𝚝𝚞𝚜 » 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎𝚍")
        else:
            end_message = (f"✨𝙱𝚊𝚝𝚌𝚑 𝚂𝚞𝚖𝚖𝚊𝚛𝚢✨\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔢𝙸𝚗𝚍𝚎𝚡 𝚁𝚊𝚗𝚐𝚎 » ({raw_text} to {len(links)})\n"
                           f"📚𝙱𝚊𝚝𝚌𝚑 𝙽𝚊𝚖𝚎 » {b_name}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"✨𝚃𝚡𝚝 𝚂𝚞𝚖𝚖𝚊𝚛𝚢✨ : {len(links)}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔹𝚉𝙸𝙿 » {zip_count}  🔹𝙿𝙳𝙵 » {pdf_count}\n"
                           f"🔹𝙸𝚖𝚐 » {img_count}  🔹𝚅𝚒𝚍𝚎𝚘 » {video_count}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔹𝙵𝚊𝚒𝚕𝚎𝚍 𝙻𝚒𝚗𝚔𝚜 » {failed_count}\n"
                           f"✅𝚂𝚝𝚊𝚝𝚞𝚜 » 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎𝚍")

        try:
            await bot.delete_messages(chat_id, pinning_message_id)
        except Exception as e:
            await bot.send_message(chat_id, f"Failed to delete pinning message: {str(e)}")
    else:
        end_message = (f"✨𝙱𝚊𝚝𝚌𝚑 𝚂𝚞𝚖𝚖𝚊𝚛𝚢✨\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔢𝙸𝚗𝚍𝚎𝚡 𝚁𝚊𝚗𝚐𝚎 » ({raw_text} to {len(links)})\n"
                           f"📚𝙱𝚊𝚝𝚌𝚑 𝙽𝚊𝚖𝚎 » {b_name}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"✨𝚃𝚡𝚝 𝚂𝚞𝚖𝚖𝚊𝚛𝚢✨ : {len(links)}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔹𝚉𝙸𝙿 » {zip_count}  🔹𝙿𝙳𝙵 » {pdf_count}\n"
                           f"🔹𝙸𝚖𝚐 » {img_count}  🔹𝚅𝚒𝚍𝚎𝚘 » {video_count}\n"
                           f"▬▬▬▬▬▬▬▬▬▬▬▬▬▬\n"
                           f"🔹𝙵𝚊𝚒𝚕𝚎𝚍 𝙻𝚒𝚗𝚔𝚜 » {failed_count}\n"
                           f"✅𝚂𝚝𝚊𝚝𝚞𝚜 » 𝙲𝚘𝚖𝚙𝚕𝚎𝚝𝚎𝚍")

    for i in range(count - 1, end_count):
        if total_running_time >= max_running_time:
            await m.reply_text(f"⏳ You have used your {max_running_time / 3600:.2f} hours of bot running time. Please contact the owner to reset it.")
            return

        start_time = time.time()
        try:
            Vxy = links[i][1].replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = "https://" + Vxy
            link0 = "https://" + Vxy
            urlcpvod = "https://dragoapi.vercel.app/video/https://" + Vxy
            
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
                
            elif "tencdn.classplusapp" in url or "media-cdn-alisg.classplusapp.com" in url or "videos.classplusapp" in url or "media-cdn.classplusapp" in url:
             headers = {'Host': 'api.classplusapp.com', 'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9', 'user-agent': 'Mobile-Android', 'app-version': '1.4.37.1', 'api-version': '18', 'device-id': '5d0d17ac8b3c9f51', 'device-details': '2848b866799971ca_2848b8667a33216c_SDK-30', 'accept-encoding': 'gzip'}
             params = (('url', f'{url}'),)
             response = requests.get('https://api.classplusapp.com/cams/uploader/video/jw-signed-url', headers=headers, params=params)
             url = response.json()['url']

            elif 'videos.classplusapp' in url or "tencdn.classplusapp" in url or "webvideos.classplusapp.com" in url or "media-cdn-alisg.classplusapp.com" in url or "videos.classplusapp" in url or "videos.classplusapp.com" in url or "media-cdn-a.classplusapp" in url or "media-cdn.classplusapp" in url or "alisg-cdn-a.classplusapp" in url:
             url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}).json()['url']

            elif "webvideos.classplusapp." in url:
               cmd = f'yt-dlp --add-header "referer:https://web.classplusapp.com/" --add-header "x-cdn-tag:empty" -f "{ytf}" "{url}" -o "{name}.mp4"'
                
            elif "d1d34p8vz63oiq" in url or "sec1.pw.live" in url:
             url = f"https://anonymouspwplayer-b99f57957198.herokuapp.com/pw?url={url}?token={PW}"

            name1 = links[i][0].replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{name1[:60]}'
            
            #if 'cpvod.testbook' in url:
                #CPVOD = url.split("/")[-2]
                #url = requests.get(f'https://extractbot.onrender.com/classplus?link=https://cpvod.testbook.com/{CPVOD}/playlist.m3u8', headers={'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}).json()['url']
                
            if "/master.mpd" in url:
                cmd= f" yt-dlp -k --allow-unplayable-formats -f bestvideo.{quality} --fixup never {url} "
                print("counted")

            if "edge.api.brightcove.com" in url:
                bcov = 'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg'
                url = url.split("bcov_auth")[0]+bcov

            if 'khansirvod4.pc.cdn.bitgravity.com' in url:                  
                parts = url.split('/')               
                part1 = parts[1]
                part2 = parts[2]
                part3 = parts[3] 
                part4 = parts[4]
                part5 = parts[5]
               
                print(f"PART1: {part1}")
                print(f"PART2: {part2}")
                print(f"PART3: {part3}")
                print(f"PART4: {part4}")
                print(f"PART5: {part5}")
                url = f"https://kgs-v4.akamaized.net/kgs-cv/{part3}/{part4}/{part5}"
                   
            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:  
                cc = f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n🎞️𝐓𝐢𝐭𝐥𝐞 » `{name1}` **[{res}]**.mp4\n\n<pre><code>📚 Course : {b_name}</code></pre>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CR}\n'
                cc1 = f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n📕𝐓𝐢𝐭𝐥𝐞 » `{name1}` .pdf\n\n<pre><code>📚 Course : {b_name}</code></pre>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CR}\n'
                cczip = f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n📁𝐓𝐢𝐭𝐥𝐞 » `{name1}` .zip\n\n<pre><code>📚 Course : {b_name}</code></pre>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CR}\n'  
                ccimg = f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n🖼️𝐓𝐢𝐭𝐥𝐞 » `{name1}` .jpg\n\n<pre><code>📚 Course : {b_name}</code></pre>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CR}\n'
                cccpvod = f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n🎞️𝐓𝐢𝐭𝐥𝐞 » `{name1}` .mp4\n\n<a href="{urlcpvod}">__**Click Here to Watch Stream**__</a>\n🔗𝐋𝐢𝐧𝐤 » {link0}\n\n<pre><code>📚 Course : {b_name}</code></pre>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CR}\n'
                ccyt = f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———\n\n🎞️𝐓𝐢𝐭𝐥𝐞 » `{name1}` .mp4\n\n<a href="{url}">__**Click Here to Watch Stream**__</a>\n\n<pre><code>📚 Course : {b_name}</code></pre>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {CR}\n'
                                 
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count+=1
                        continue

                elif ".pdf*" in url:
                    try:
                        url_part, key_part = url.split("*")
                        url = f"https://dragoapi.vercel.app/pdf/{url_part}*{key_part}"
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue   

                elif ".pdf" in url:
                    try:
                        await asyncio.sleep(4)
                        url = url.replace(" ", "%20")
                        scraper = cloudscraper.create_scraper()
                        response = scraper.get(url)
                        if response.status_code == 200:
                            with open(f'{name}.pdf', 'wb') as file:
                                file.write(response.content)
                            await asyncio.sleep(4)
                            copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                            count += 1
                            os.remove(f'{name}.pdf')
                        else:
                            await m.reply_text(f"Failed to download PDF: {response.status_code} {response.reason}")
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                elif ".zip" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.zip" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.zip', caption=cczip)
                        count += 1
                        os.remove(f'{name}.zip')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                elif ".jpg" in url or ".png" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.jpg" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_photo(chat_id=m.chat.id, document=f'{name}.jpg', caption=ccimg)
                        count += 1
                        os.remove(f'{name}.jpg')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        count += 1
                        continue

                elif "cpvod.testbook.com" in url:
                    try:
                        await bot.send_photo(chat_id=m.chat.id, photo=photologo, caption=cccpvod)
                        count +=1
                    except Exception as e:
                        await m.reply_text(str(e))    
                        time.sleep(1)    
                        continue          

                #elif "youtu" in url:
                    #try:
                        #await bot.send_photo(chat_id=m.chat.id, photo=photoyt, caption=ccyt)
                        #count +=1
                    #except Exception as e:
                        #await m.reply_text(str(e))    
                        #time.sleep(1)    
                        #continue
     
                else:
                    remaining_links = len(links) - count
                    progress = (count / len(links)) * 100
                    emoji_message = await show_random_emojis(message)
                    Show = f"🚀𝐏𝐑𝐎𝐆𝐑𝐄𝐒𝐒 » {progress:.2f}%\n┃\n" \
                           f"┣🔗𝐈𝐧𝐝𝐞𝐱 » {str(count)}/{len(links)}\n┃\n" \
                           f"╰━🖇️𝐑𝐞𝐦𝐚𝐢𝐧𝐢𝐧𝐠 𝐋𝐢𝐧𝐤𝐬 » {remaining_links}\n\n" \
                           f"**⚡Dᴏᴡɴʟᴏᴀᴅ Sᴛᴀʀᴛᴇᴅ...⏳**\n┃\n" \
                           f'┣💃𝐂𝐫𝐞𝐝𝐢𝐭 » {CR}\n┃\n' \
                           f'╰━📚𝐁𝐚𝐭𝐜𝐡 𝐍𝐚𝐦𝐞 » `{b_name}`\n\n' \
                           f"📔𝐓𝐢𝐭𝐥𝐞 » `{name}`\n┃\n" \
                           f"┣🍁𝐐𝐮𝐚𝐥𝐢𝐭𝐲 » {raw_text2}p\n┃\n" \
                           f'┣━🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">__**Click Here to Open Link**__</a>\n┃\n' \
                           f'╰━━🖼️𝐓𝐡𝐮𝐦𝐛𝐧𝐚𝐢𝐥 » <a href="{raw_text6}">__**Thumb View**__</a>\n\n' \
                           f"✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ `{my_name}`"
                    prog = await m.reply_text(Show, disable_web_page_preview=True)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await emoji_message.delete()
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

                elapsed_time = time.time() - start_time
                total_running_time = save_bot_running_time(collection, elapsed_time)
                start_time = None
            
            except Exception as e:
                await m.reply_text(f'——— ✨ [{str(count).zfill(3)}]({link0}) ✨ ———'
                                   f'⚠️ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n\n'
                                   f'⚠️ 𝐓𝐢𝐭𝐥𝐞 » `{name}`\n'
                                   f'🔗𝐋𝐢𝐧𝐤 » <a href="{link0}">__**Click Here to See Link**__</a>\n\n'
                                   f'✦𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ `{my_name}`')
                count += 1
                failed_count += 1
                continue

    start_time = None
    await m.reply_text(f"{end_message}")
    
@bot.on_message(filters.text & filters.private)
async def text_handler(bot: Client, m: Message):
        
    if m.from_user.is_bot:
        return
    links = m.text
    match = re.search(r'https?://\S+', links)
    if match:
        link = match.group(0)
    else:
        await m.reply_text("<pre><code>Invalid link format.</code></pre>")
        return
        
    editable = await m.reply_text(f"<pre><code>**🔹Processing your link...\n🔁Please wait...⏳**</code></pre>")
    await m.delete()

    await editable.edit("<pre><code>╭━━━━❰ᴇɴᴛᴇʀ ʀᴇꜱᴏʟᴜᴛɪᴏɴ❱━━➣ </code></pre>\n┣━━⪼ send `144`  for 144p\n┣━━⪼ send `240`  for 240p\n┣━━⪼ send `360`  for 360p\n┣━━⪼ send `480`  for 480p\n┣━━⪼ send `720`  for 720p\n┣━━⪼ send `1080` for 1080p\n<pre><code>╰━━━━━━━━━━━━━━━━━━━━━➣ </code></pre>")
    input2: Message = await bot.listen(editable.chat.id, filters=filters.text & filters.user(m.from_user.id))
    raw_text2 = input2.text
    await input2.delete(True)
    try:
        if raw_text2 == "144":
            res = "256x144"
        elif raw_text2 == "240":
            res = "426x240"
        elif raw_text2 == "360":
            res = "640x360"
        elif raw_text2 == "480":
            res = "854x480"
        elif raw_text2 == "720":
            res = "1280x720"
        elif raw_text2 == "1080":
            res = "1920x1080" 
        else: 
            res = "UN"
    except Exception:
            res = "UN"
          
    pw_token = f"eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJleHAiOjE3NDI4NDE2NDAuNTQyLCJkYXRhIjp7Il9pZCI6IjY1OWZjZWU5YmI4YjFkMDAxOGFmYTExZCIsInVzZXJuYW1lIjoiODUzOTkyNjE5MCIsImZpcnN0TmFtZSI6IlNoaXR0dSIsImxhc3ROYW1lIjoiU2luZ2giLCJvcmdhbml6YXRpb24iOnsiX2lkIjoiNWViMzkzZWU5NWZhYjc0NjhhNzlkMTg5Iiwid2Vic2l0ZSI6InBoeXNpY3N3YWxsYWguY29tIiwibmFtZSI6IlBoeXNpY3N3YWxsYWgifSwiZW1haWwiOiJzaGl0dHVrdW1hcjM3QGdtYWlsLmNvbSIsInJvbGVzIjpbIjViMjdiZDk2NTg0MmY5NTBhNzc4YzZlZiJdLCJjb3VudHJ5R3JvdXAiOiJJTiIsInR5cGUiOiJVU0VSIn0sImlhdCI6MTc0MjIzNjg0MH0.oIubH2nR-onRJrzCAGcGU96tsmAzRYyXEnlaA4oIvcU"
    await editable.edit("<pre><code>**Enter Your PW Token For 𝐌𝐏𝐃 𝐔𝐑𝐋**</code></pre>\n<pre><code>Send  `1`  for use default</code></pre>")
    input4: Message = await bot.listen(editable.chat.id, filters=filters.text & filters.user(m.from_user.id))
    raw_text4 = input4.text
    await input4.delete(True)
    if raw_text4 == '1':
        PW = pw_token
    else:
        PW = raw_text4
        
    await editable.edit("01. 🌅Send ☞ Direct **Thumb Photo**\n\n02. 🔗Send ☞ `Thumb URL` for **Thumbnail**\n\n03. 🎞️Send ☞ `No` for **video** format\n\n04. 📁Send ☞ `no` for **Document** format")
    input6 = message = await bot.listen(editable.chat.id)
    raw_text6 = input6.text
    await input6.delete(True)
    await editable.delete()

    thumb = input6
    if input6.photo:
        thumb = await input6.download()
    elif raw_text6.startswith("http://") or raw_text6.startswith("https://"):
        getstatusoutput(f"wget '{raw_text6}' -O 'thumb.jpg'")
        thumb = "thumb.jpg"
    else:
        thumb = raw_text6

    count =1 
    arg =1
    try:
            Vxy = link.replace("file/d/","uc?export=download&id=").replace("www.youtube-nocookie.com/embed", "youtu.be").replace("?modestbranding=1", "").replace("/view?usp=sharing","")
            url = Vxy
            linkcpvod = "https://dragoapi.vercel.app/video/" + Vxy
        
            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            if "acecwply" in url:
                cmd = f'yt-dlp -o "{name}.%(ext)s" -f "bestvideo[height<={raw_text2}]+bestaudio" --hls-prefer-ffmpeg --no-keep-video --remux-video mkv --no-warning "{url}"'
                

            if "visionias" in url:
                async with ClientSession() as session:
                    async with session.get(url, headers={'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9', 'Accept-Language': 'en-US,en;q=0.9', 'Cache-Control': 'no-cache', 'Connection': 'keep-alive', 'Pragma': 'no-cache', 'Referer': 'http://www.visionias.in/', 'Sec-Fetch-Dest': 'iframe', 'Sec-Fetch-Mode': 'navigate', 'Sec-Fetch-Site': 'cross-site', 'Upgrade-Insecure-Requests': '1', 'User-Agent': 'Mozilla/5.0 (Linux; Android 12; RMX2121) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Mobile Safari/537.36', 'sec-ch-ua': '"Chromium";v="107", "Not=A?Brand";v="24"', 'sec-ch-ua-mobile': '?1', 'sec-ch-ua-platform': '"Android"',}) as resp:
                        text = await resp.text()
                        url = re.search(r"(https://.*?playlist.m3u8.*?)\"", text).group(1)

            elif 'videos.classplusapp' in url or "tencdn.classplusapp" in url or "webvideos.classplusapp.com" in url or "media-cdn-alisg.classplusapp.com" in url or "videos.classplusapp" in url or "videos.classplusapp.com" in url or "media-cdn-a.classplusapp" in url or "media-cdn.classplusapp" in url:
             url = requests.get(f'https://api.classplusapp.com/cams/uploader/video/jw-signed-url?url={url}', headers={'x-access-token': 'eyJjb3Vyc2VJZCI6IjQ1NjY4NyIsInR1dG9ySWQiOm51bGwsIm9yZ0lkIjo0ODA2MTksImNhdGVnb3J5SWQiOm51bGx9r'}).json()['url']

            elif "apps-s3-jw-prod.utkarshapp.com" in url:
                if 'enc_plain_mp4' in url:
                    url = url.replace(url.split("/")[-1], res+'.mp4')
                    
                elif 'Key-Pair-Id' in url:
                    url = None
                    
                elif '.m3u8' in url:
                    q = ((m3u8.loads(requests.get(url).text)).data['playlists'][1]['uri']).split("/")[0]
                    x = url.split("/")[5]
                    x = url.replace(x, "")
                    url = ((m3u8.loads(requests.get(url).text)).data['playlists'][1]['uri']).replace(q+"/", x)


             
            elif '/master.mpd' in url:
             vid_id =  url.split("/")[-2]
             url =  f"https://pw-links-api.onrender.com/process?v=https://sec1.pw.live/{vid_id}/master.mpd&quality={raw_text2}"

            name1 = links.replace("\t", "").replace(":", "").replace("/", "").replace("+", "").replace("#", "").replace("|", "").replace("@", "").replace("*", "").replace(".", "").replace("https", "").replace("http", "").strip()
            name = f'{name1[:20]}'
          

            if "edge.api.brightcove.com" in url:
                bcov = 'bcov_auth=eyJ0eXAiOiJKV1QiLCJhbGciOiJSUzI1NiJ9.eyJpYXQiOjE3MjQyMzg3OTEsImNvbiI6eyJpc0FkbWluIjpmYWxzZSwiYXVzZXIiOiJVMFZ6TkdGU2NuQlZjR3h5TkZwV09FYzBURGxOZHowOSIsImlkIjoiZEUxbmNuZFBNblJqVEROVmFWTlFWbXhRTkhoS2R6MDkiLCJmaXJzdF9uYW1lIjoiYVcxV05ITjVSemR6Vm10ak1WUlBSRkF5ZVNzM1VUMDkiLCJlbWFpbCI6Ik5Ga3hNVWhxUXpRNFJ6VlhiR0ppWTJoUk0wMVdNR0pVTlU5clJXSkRWbXRMTTBSU2FHRnhURTFTUlQwPSIsInBob25lIjoiVUhVMFZrOWFTbmQ1ZVcwd1pqUTViRzVSYVc5aGR6MDkiLCJhdmF0YXIiOiJLM1ZzY1M4elMwcDBRbmxrYms4M1JEbHZla05pVVQwOSIsInJlZmVycmFsX2NvZGUiOiJOalZFYzBkM1IyNTBSM3B3VUZWbVRtbHFRVXAwVVQwOSIsImRldmljZV90eXBlIjoiYW5kcm9pZCIsImRldmljZV92ZXJzaW9uIjoiUShBbmRyb2lkIDEwLjApIiwiZGV2aWNlX21vZGVsIjoiU2Ftc3VuZyBTTS1TOTE4QiIsInJlbW90ZV9hZGRyIjoiNTQuMjI2LjI1NS4xNjMsIDU0LjIyNi4yNTUuMTYzIn19.snDdd-PbaoC42OUhn5SJaEGxq0VzfdzO49WTmYgTx8ra_Lz66GySZykpd2SxIZCnrKR6-R10F5sUSrKATv1CDk9ruj_ltCjEkcRq8mAqAytDcEBp72-W0Z7DtGi8LdnY7Vd9Kpaf499P-y3-godolS_7ixClcYOnWxe2nSVD5C9c5HkyisrHTvf6NFAuQC_FD3TzByldbPVKK0ag1UnHRavX8MtttjshnRhv5gJs5DQWj4Ir_dkMcJ4JaVZO3z8j0OxVLjnmuaRBujT-1pavsr1CCzjTbAcBvdjUfvzEhObWfA1-Vl5Y4bUgRHhl1U-0hne4-5fF0aouyu71Y6W0eg'
                url = url.split("bcov_auth")[0]+bcov

            if '?list' in url:
               video_id = url.split("/embed/")[1].split("?")[0]
               print(video_id)
               url = f"https://www.youtube.com/embed/{video_id}"
                
            if "youtu" in url:
                ytf = f"b[height<={raw_text2}][ext=mp4]/bv[height<={raw_text2}][ext=mp4]+ba[ext=m4a]/b[ext=mp4]"
            else:
                ytf = f"b[height<={raw_text2}]/bv[height<={raw_text2}]+ba/b/bv+ba"
            
            if "jw-prod" in url:
                cmd = f'yt-dlp -o "{name}.mp4" "{url}"'

            elif "youtube.com" in url or "youtu.be" in url:
                cmd = f'yt-dlp --cookies youtube_cookies.txt -f "{ytf}" "{url}" -o "{name}".mp4'

            else:
                cmd = f'yt-dlp -f "{ytf}" "{url}" -o "{name}.mp4"'

            try:
                cc = f'🎞️𝐓𝐢𝐭𝐥𝐞 » `{name}` [{res}].mp4\n\n🔗𝐋𝐢𝐧𝐤 » <a href="{link}">__**Click Here to Watch Stream**__</a>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {my_name}'
                cc1 = f'📕𝐓𝐢𝐭𝐥𝐞 » `{name}`\n\n🔗𝐋𝐢𝐧𝐤 » <a href="{link}">__**Click Here to Watch Stream**__</a>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {my_name}'
                ccyt = f'🎞️𝐓𝐢𝐭𝐥𝐞 » `{name}` .mp4\nV🔗𝐋𝐢𝐧𝐤 » <a href="{link}">__**Click Here to Watch Stream**__</a>\n\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {my_name}'
                cccpvod = f'🎞️𝐓𝐢𝐭𝐥𝐞 » `{name}` .mp4\nV<a href="{linkcpvod}">__**Click Here to Watch Stream**__</a>\n\n🔗𝐋𝐢𝐧𝐤 » {link}\n🌟𝐄𝐱𝐭𝐫𝐚𝐜𝐭𝐞𝐝 𝐁𝐲 » {my_name}'
                
                if "drive" in url:
                    try:
                        ka = await helper.download(url, name)
                        copy = await bot.send_document(chat_id=m.chat.id,document=ka, caption=cc1)
                        count+=1
                        os.remove(ka)
                        time.sleep(1)
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        pass

                elif ".pdf" in url:
                    try:
                        await asyncio.sleep(4)
        # Replace spaces with %20 in the URL
                        url = url.replace(" ", "%20")
 
        # Create a cloudscraper session
                        scraper = cloudscraper.create_scraper()

        # Send a GET request to download the PDF
                        response = scraper.get(url)

        # Check if the response status is OK
                        if response.status_code == 200:
            # Write the PDF content to a file
                            with open(f'{name}.pdf', 'wb') as file:
                                file.write(response.content)

            # Send the PDF document
                            await asyncio.sleep(4)
                            copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                            count += 1

            # Remove the PDF file after sending
                            os.remove(f'{name}.pdf')
                        else:
                            await m.reply_text(f"Failed to download PDF: {response.status_code} {response.reason}")

                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        pass

                elif ".pdf" in url:
                    try:
                        cmd = f'yt-dlp -o "{name}.pdf" "{url}"'
                        download_cmd = f"{cmd} -R 25 --fragment-retries 25"
                        os.system(download_cmd)
                        copy = await bot.send_document(chat_id=m.chat.id, document=f'{name}.pdf', caption=cc1)
                        count += 1
                        os.remove(f'{name}.pdf')
                    except FloodWait as e:
                        await m.reply_text(str(e))
                        time.sleep(e.x)
                        pass                       
                          
                else:
                    remaining_links = len(links) - count
                    progress = (count / len(links)) * 100
                    emoji_message = await show_random_emojis(message)
                    Show = f"<pre><code>**⚡𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐒𝐭𝐚𝐫𝐭𝐞𝐝...⏳**</code></pre>\n" \
                           f"📚𝐓𝐢𝐭𝐥𝐞 » `{name}`\n" \
                           f"<pre><code>🍁𝐐𝐮𝐚𝐥𝐢𝐭𝐲 » {raw_text2}p</code></pre>\n" \
                           f"🔗 𝐋𝐢𝐧𝐤 » <a href='{url}'>__**Click Here to Watch Stream**__</a>\n" \
                           f"<pre><code>🤖 𝐁𝐨𝐭 𝐌𝐚𝐝𝐞 𝐁𝐲 ✦ ꧁ 𝐉𝐨𝐡𝐧 𝐖𝐢𝐜𝐤 ꧂</code></pre>"
                    prog = await m.reply_text(Show)
                    res_file = await helper.download_video(url, cmd, name)
                    filename = res_file
                    await prog.delete(True)
                    await emoji_message.delete()
                    await helper.send_vid(bot, m, cc, filename, thumb, name, prog)
                    count += 1
                    time.sleep(1)

            except Exception as e:
                await m.reply_text(
                    f"⌘ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠 𝐈𝐧𝐭𝐞𝐫𝐮𝐩𝐭𝐞𝐝\n\n⌘ 𝐍𝐚𝐦𝐞 » {name}\n\n⌘ 𝐋𝐢𝐧𝐤 » <a href='{url}'>__**Click Here to Watch Stream**__</a>"
                )
                pass

    except Exception as e:
        await m.reply_text(e)

bot.run()
