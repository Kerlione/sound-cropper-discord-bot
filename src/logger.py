import logging

logger = logging.getLogger('bot')
logger.setLevel(logging.DEBUG)

# create a console handler
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create a file handler
file_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
file_handler.setLevel(logging.INFO)

# create a formatter
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')
ch.setFormatter(formatter)
file_handler.setFormatter(formatter)

# add the handler to the logger
logger.addHandler(ch)
logger.addHandler(file_handler)
