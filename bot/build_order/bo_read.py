from typing import Dict, List
import asyncio

import yaml

from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId as id
from bot.routines.economy import default_econ_power
from sc2.ids.upgrade_id import UpgradeId
from bot.routines.economy import distribute_workers_with_exception
from bot.routines.base_upkeep import build_building
from sc2.player import Bot

STRUCTURES = {'pylon', 'gate', 'core', 'nexus', 'gas'}
UNITS = {'probe', 'stalker', 'zealot'}
UPGRADES = {'warpgate'}

TRANSLATOR = {'pylon': id.PYLON, # Buildings 
              'gate': id.GATEWAY, 
              'core': id.CYBERNETICSCORE, 
              'nexus': id.NEXUS, 
              'gas': id.ASSIMILATOR,
              'robo': id.ROBOTICSFACILITY,
              'forge': id.FORGE,
              'bay': id.ROBOTICSBAY,
              
              'probe': id.PROBE, # Units
              'stalker': id.STALKER, 
              'zealot': id.ZEALOT,
              'sentry': id.SENTRY,
              'adept': id.ADEPT,
              'dt': id.DARKTEMPLAR,
              'ht': id.HIGHTEMPLAR,
              'prism': id.WARPPRISM,
              'immortal': id.IMMORTAL,
              'colossus': id.COLOSSUS,
              'disruptor': id.DISRUPTOR,
              'phoenix': id.PHOENIX,
              'voidray': id.VOIDRAY,
              'oracle': id.ORACLE,
              'carrier': id.CARRIER,
              'tempest': id.TEMPEST,
              'archon': id.ARCHON,
              
              'warpgate': UpgradeId.WARPGATERESEARCH} # Upgrades

