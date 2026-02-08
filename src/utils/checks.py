from config import *

def command_channel(ctx):
    return ctx.channel.id == COMMANDS_CHANNEL_ID
