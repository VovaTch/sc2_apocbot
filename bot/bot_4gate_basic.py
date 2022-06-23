from email.mime import base
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from bot.routines import attack, base_upkeep, economy, army, upgrades, micro
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId

class Apoc4GateBot(BotAI):
    NAME: str = "ApocBot"
    """This bot's name"""

    RACE: Race = Race.Protoss
    """This bot's Starcraft 2 race.
    Options are:
        Race.Terran
        Race.Zerg
        Race.Protoss
        Race.Random
    """
    def __init__(self) -> None:
        BotAI.__init__(self)
        self.proxy_built = False

    async def on_start(self):
        """
        This code runs once at the start of the game
        Do things here before the game starts
        """
        print("Game started")

    async def on_step(self, iteration: int):
        """
        This code runs continually throughout the game
        Populate this function with whatever your bot should do!
        """
        await self.distribute_workers()
        await economy.default_econ_power(self, iteration)
        await base_upkeep.build_pylons_basic(self, iteration)
        
        # Production building
        if self.structures(UnitTypeId.CYBERNETICSCORE).amount == 0:
            await base_upkeep.build_gateway_basic(self, iteration, amount_limit=1)
        else:
            await base_upkeep.build_gateway_basic(self, iteration, amount_limit=4)
            await base_upkeep.build_proxy_pylon(self, iteration)
        await base_upkeep.build_cybercore_basic(self, iteration, amount_limit=1)
        if self.proxy_built:
            proxy_pylon = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])
        else:
            proxy_pylon = None
            
        if proxy_pylon == None:
            self.proxy_built = None
            
        # Warp if warpgates, build if otherwise. Basic stalker attack routine
        await upgrades.research_warpgate(self, iteration)
        if self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 1:
            pylon_position = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0]).position if\
                self.proxy_built else self.structures(UnitTypeId.PYLON).random.position
            await army.train_stalkers_basic(self, iteration, position=pylon_position.random_on_distance(4), warp=True)
        else:
            await army.train_stalkers_basic(self, iteration)
        
        if self.units(UnitTypeId.STALKER).ready.amount > 4:
            await attack.basic_stalker_attack(self, iteration, min_attack_count=4)
            await micro.basic_stalker_kiting(self, iteration)
        
        # Chronoboost logic; chrono gateways when they are ready, otherwise chrono nexus
        if self.structures(UnitTypeId.GATEWAY).ready:
            await base_upkeep.chronoboost(self, iteration, UnitTypeId.GATEWAY)
        else:
            await base_upkeep.chronoboost(self, iteration)

    async def on_end(self, result: Result):
        """
        This code runs once at the end of the game
        Do things here after the game ends
        """
        print("Game ended.")
