from dataclasses import dataclass
from typing import List

from environs import Env

@dataclass
class Bot:
	token: str
	admin_ids: List[int]
	use_redis: bool

@dataclass
class Miscellaneous:
	other_parameters: str = None

@dataclass
class Config:
	bot: Bot
	misc: Miscellaneous


def get_config(path: str = None):
	env = Env()
	env.read_env(path)

	return Config(
		bot=Bot(
			token=env.str("BOT_TOKEN"),
			admin_ids=list(map(int, env.list("ADMINS"))),
			use_redis=env.bool("USE_REDIS")
		),
		misc=Miscellaneous()
	)
