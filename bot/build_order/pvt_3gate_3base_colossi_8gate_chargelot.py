from distutils.command.build import build
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
from bot.routines.attack import adept_attack_logic_basic, basic_base_defense_logic
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
            
            if bot.already_pending(id.COLOSSUS):
                chrono_target = bot.structures(id.ROBOTICSFACILITY).ready.random
                await self._chrono_building(bot, chrono_target, iteration)
            
            chrono_target = bot.townhalls.ready.random
            await self._chrono_building(bot, chrono_target, iteration)
                
        # 27 stalker
        if current_supply >= 27 and bot.units(id.STALKER).amount + bot.already_pending(id.STALKER) < 1:
            await train_gateway_unit_basic(bot, id.STALKER)
                
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
        if current_supply >= 38:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.GATEWAY, iteration, placement, amount_limit=3)
            
        # 39 stalker
        if current_supply >= 39 and bot.units(id.STALKER).amount + bot.already_pending(id.STALKER) < 2:
            await train_gateway_unit_basic(bot, id.STALKER)
                
        # 43 observer
        if current_supply >= 43 and bot.units(id.OBSERVER).amount + bot.already_pending(id.OBSERVER) < 1:
            await train_nongateway_unit_basic(bot, id.OBSERVER)
            
        
        # 46 expand
        if current_supply >= 46:
            
            # Send a probe to the expansion
            if bot.townhalls.amount < 3:
                await bot.expand_now()
                if bot.minerals > 300 and self.scouting_probe is None:
                    self.scouting_probe = bot.units(id.PROBE).closest_to(bot.enemy_start_locations[0])
                    self.scouting_probe.move(bot.enemy_start_locations[0])
                    
        # 47 3rd gas
        if current_supply >= 47:
            await build_building(bot, id.ASSIMILATOR, iteration, placement, amount_limit=3)
            
        # 48 pylon + robobay
        if current_supply >= 48:
            await build_building(bot, id.ROBOTICSBAY, iteration, placement, amount_limit=1)
            placement = bot.townhalls.closest_to(bot.enemy_start_locations[0]).\
                position.towards(bot.enemy_start_locations[0], distance=4)
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=4)
            
        # 50 x3 stalkers
        if current_supply >= 50 and bot.units(id.STALKER).amount < 5:
            await train_gateway_unit_basic(bot, id.STALKER)
            
        # 56 pylon
        if current_supply >= 56:
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=5)
            
        # 60 x3 stalkers
        if current_supply >= 50 and bot.units(id.STALKER).amount < 8:
            await train_gateway_unit_basic(bot, id.STALKER)
            
        # 66 colossus
        if current_supply >= 66 and bot.units(id.COLOSSUS).amount < 1:
            await train_nongateway_unit_basic(bot, id.COLOSSUS)
            
        # 75 shield battery
        if current_supply >= 75:
            placement = bot.townhalls.closest_to(bot.enemy_start_locations[0]).\
                position.towards(bot.enemy_start_locations[0], distance=4)
            await build_building(bot, id.SHIELDBATTERY, iteration, placement, amount_limit=1)
            
        # 77 shield battery
        if current_supply >= 75:
            placement = bot.townhalls.closest_to(bot.enemy_start_locations[0]).\
                position.towards(bot.enemy_start_locations[0], distance=4)
            await build_building(bot, id.SHIELDBATTERY, iteration, placement, amount_limit=2)
            
                            
        # 80 4th gas + extended termal lance + 2 pylons
        if current_supply >= 80:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await build_building(bot, id.ASSIMILATOR, iteration, placement, amount_limit=4)
            await research_upgrade(bot, id.ROBOTICSBAY, UpgradeId.EXTENDEDTHERMALLANCE, iteration)
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=7)
        
        # 83 colossus    
        if current_supply >= 83 and bot.units(id.COLOSSUS).amount < 2:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            await train_nongateway_unit_basic(bot, id.COLOSSUS)
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=9)
            
        # 92 Zealots x3
        if current_supply >= 92 and bot.units(id.ZEALOT).amount < 3:
            await train_gateway_unit_basic(bot, id.ZEALOT)
            
        # 98 upgrades
        if current_supply >= 98:
            placement = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            self.econ_stop_flag = True
            await build_building(bot, id.FORGE, iteration, placement, amount_limit=2)
            await build_building(bot, id.TWILIGHTCOUNCIL, iteration, placement, amount_limit=1)
            await build_building(bot, id.GATEWAY, iteration, placement, amount_limit=8)
            await build_building(bot, id.PYLON, iteration, placement, amount_limit=12)
            
        # Forge upgrades
        if bot.structures(id.FORGE).ready.amount == 2:
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDWEAPONSLEVEL1, iteration)
            await research_upgrade(bot, id.FORGE, UpgradeId.PROTOSSGROUNDARMORSLEVEL1, iteration)
            
        # Council charge
        if bot.structures(id.TWILIGHTCOUNCIL).ready.amount == 1:
            await research_upgrade(bot, id.TWILIGHTCOUNCIL, UpgradeId.CHARGE, iteration)

            
        # Build another colossus
        if current_supply >= 98 and bot.units(id.COLOSSUS).amount < 3:
            await train_nongateway_unit_basic(bot, id.COLOSSUS)
            
        # Build a Warp Prism
        if current_supply >= 104 and bot.units(id.WARPPRISM).amount < 1:
            await train_nongateway_unit_basic(bot, id.WARPPRISM)
            if not self.build_order_finished:
                await bot.chat_send(f'Finished the build order at {current_supply} supply ^_^')
            self.build_order_finished = True
        
        '''
        BUILD ORDER FINISHES HERE <========================================
        '''
        if current_supply >= 35:
            await basic_base_defense_logic(bot, iteration)
            
        # Economy whether to build probes or not
        if not self.econ_stop_flag:
            await default_econ_power(bot, iteration)
            
    
    async def scounting_logic(self, bot: BotAI, iteration):
        if self.scouting_probe is not None:
            self.scouting_probe.move(bot.enemy_start_locations[0].random_on_distance(7))
        if bot.units(id.OBSERVER).ready.amount > 0:
            for obs in bot.units(id.OBSERVER):
                send_location = bot.enemy_start_locations[0].towards(bot.game_info.map_center, distance=5)
                obs.move(send_location)
        
    async def _chrono_building(self, bot: BotAI, target, iteration, energy_min=0):
        
        nexus = bot.townhalls.ready.random
        if nexus.energy > 50 + energy_min:
            nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, target)
            