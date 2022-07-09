from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.unit_typeid import UnitTypeId as id
from sc2.ids.upgrade_id import UpgradeId


async def research_upgrade(bot: BotAI, struct_id: id, upgrade_id: UpgradeId, iteration):
    structures = bot.structures(struct_id).ready
    for structure in structures:
        if (bot.structures(struct_id).ready
            and bot.can_afford(upgrade_id) 
            and bot.already_pending_upgrade(upgrade_id) == 0
            and not structure.is_active):
            
            structure.research(upgrade_id)



async def research_warpgate(bot: BotAI, iteration):
    if (bot.structures(id.CYBERNETICSCORE).ready 
        and bot.can_afford(UpgradeId.WARPGATERESEARCH) 
        and bot.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0):
        
        cybercore = bot.structures(id.CYBERNETICSCORE).ready.idle
        cybercore.research(UpgradeId.WARPGATERESEARCH)
        
async def forge_upgrades(bot: BotAI, upgrade_id: UpgradeId, iteration):
    if (bot.structures(id.FORGE).ready 
        and bot.can_afford(upgrade_id) 
        and bot.already_pending_upgrade(upgrade_id) == 0):
        
        forge = bot.structures(id.FORGE).ready.idle
        forge.research(upgrade_id)
        
async def upgrade_weapons(bot: BotAI, iteration):
    await forge_upgrades(bot, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1)
    await forge_upgrades(bot, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2)
    await forge_upgrades(bot, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3)
        
async def upgrade_armor(bot: BotAI, iteration):
    await forge_upgrades(bot, UpgradeId.PROTOSSGROUNDARMORSLEVEL1)
    await forge_upgrades(bot, UpgradeId.PROTOSSGROUNDARMORSLEVEL2)
    await forge_upgrades(bot, UpgradeId.PROTOSSGROUNDARMORSLEVEL3)
    
async def upgrade_shields(bot: BotAI, iteration):
    await forge_upgrades(bot, UpgradeId.PROTOSSSHIELDSLEVEL1)
    await forge_upgrades(bot, UpgradeId.PROTOSSSHIELDSLEVEL2)
    await forge_upgrades(bot, UpgradeId.PROTOSSSHIELDSLEVEL3)