class BuildOrder:
    """
    A class that stores and executes a build order.
    """
    
    def __init__(self, 
                 bo_file_path: str,
                 chosen_bo: str) -> None:
        
        with open(bo_file_path, 'r') as f:
            raw_dict = yaml.safe_load(f)
            
        self.bo_dict: Dict[int, str] = raw_dict[chosen_bo]
            
        self.current_tasks = []
        self.chrono_target = None
        self.parse_supply = 0
        self.proxy_probe = None # This will assume a single proxy probe for now.
        self.required_action_counts = {}
        self.complete = False
            
    async def execute(self, bot: BotAI, iteration):
        
        # distribute the workers with excluding a proxy probe
        await distribute_workers_with_exception(bot, iteration, exception_probe=self.proxy_probe)
        
        # Designate a chronoboost nexus
        chrono_nexus = bot.structures(id.NEXUS).ready.random
        
        # Build probes by default
        await default_econ_power(bot, iteration)
        if bot.supply_used == 16:
            self.chrono_target = bot.structures(id.NEXUS).ready.first
        elif bot.supply_used == 17:
            self.chrono_target = None
        
        # Apply chronoboost
        if self.chrono_target is not None and chrono_nexus.energy >= 50:
            chrono_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, self.chrono_target)
                 
        current_supply = bot.supply_used
        self._count_required_actions(current_supply)
        
        for sup_key, tasks_together in self.bo_dict.items():
            
            if sup_key > current_supply:
                return
            
            tasks = tasks_together.split()
            for task in tasks:
                await self._perform_action(bot, task, iteration)
                  
    async def _perform_action(self, bot: BotAI, task, iteration):
        
        task_split = task.split('_')
        
        # Construct structure
        if task_split[0] in STRUCTURES:
            await self._perform_construction_action(bot, task_split, iteration)
            
        elif task_split[0] in UNITS:
            await self._perform_training_action(bot, task_split, iteration)
            
        elif task_split[0] in UPGRADES:
            await self._perform_upgrade_action(bot, task_split, iteration)
            
        elif task_split[0] == 'chrono':
            self.chrono_target = bot.structures(TRANSLATOR[task_split[1]]).random
            
            
    def _count_required_actions(self, current_supply):
        """
        Performs a counting of all the required buildings from a build order given a supply count.
        """
        
        self.required_action_counts = {}
        for sup_key, tasks_together in self.bo_dict.items():
            
            # Filter out premature build order commands
            if sup_key > current_supply:
                return
            
            tasks = tasks_together.split()
            
            for task in tasks:
                
                task_split = task.split('_')
                
                if task_split[0] != 'chrono' and task_split[0] not in self.required_action_counts:
                    self.required_action_counts[task_split[0]] = 1
                elif task_split[0] != 'chrono' and task_split[0] in self.required_action_counts:
                    self.required_action_counts[task_split[0]] += 1
                    
    async def _perform_construction_action(self, bot: BotAI, task_split: List[str], iteration):
        """
        Perform construction with a proxy posibility. TODO: Maybe later there will be a neural network that decides the location
        """
                 
        if 'proxy' in task_split and 'pylon' in task_split:
            build_location = bot.game_info.map_center.towards(bot.enemy_start_locations[0], 4)
            self.proxy_probe = bot.units(id.PROBE).closest_to(build_location)
            probe = self.proxy_probe
        elif 'proxy' in task_split:
            proxy_pylon = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0])
            # if not proxy_pylon.is_ready:
            #     return
            build_location = proxy_pylon.position.random_on_distance(4)
            self.proxy_probe = bot.units(id.PROBE).closest_to(build_location)
            probe = self.proxy_probe
        elif 'pylon' in task_split:
            nexus = bot.townhalls.ready.random
            build_location = nexus.position.towards(bot.enemy_start_locations[0], 7)
            probe = None
        else:
            build_location = bot.structures(id.PYLON).ready.random.position.random_on_distance(4)
            probe = None
            
        await build_building(bot, TRANSLATOR[task_split[0]], iteration, build_location, 
                             probe, amount_limit=self.required_action_counts[task_split[0]])
            
        
    async def _perform_training_action(self, bot: BotAI, task_split: List[str], iteration):
        """
        Creates a unit. If it's a gateway unit and warpgate is available, warps the unit near the proxy pylon
        """
        # Returns if the number of units reaches the required counts
        if (self.required_action_counts[task_split[0]] <= 
            bot.units(TRANSLATOR[task_split[0]]).amount + 
            bot.already_pending(TRANSLATOR[task_split[0]])):
            return
        
        if task_split[0] == 'probe' and bot.structures(id.NEXUS).ready > 0:
            nexus = bot.structures(id.NEXUS).ready.random
            nexus.train(id.PROBE)
            
        elif (task_split[0] in ['zealot', 'stalker', 'ht', 'dt', 'adept', 'sentry'] and 
                bot.structures(id.GATEWAY).ready.amount + bot.structures(id.WARPGATE).ready.amount > 0):
            
            unit_type = TRANSLATOR[task_split[0]]

            # Gateway training
            if bot.can_afford(unit_type) and bot.supply_left >= 2:
                if (task_split[0] == 'zealot' or 
                    (task_split[0] in ['stalker', 'adept', 'sentry'] and bot.structures(id.CYBERNETICSCORE).ready.amount > 0) or
                    (task_split[0] == 'ht' and bot.structures(id.TEMPLARARCHIVE).ready.amount > 0) or
                    (task_split[0] == 'dt' and bot.structures(id.DARKSHRINE).ready.amount > 0)):
                    
                    if bot.structures(id.WARPGATE).ready.amount > 0:
                        warpgate = bot.structures(id.WARPGATE).ready.random
                        warp_location = bot.structures(id.PYLON).closest_to(bot.enemy_start_locations[0]).position.random_on_distance(4)
                        warpgate.warp_in(unit_type, warp_location)
                    else:
                        gateway = bot.structures(id.GATEWAY).ready.random
                        gateway.train(unit_type)
                        
    async def _perform_upgrade_action(self, bot: BotAI, task_split: List[str], iteration):
        
        upgrade_type = TRANSLATOR[task_split[0]]
        if task_split[0] in ['warpgate']:
            if (bot.structures(id.CYBERNETICSCORE).ready.amount > 0 
                and bot.already_pending_upgrade(upgrade_type) != 1 
                and bot.can_afford(upgrade_type)):
                
                upgrader = bot.structures(id.CYBERNETICSCORE).ready.random
            else:
                return
                
        upgrader.research(upgrade_type)
                

                 
                 
                 
             