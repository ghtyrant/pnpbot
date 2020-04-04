import random
from typing import List, Tuple, Any, Optional
from discord.ext.commands import Context
from .base import BaseSystem, Dice
from pnpbot.character import Attribute, Character


class System(BaseSystem):
    Name = "HexDec"
    Attributes = [
        Attribute(name="Vita", limited=True, spendable=True),
        Attribute(name="AP", limited=True, spendable=True),
        Attribute(name="Körper", limited=True, spendable=True),
        Attribute(name="Geist", limited=True, spendable=True),
        Attribute(name="Sozial", limited=True, spendable=True),
    ]
    RollHelp = "Verwendung: !roll XdY Basis (z.B. `!roll 3d20 15`)"

    async def handle_roll(
        self, ctx: Context, character: Optional[Character], dice: Dice, base: int
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

        results = [random.randint(1, dice.sides) for r in range(dice.number)]
        successes = sum([1 for r in results if r > base])
        success = successes > 0
        critical = any([True for r in results if r == 20 or r == 1 and not success])

        results_out = []
        for r in results:
            if r > base:
                results_out.append(f"**{r}**")
            else:
                results_out.append(str(r))

        msg = ""
        if success:
            if critical:
                msg = (
                    f":fire: :fire: :fire: **Kritischer Erfolg!** :fire: :fire: :fire:"
                )
            else:
                msg = f":green_circle: **Erfolg!**"
        else:
            if critical:
                msg = f":zap: :zap: :zap: **Kritischer Misserfolg!** :zap: :zap: :zap:"
            else:
                msg = f":red_circle: **Misserfolg!**"

        dice_msg = ", ".join(results_out)
        plural = "e"
        if successes == 1:
            plural = ""

        await ctx.send(
            f">>> {ctx.author.mention}\n{msg}\n:game_die: {dice_msg} ({successes} Erfolg{plural})"
        )
