from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

async def research_warpgate(bot: BotAI, iteration):
    if (bot.structures(UnitTypeId.CYBERNETICSCORE).ready 
        and bot.can_afford(UpgradeId.WARPGATERESEARCH) 
        and bot.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0):
        
        cybercore = bot.structures(UnitTypeId.CYBERNETICSCORE).ready.first
        cybercore.research(UpgradeId.WARPGATERESEARCH)