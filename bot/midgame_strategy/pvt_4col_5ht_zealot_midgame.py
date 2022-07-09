from distutils.command.build import build
from typing import Dict, List
import asyncio

import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id
from bot.routines.economy import distribute_workers_with_exception, default_econ_power
from bot.routines.base_upkeep import build_building, build_pylons_basic
from bot.routines.army import train_gateway_unit_basic, train_nongateway_unit_basic
from bot.routines.upgrades import research_upgrade
from bot.routines.attack import adept_attack_logic_basic, basic_base_defense_logic
from sc2.ids.upgrade_id import UpgradeId


class MidGameStrategy:
    
    def __init__(self) -> None:
        
        self.scouting_probe = None
        self.templar_tech_flag = False
        self.shield_upgrade_flag = False
    
    async def execute(self, bot: BotAI, iteration):
        
        await distribute_workers_with_exception(bot, iteration, self.scouting_probe) # Force mining
        await build_pylons_basic(bot, iteration)
        await build_building(bot, id.ASSIMILATOR, iteration, None, amount_limit=bot.townhalls.amount * 2)
            
        # Basic midgame logics for macro
        await self._upgrade_logic(bot, iteration)
        await self._chrono_logic(bot, iteration)
        await self._tech_logic(bot, iteration)
        await self._maxed_logic(bot, iteration)
        
        # Basic midgame logic for army
        await basic_base_defense_logic(bot, iteration)
        await self._build_army(bot, iteration)
    
        
        # Limit to 75 probes
        if bot.units(id.PROBE).amount < 75:
            await default_econ_power(bot, iteration)
            
    async def _upgrade_logic(self, bot: BotAI, iteration):
        '''
        Basic upgrade logic. Upgrade weapons and armor first, then upgrade shields. 
        Also research individual unit upgrades for the units in the mix.
        '''
   
        if (bot.already_pending_upgrade(UpgradeId.PROTOSSGROUNDARMORSLEVEL3) == 1 or 
            bot.already_pending_upgrade(UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3) == 1):
            self.shield_upgrade_flag = True
        if not self.shield_upgrade_flag:
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDARMORSLEVEL1, iteration)
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDARMORSLEVEL2, iteration)
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDARMORSLEVEL3, iteration)
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, iteration)
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL2, iteration)
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL3, iteration)
        else:
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSSHIELDSLEVEL1, iteration) 
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSSHIELDSLEVEL2, iteration) 
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSSHIELDSLEVEL3, iteration) 
        await research_upgrade(bot, id.TWILIGHTCOUNCIL, UpgradeId.CHARGE, iteration)
        await research_upgrade(bot, id.TWILIGHTCOUNCIL, UpgradeId.BLINKTECH, iteration)
        await research_upgrade(bot, id.TEMPLARARCHIVE, UpgradeId.PSISTORMTECH, iteration)
        await research_upgrade(bot, id.DARKSHRINE, UpgradeId.DARKTEMPLARBLINKUPGRADE, iteration)
        await research_upgrade(bot, id.ROBOTICSBAY, UpgradeId.GRAVITICDRIVE, iteration)
        await research_upgrade(bot, id.ROBOTICSBAY, UpgradeId.OBSERVERGRAVITICBOOSTER, iteration)
            
    async def _chrono_logic(self, bot: BotAI, iteration):
        
        forge = bot.structures(id.FORGE).ready.random
        if forge.is_active:
            await self._chrono_building(bot, forge, iteration)
        robo = bot.structures(id.ROBOTICSFACILITY).ready.random
        if robo.is_active:
            await self._chrono_building(bot, robo, iteration)
            
    async def _tech_logic(self, bot: BotAI, iteration):
        
        # Once supply is over 135, activate the templar tech flag, build Templar Archives and Dark Shrine
        if bot.supply_used >= 135:
            self.templar_tech_flag = True
        if self.templar_tech_flag:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.TEMPLARARCHIVE, iteration, placement, amount_limit=1)
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.TEMPLARARCHIVE, iteration, placement, amount_limit=1)
        
    async def _maxed_logic(self, bot: BotAI, iteration):
        
        # Production powerup when we are maxed
        if bot.supply_used >= 195:
            
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.GATEWAY, iteration, placement, amount_limit=25)
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.ROBOTICSFACILITY, iteration, placement, amount_limit=3)
        
    async def _chrono_building(self, bot: BotAI, target, iteration, energy_min=0):
        
        nexus = bot.townhalls.ready.random
        if nexus.energy > 50 + energy_min:
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)
            
    async def _build_army(self, bot: BotAI, iteration):
        
        ht_amount = 5
        col_amount = 4
        ration_dict = {'zealot': 1,
                       'stalker': 0.5,
                       'immortal': 0.1} # TODO: Remove this hardcoding?
        unit_dict = {'zealot': id.ZEALOT,
                     'stalker': id.STALKER,
                     'immortal': id.IMMORTAL}
        
        # Fixed amount units
        if bot.units(id.HIGHTEMPLAR).amount < ht_amount:
            await train_gateway_unit_basic(bot, id.HIGHTEMPLAR)
        if bot.units(id.COLOSSUS).amount < col_amount:
            await train_nongateway_unit_basic(bot, id.COLOSSUS)
        
        # Ratio units
        for unit in ration_dict:
            
            if unit == 'zealot':
                continue
            
            if (bot.units(unit_dict['zealot']).amount / (bot.units(unit_dict[unit]).amount + 1e-5) >=
                ration_dict['zealot'] / ration_dict[unit]):
                
                if unit in ['stalker', 'sentry', 'adept', 'ht', 'dt']:
                    await train_gateway_unit_basic(bot, unit_dict[unit])
                else:
                    await train_nongateway_unit_basic(bot, unit_dict[unit])
                    
            else:
                await train_gateway_unit_basic(bot, id.ZEALOT)
                
        # TODO: Archon logic
        
            
        
        
        
        
        
        