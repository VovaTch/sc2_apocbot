from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId

async def train_stalkers_basic(bot: BotAI, iteration, warp=False):
    
    if warp is False:
        for gateway in bot.structures(UnitTypeId.GATEWAY).ready:
            if (bot.can_afford(UnitTypeId.STALKER) and gateway.is_idle):
                gateway.train(UnitTypeId.STALKER)