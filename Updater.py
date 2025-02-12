import requests
import os
import subprocess
import time
import zipfile
import shutil
import psutil
import discord
import asyncio
import threading
import platform  # To check OS type
from config import BOT_TOKEN, LOG_CHANNEL_ID, REPO_OWNER, REPO_NAME, ACCESS_TOKEN, APPLICATION_NAME, EXCLUDED_FILES

# Initialize Discord client
intents = discord.Intents.default()  # Use default intents
client = discord.Client(intents=intents)
channel = None  # Placeholder for log channel


# ----------------------------- DISCORD MESSAGING -----------------------------

# Sends a message to the log channel on Discord
async def send_discord_message(message):
    global channel
    if channel is None:
        channel = client.get_channel(LOG_CHANNEL_ID)
        if channel is None:
            print(f"Error: Channel with ID {LOG_CHANNEL_ID} not found.")
            return
    await channel.send(message)


# ----------------------------- GITHUB UPDATE HANDLING -----------------------------

# Downloads the latest version of the repository from GitHub as a ZIP file
def download_latest_release(REPO_OWNER, REPO_NAME, ACCESS_TOKEN):
    url = f"https://github.com/{REPO_OWNER}/{REPO_NAME}/archive/refs/heads/main.zip"
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        file_path = f"{REPO_NAME}.zip"
        with open(file_path, 'wb') as file:
            file.write(response.content)

        # Notify Discord
        client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message("Downloaded newest version."))
        return file_path
    else:
        client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message("Error while downloading newest version."))
        return None


# Extracts the downloaded ZIP file into the given directory
def extract_zip(file_path, extract_to):
    os.makedirs(extract_to, exist_ok=True)
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)


# Finds the process ID (PID) of a running script by its name
def get_pid_by_name(script_name):
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        if proc.info['cmdline'] and script_name in proc.info['cmdline']:
            return proc.pid
    return None


# Fetches the latest commit hash from GitHub
def update_and_restart(REPO_OWNER, REPO_NAME, ACCESS_TOKEN, last_commit_hash):
    latest_commit_hash = get_latest_commit(REPO_OWNER, REPO_NAME)

    # Check if there is a new commit
    if latest_commit_hash != last_commit_hash:
        client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message("Repository updated. Downloading the newest version..."))

        # Download the latest version
        file_path = download_latest_release(REPO_OWNER, REPO_NAME, ACCESS_TOKEN)
        if file_path:
            current_directory = os.path.dirname(__file__)
            zip_file_path = os.path.join(current_directory, file_path)
            extract_to_directory = current_directory

            # Extract files
            extract_zip(zip_file_path, extract_to_directory)

            # Set source directory name
            source_dir = os.path.join(current_directory, f"{REPO_NAME}-main")
            target_dir = current_directory

            # Get all file names from the extracted folder
            file_names = os.listdir(source_dir)

            # Move all files except excluded ones
            for file_name in file_names:
                if file_name not in EXCLUDED_FILES:
                    source_file = os.path.join(source_dir, file_name)
                    target_file = os.path.join(target_dir, file_name)

                    try:
                        os.replace(source_file, target_file)
                    except PermissionError as e:
                        client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message(f"PermissionError: {e}."))

                        # Try moving the file instead
                        try:
                            shutil.move(source_file, target_file)
                        except Exception as e:
                            client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message(f"Error while moving file {e}."))

            # Remove the extracted source directory and the ZIP file
            shutil.rmtree(source_dir)
            os.remove(zip_file_path)

            # Find and terminate the old bot process
            bot_pid = get_pid_by_name(f"{APPLICATION_NAME}.py")
            if bot_pid:
                client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message(f"Closing process with PID {bot_pid}."))
                psutil.Process(bot_pid).terminate()

            # Restart the bot based on Linux/Windows
            start_command = ["python3", f"{APPLICATION_NAME}.py"] if platform.system() != "Windows" else ["python", f"{APPLICATION_NAME}.py"]
            subprocess.Popen(start_command)  # Start the bot with the appropriate command

            client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message(f"Application restarted."))
            return latest_commit_hash
        else:
            client.loop.call_soon_threadsafe(asyncio.create_task, send_discord_message(f"Application couldn't update."))
            return last_commit_hash
    else:
        return last_commit_hash

# Fetches the latest commit hash from GitHub.
def get_latest_commit(REPO_OWNER, REPO_NAME):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/commits"
    headers = {"Authorization": f"token {ACCESS_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        commits = response.json()
        latest_commit = commits[0]
        return latest_commit['sha']
    else:
        return None


# ----------------------------- DISCORD BOT SETUP -----------------------------

# Runs when the bot connects to Discord.
@client.event
async def on_ready():
    global channel
    channel = client.get_channel(LOG_CHANNEL_ID)
    if channel is None:
        print(f"Error: Channel with ID {LOG_CHANNEL_ID} not found.")
    else:
        print(f"Bot is ready and connected with channel: {channel.name}")

# Starts the Discord bot in a separate thread.
def start_discord_bot():
    client.run(BOT_TOKEN)


# Start the Discord bot in a separate thread
threading.Thread(target=start_discord_bot).start()

# Wait until the channel is initialized
while channel is None:
    time.sleep(1)

# ----------------------------- UPDATE LOOP -----------------------------
last_commit_hash = None
while True:
    last_commit_hash = update_and_restart(REPO_OWNER, REPO_NAME, ACCESS_TOKEN, last_commit_hash)
    time.sleep(5)
