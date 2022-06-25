from typing import Dict, List
import asyncio

import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id
from bot.routines.economy import distribute_workers_with_exception, default_econ_power
from bot.routines.base_upkeep import build_building
from bot.routines.army import train_gateway_unit_basic, train_nongateway_unit_basic
from bot.routines.upgrades import research_upgrade
from bot.routines.attack import adept_attack_logic_basic
from sc2.ids.upgrade_id import UpgradeId


class BuildOrder:
    
    def __init__(self) -> None:

        self.scouting_probe = None
        self.econ_stop_flag = False
        self.build_order_finished = False
        self.adept_built_flag = False
        self.stalker_built_flag = False
        self.observer_built_flag = False
    
    async def execute(self, bot: BotAI, iteration):
        
        # Cuts out if the build order considered finished
        if self.build_order_finished:
            return
        
        # Distribute workers to work and compute current supply
        await distribute_workers_with_exception(bot, iteration, self.scouting_probe)
        current_supply = bot.supply_used
        self.econ_stop_flag = False
        
        '''
        BUILD ORDER STARTS HERE =======================>
        '''
        # 14 pylon
        if current_supply >= 14:
            nexus = bot.townhalls.ready.random
            placement = nexus.position.towards_with_random_angle(p=bot.enemy_start_locations[0], 
                                                                 distance=4)# TODO: To be changed once the neural network is active
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=1)
            
        # 16 gate
        if current_supply >= 16:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.GATEWAY, iteration, placement, amount_limit=1)
            
        # 17 nexus, gas, send scouting probe to scout
        if current_supply >= 17:
            self.econ_stop_flag = True
            
            # Send a probe to the expansion
            if bot.townhalls.amount < 2:
                await bot.expand_now()
                if bot.minerals > 300 and self.scouting_probe is None:
                    self.scouting_probe = bot.units(id.PROBE).closest_to(bot.enemy_start_locations[0])
                    self.scouting_probe.move(bot.enemy_start_locations[0])
                
            if bot.already_pending(id.NEXUS) == 1:
                await build_building(bot, id.ASSIMILATOR, iteration, placement, amount_limit=1)
                
            if bot.already_pending(id.NEXUS) == 1 and bot.already_pending(id.ASSIMILATOR) == 1:
                self.econ_stop_flag = False
                self.scouting_probe.move(bot.enemy_start_locations[0])
                
        # Scounting logic. TODO: Expand upon it
        if current_supply >= 22:
            if self.scouting_probe is not None:
                await self.scounting_logic(bot, iteration)
            else:
                self.scouting_probe = bot.units(id.PROBE).closest_to(bot.enemy_start_locations[0])
            
        # 18 resume production + cybercore
        if current_supply >= 18:
            self.econ_stop_flag = False
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.CYBERNETICSCORE, iteration, placement, amount_limit=1)
            if current_supply in [18, 19]: # Giving a room to breath to prevent mistakes
                chrono_target = bot.townhalls.ready.random
                await self._chrono_building(bot, chrono_target, iteration, energy_min=50)
            
        # 21 pylon
        if current_supply >= 21:
            nexus = bot.townhalls.ready.random
            placement = nexus.position.towards_with_random_angle(p=bot.enemy_start_locations[0], 
                                                                 distance=7).random_on_distance(4)# TODO: To be changed once the neural network is active
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=2)
            
        # 22 gas + adept + warpgate
        if current_supply >= 22:
            await build_building(bot, id.ASSIMILATOR, iteration, placement, amount_limit=2)
            await research_upgrade(bot, id.CYBERNETICSCORE, UpgradeId.WARPGATERESEARCH, iteration)
            if bot.already_pending(id.ADEPT) and not self.adept_built_flag:
                chrono_target = bot.structures(id.GATEWAY).ready.first
                await self._chrono_building(bot, chrono_target, iteration)
                self.adept_built_flag = True
                
            if bot.units(id.ADEPT).amount > 0:
                await adept_attack_logic_basic(bot, iteration)
            elif not self.adept_built_flag:
                await train_gateway_unit_basic(bot, id.ADEPT)
                
        # Chrono economy
        if self.adept_built_flag:
            chrono_target = bot.townhalls.ready.random
            await self._chrono_building(bot, chrono_target, iteration)
                
        # 27 stalker
        if current_supply >= 27:
            
            if not self.stalker_built_flag:
                await train_gateway_unit_basic(bot, id.STALKER)
            elif bot.already_pending(id.STALKER):
                self.stalker_built_flag = True
                
        # 33 robo
        if current_supply >= 32:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.ROBOTICSFACILITY, iteration, placement, amount_limit=1)
            
        # 35 pylon
        if current_supply >= 35:
            nexus = bot.townhalls.ready.random
            placement = nexus.position.towards_with_random_angle(p=bot.enemy_start_locations[0], 
                                                                 distance=7).random_on_distance(4)# TODO: To be changed once the neural network is active
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=3)
            
        # 38 x2 gateways
        if current_supply >= 32:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.ROBOTICSFACILITY, iteration, placement, amount_limit=3)
            
        # 39 stalker
        if current_supply == 39:
            self.stalker_built_flag = False
        if current_supply >= 39:
        
            if not self.stalker_built_flag:
                await train_gateway_unit_basic(bot, id.STALKER)
            elif bot.already_pending(id.STALKER):
                self.stalker_built_flag = True
                
        # 43 observer
        if current_supply >= 43:
        
            if not self.observer_built_flag:
                await train_nongateway_unit_basic(bot, id.OBSERVER)
            elif bot.already_pending(id.OBSERVER):
                self.stalker_built_flag = True
            
        '''
        BUILD ORDER FINISHES HERE <========================================
        '''
            
        # Economy whether to build probes or not
        if not self.econ_stop_flag:
            await default_econ_power(bot, iteration)
            
    
    async def scounting_logic(self, bot: BotAI, iteration):
        self.scouting_probe.move(bot.enemy_start_locations[0].random_on_distance(7))
        
    async def _chrono_building(self, bot: BotAI, target, iteration, energy_min=0):
        
        nexus = bot.townhalls.ready.random
        if nexus.energy > 50 + energy_min:
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)
            