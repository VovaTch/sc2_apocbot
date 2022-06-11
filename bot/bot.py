from email.mime import base
from sc2.bot_ai import BotAI, Race
from sc2.data import Result
from bot.routines import base_upkeep, economy, army
from sc2.ids.unit_typeid import UnitTypeId

class ApocBot(BotAI):
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
        await base_upkeep.build_gateway_basic(self, iteration, amount_limit=3)
        await base_upkeep.build_cybercore_basic(self, iteration, amount_limit=1)
        
        # Warp if warpgates, build if otherwise
        await army.train_stalkers_basic(self, iteration)
        
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
