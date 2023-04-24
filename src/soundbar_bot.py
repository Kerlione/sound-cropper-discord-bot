import asyncio
import configparser
from audio_exporter import AudioExporter, AgeRestrictedError
import discord
from discord.ext import commands
from logger import logger, file_handler
from pytube.exceptions import PytubeError


async def wrap_with_retries(ctx: commands.Context, function, command_name: str):
    youtube_failure = False
    for i in range(0, max_download_attempts):
        try:
            logger.info(
                f"[{command_name}] Serving request. Attempt: {i + 1} of {max_download_attempts}"
            )
            result = function()
            with open(result, 'rb') as f:
                file = discord.File(f)

            # Send the file
            await ctx.send(file=file)
            youtube_failure = False
            break
        except ValueError as e:
            logger.error(f"Processing failed with error: {str(e)}")
            await ctx.send(
                f'Processing failed with error: {str(e)}. Please, try again')
            break
        except PytubeError as e:
            logger.error(f"Processing failed with error: {str(e)}")
            youtube_failure = True
            await ctx.send(
                f'Failed to retrieve YouTube video. Retrying... Attempt {i + 1} from {max_download_attempts}'
            )
        except AgeRestrictedError as e:
            logger.error(f"Processing failed with error: {str(e)}")
            await ctx.send(
                f'YouTube video access failed with error: \'{str(e)}\'.')
        except Exception as e:
            logger.error(f'Unexpected error occurred: \'{str(e)}\'')
            await ctx.send(
                f'Unexpected error occurred: \'{str(e)}\'. Please, contact someone :)'
            )
        logger.debug("Sleeping for 2 seconds...")
        await asyncio.sleep(2)
    if youtube_failure:
        await ctx.send(
            'Failed to perform the request. Please, try again later. If the error persists, contact someone :)'
        )


def parse_int(string, default: int) -> int:
    try:
        return int(string)
    except ValueError:
        return default

logger.info("Loading configuration")

config = configparser.ConfigParser()
config.read('config.ini')

logger.info("Configuration loaded")

max_download_attempts = parse_int(
    config.get('General', 'MAX_RETRIES', fallback=6), 6)
max_allowed_duration = parse_int(
    config.get('General', 'MAX_AUDIO_DURATION_SECONDS', fallback=180), 180)
token = config.get('General', 'BOT_TOKEN')
command_prefix = config.get('General', 'COMMAND_PREFIX', fallback='!')
logger.info(f"Working with settings: MAX_RETRIES:{max_download_attempts};MAX_DURATION:{max_allowed_duration};COMMAND_PREFIX:{command_prefix}")

if not token:
    logger.error("Token not found in configuration")
    raise ValueError(
        'Bot token not found. Update the config.ini BOT_TOKEN value')

intents = discord.Intents.default()
intents.message_content = True

exporter = AudioExporter(logger, max_allowed_duration)

bot = commands.Bot(command_prefix=command_prefix, intents=intents)


@bot.command(
    name='crop',
    help=
    'Get cropped mp3 audio from YouTube or Coub. Usage: !crop url start_second end_second (max duration = 180s). Example: !crop https://coub.com/view/so6aq 0 5'
)
async def crop(ctx: commands.Context, url: str, start: int = 0, end: int = -1):
    logger.info(f"Received request from {ctx.author.display_name} with arguments {ctx.args}")
    await wrap_with_retries(
        ctx, lambda: exporter.load_and_crop(url, False, start, end), "CROP")


@bot.command(
    name='fullcrop',
    help=
    'Get the mp3 of the YouTube or Coub video. Usage: !fullcrop url (max duration = 180s). Example: !fullcrop https://coub.com/view/so6aq'
)
async def full_crop(ctx, url: str):
    logger.info(f"Received request from {ctx.author.display_name} with arguments {ctx.args}")
    await wrap_with_retries(ctx, lambda: exporter.load_and_crop(url, True), "FULLCROP")

@bot.command(
    name='cropfull',
    help=
    'Get the mp3 of the YouTube or Coub video. Usage: !cropfull url (max duration = 180s). Example: !cropfull https://coub.com/view/so6aq'
)
async def crop_full(ctx, url: str):
    logger.info(f"Received request from {ctx.author.display_name} with arguments {ctx.args}")
    await wrap_with_retries(ctx, lambda: exporter.load_and_crop(url, True), "FULLCROP")

logger.info("Starting bot...")
bot.run(token, log_handler=file_handler)
logger.info("Bot closed")