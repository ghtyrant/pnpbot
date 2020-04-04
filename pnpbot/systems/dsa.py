import random
from typing import List, Tuple, Any
from discord.ext.commands import Context
from .base import BaseSystem, Dice

import logging

_logger = logging.getLogger("pnpbot")


class System(BaseSystem):
    Name = "DSA"
    Attributes = [
        "MU",
        "KL",
        "IN",
        "CH",
        "FF",
        "GE",
        "KO",
        "KK",
        "LeP",
        "Aus",
        "AsP",
        "KaP",
    ]
    RollArgs = [Dice, int, int, int, int]
    RollHelp = "Verwendung: !roll XdY BasisWert BasisWert BasisWert TalentWert  (z.B. `!roll 3d20 10 11 12 5`)"

    async def handle_roll(
        self, ctx: Context, dice: Dice, base1: int, base2: int, base3: int, talent: int
    ):
        if dice.number <= 0 or dice.sides <= 0:
            await ctx.send("Verwendung: !roll XdY Basis (e.g. `!roll 3d20 15`")
            return

        if dice.number > 50:
            await ctx.send("Du kannst maximal 50 Würfel gleichzeitig werfen.")
            return

        if dice.sides > 100:
            await ctx.send("Die Würfel können nicht mehr als 100 Seiten haben.")
            return

        base = [base1, base2, base3]
        # _logger.debug(f"Base1: '{base[0]}' Base2: '{base[1]}' Base3: '{base[2]}'")

        results = [random.randint(1, dice.sides) for r in range(dice.number)]

        # successes = sum([1 for r in results if r <= base[0]])
        # _logger.debug(f"successes: '{successes}'")
        TaW = talent
        successes = 0
        results_out = []

        _logger.debug(f"talent: '{TaW}'")
        i = -1
        for r in results:
            i += 1
            if r <= base[i]:
                successes += 1
                results_out.append(f"**{r}**")
            else:
                if r <= base[i] + TaW:
                    successes += 1
                    results_out.append(f"**{r}**")
                    TaW -= r - base[i]
                else:
                    results_out.append(str(r))
                    TaW -= r - base[i]
        # _logger.debug(f"talent: '{TaW}'")
        # _logger.debug(f"successes: '{successes}'")
        success = successes >= 3
        i = 0
        for r in results:
            if r == 1:
                i += 1
        if i >= 2:
            success = 3
        # _logger.debug(f"success: '{success}'")

        msg = ""
        KritErf = 0
        KritMisErf = 0

        if success:
            for r in results:
                if r == 1:
                    KritErf += 1
            if KritErf >= 2:
                msg = (
                    f":fire: :fire: :fire: **Kritischer Erfolg!** :fire: :fire: :fire:"
                )
            else:
                msg = f":green_circle: **Erfolg!**"
        else:
            for r in results:
                if r == 20:
                    KritMisErf += 1

            if KritMisErf >= 2:
                msg = f":zap: :zap: :zap: **Kritischer Misserfolg!** :zap: :zap: :zap:"
            else:
                msg = f":red_circle: **Misserfolg!**"

        dice_msg = ", ".join(results_out)
        plural = "e"
        if successes == 1:
            plural = ""

        await ctx.send(
            f">>> {ctx.author.mention}\n{msg}\n:game_die: {dice_msg} ({successes} Erfolg{plural}) {TaW}TaW"
        )
