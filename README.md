# Discord Auto-Updater Bot

A Discord bot that automatically checks for updates in a GitHub repository, downloads the latest version, and restarts itself when a new update is available.

## Features
✔️ Automatically checks for new updates in a GitHub repository  
✔️ Downloads and extracts the latest version  
✔️ Restarts the bot after updating  
✔️ Sends update logs to a specified Discord channel  

## Setup Instructions

### 1. Clone the Repository
```sh
git clone https://github.com/Cametolose/Discord-Bot-Updater.git
cd Discord-Bot-Updater
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Configure the Bot  
Edit `config.py` and update the following values:
```python
BOT_TOKEN = "your-bot-token-here"
LOG_CHANNEL_ID = 123456789  # Replace with your Discord log channel ID
REPO_OWNER = "your-github-username"
REPO_NAME = "your-repository-name"
ACCESS_TOKEN = "your-github-access-token"
APPLICATION_NAME = "your-application-name"  # Replace with .py at the end
```

### 4. Run the Bot
```sh
python Updater.py
```

## License
This project is licensed under the MIT License.
