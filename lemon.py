import os
import sys
from typing import List

from guilded.ext import commands

from core import exceptions

__version__ = "0.0.0"


# Setup checks


def test_dotenv() -> None:
    if type(os.getenv("DB_STRING")) != str:
        raise exceptions.DotEnvException("DB_STRING is not set.")
    if type(os.getenv("EMAIL")) != str:
        raise exceptions.DotEnvException("EMAIL is not set.")
    if type(os.getenv("PASSWORD")) != str:
        raise exceptions.DotEnvException("PASSWORD is not set.")


test_dotenv()


# Move to the script's home directory


root_path = os.path.dirname(os.path.abspath(__file__))
os.chdir(root_path)
del root_path


# Database


import database
import database.config


database.init_core()
database.init_modules()


# Load or create config object


config = database.config.Config.get()


# Setup guilded.py


def _prefix_callable(bot, message) -> List[str]:
    """Get bot prefix with optional mention function"""
    # TODO This should be extended for per-guild prefixes as dict
    # See https://github.com/Rapptz/RoboDanny/blob/rewrite/bot.py:_prefix_callable()
    base = []
    if config.mention_as_prefix:
        user_id = bot.user.id
        base += [f"<@!{user_id}> ", f"<@{user_id}> "]
    # TODO guild condition
    base.append(config.prefix)
    return base


from core.help import Help

bot = commands.Bot(
    command_prefix="!", help_command=Help(), description="I am a Test bot"
)


# Setup logging

from core import logging

bot_log = logging.Bot.logger(bot)
guild_log = logging.Guild.logger(bot)


# Setup listeners

already_loaded: bool = False


@bot.event
async def on_ready():
    """This is run on login and on reconnect."""
    global already_loaded

    if already_loaded:
        await bot_log.info(None, None, "Reconnected")
    else:
        await bot_log.info(None, None, "The pie is ready.")
        already_loaded = True


# Add required modules


from modules.base.admin.database import BaseAdminModule


modules = {
    "base.acl",
    "base.admin",
    "base.base",
    "base.errors",
    "base.logging",
}
db_modules = BaseAdminModule.get_all()
db_module_names = [m.name for m in db_modules]

for module in modules:
    if module in db_module_names:
        # This module is managed by database
        continue
    bot.load_extension(f"modules.{module}.module")
    print("Loaded module " + module, file=sys.stdout)  # noqa: T001

for module in db_modules:
    if not module.enabled:
        print("Skipping module " + module.name, file=sys.stdout)  # noqa: T001
        continue
    try:
        bot.load_extension(f"modules.{module.name}.module")
    except (ImportError, ModuleNotFoundError, commands.ExtensionNotFound):
        print(f"Module not found: {module.name}", file=sys.stdout)  # noqa: T001
        continue
    print("Loaded module " + module.name, file=sys.stdout)  # noqa: T001


# Run the bot

bot.run(os.getenv("EMAIL"), os.getenv("PASSWORD"))
