# sound-cropper-discord-bot
Simple Discord bot for downloading audio from YouTube and Coub videos with an option to crop it and get an mp3

# Main purpose
After Soundbar introduction by Discord, it became a pretty common task for me to download and crop various funny sounds.

I decided to make a bot, that would allow to 'exchange' the video URLs with mp3 files, with an option to crop the audio.

# Requirements

The bot is written using Python 3.8.10 and tested on ARM64 Ubuntu.

# Installation

*Not yet verified* The repository contains the [install.sh](./src/install.sh) file.

The steps are following:
1. Clone the repo
2. Update the [config.ini](./src/config.ini) file by adding your discord bot token (for bot creation and token obtaining, please refer to the [guide](https://discordpy.readthedocs.io/en/stable/discord.html))

````ini
[General]

BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
MAX_RETRIES=5
MAX_VIDEO_DURATION_SECONDS=180
COMMAND_PREFIX=!
````

3. Run the bot in one of the following ways:
    1. Self-managed - you run the script using via terminal and manually ensure that it runs after reboot on the machine
        1. Can be started via following commands:
        ````sh
        cd src
        python3 -m venv venv
        source venv/bin/activate
        pip install -r requirements.txt

        python run soundbar_bot.py
        ````
        2. In order to run in background on Linux - replace last command with:
        ````sh
        python run soundbar_bot.py &
        ````
    2. Run the [install.sh](./src/install.sh), which will create a daemon service and make it start on boot

# Configuration

There are following settings, available for manual configuration via [config.ini](./src/config.ini) file:
````ini
[General]
BOT_TOKEN=YOUR_DISCORD_BOT_TOKEN
MAX_RETRIES=5
MAX_VIDEO_DURATION_SECONDS=180
COMMAND_PREFIX=!
````

1. **BOT_TOKEN** - the Discord bot token
2. **MAX_RETRIES** - the pytube library tends to yield errors when accessing the video, so the retry mechanism was implemented to handle such errors, by retrying after a delay (default - *2 seconds*)
3. **MAX_VIDEO_DURATION_SECONDS** - in order to avoid large files processing, the length of downloaded audio tracks is limited. This parameter also sets the limit for a cropped audio duration
4. **COMMAND_PREFIX** - prefix of the commands for the bot

# Usage

Bot has following commands:
1. *prefix*help - default embedded command of bot to get the information about registered commands. Sample output can be seen below:
````
No Category:
  crop     Get cropped mp3 audio from YouTube or Coub. Usage: !crop url start...
  cropfull Get the mp3 of the YouTube or Coub video. Usage: !cropfull url (ma...
  fullcrop Get the mp3 of the YouTube or Coub video. Usage: !fullcrop url (ma...
  help     Shows this message

Type !help command for more info on a command.
You can also type !help category for more info on a category.
````
2. *prefix*crop - cropping of audio from the provided url, from specified start second till the specified end second
3. *prefix*cropfull - downloading all the audio from a supplied link 
  1. *prefix*fullcrop - an alias for the *cropfull*

