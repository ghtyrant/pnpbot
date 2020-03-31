import logging
import random
import pickle

from typing import Optional, Union, Any, Dict
from pathlib import Path

from discord.ext import commands
from discord.ext.commands import Context, command

from .systems.base import BaseSystem
from .character import Character, CharStatParseException, CharStat


description = """An example bot to showcase the discord.ext.commands extension
module.

There are a number of utility commands being showcased here."""

_logger = logging.getLogger("pnpbot")


class PnPBot(commands.Bot):
    def __init__(self, system: str, channel_id: int):
        super().__init__(
            command_prefix="!", description=description,
        )

        self.system = load_system(system)
        self.channel_id = channel_id
        self.characters: Dict[int, Character] = {}

        self.play_channel = None

        self.add_cog(PnPCog(self))

    async def on_ready(self):
        _logger.info(f"Logged in as {self.user.name} (#{self.user.id})")
        self.load_stats()

        self.play_channel = self.get_channel(self.channel_id)

        if not self.play_channel:
            _logger.error("Unable to locate play channel!")
            self.close()

        _logger.info("Loaded characters:")
        for user_id, stat in self.characters.items():
            _logger.info(str(stat))

    def load_stats(self):
        if not Path("stats.pickle").exists():
            self.characters = {}
            return

        with open("stats.pickle", "rb") as stream:
            self.characters = pickle.loads(stream.read())

    def save_stats(self):
        with open("stats.pickle", "wb") as stream:
            stream.write(pickle.dumps(self.characters))

    def add_character(self, user_id: int, name: str, *args) -> Character:
        self.characters[user_id] = Character(name, *args)
        self.save_stats()

        return self.characters[user_id]

    def delete_character(self, user_id: int):
        del self.characters[user_id]
        self.save_stats()

    def get_character(self, user_id: int) -> Optional[Character]:
        return self.characters.get(user_id, None)

    def has_character(self, user_id: int) -> bool:
        return user_id in self.characters


class PnPCog(commands.Cog):
    def __init__(self, bot: PnPBot):
        super().__init__()

        self.bot = bot

    @commands.command()
    @commands.has_any_role("DM")
    async def add(
        self, ctx: Context, player: str, character_name: str, *raw_attributes
    ):

        member = ctx.guild.get_member_named(player)

        if not member:
            await ctx.send(f"Spieler '{player}' nicht gefunden!")
            return

        if member.id in self.bot.characters:
            character = self.bot.get_character(member.id)
            assert character is not None

            await ctx.send(
                f"Der Spieler {member.name} hat schon einen Charakter ({character.name})!"
            )
            return

        try:
            attributes = self.bot.system.parse_attributes(raw_attributes)
        except CharStatParseException:
            await ctx.send(
                "Alle Attribute müssen im Format *wert*/*maximum* angegeben werden!"
            )
            return

        character = self.bot.add_character(member.id, character_name, attributes)

        await ctx.send(f"Spieler '{player}' ({member.id}) hinzugefügt!")

        msg = f"Charakter '{character_name}' hinzugefügt!\n"
        msg += str(character)
        assert self.bot.play_channel is not None
        await self.bot.play_channel.send(msg)

    @commands.command()
    @commands.has_any_role("DM")
    async def delete(self, ctx: Context, player: str):
        member = ctx.guild.get_member_named(player)

        if not member:
            await ctx.send(f"Spieler '{player}' nicht gefunden!")
            return

        await ctx.send(f"Spieler '{player}' ({member.id}) gelöscht!")
        self.bot.delete_character(member.id)

    @commands.command()
    async def set(self, ctx: Context, player: str, stat_name: str, value: str):
        member = ctx.guild.get_member_named(player)

        if not member or not self.bot.has_character(member.id):
            await ctx.send(f"Spieler '{player}' nicht gefunden!")
            return

        character = self.bot.get_character(member.id)

        if not character:
            return

        if not character.has_stat(stat_name):
            await ctx.send(
                f"Der Charakter {character.name} hat kein Attribut namens '{stat_name}'!"
            )
            return

        stat = character[stat_name]

        if "/" in value:
            new_stat = CharStat.from_str(stat_name, value)
            stat.update(new_stat)
        else:
            try:
                new_stat = int(value)
                stat.update(new_stat)
            except ValueError:
                await ctx.send(
                    "Der Wert muss entweder eine Zahl oder im Format x/y (z.B. 5/8) sein."
                )
                return

        assert self.bot.play_channel is not None
        await self.bot.play_channel.send(
            f":bust_in_silhouette: {character.name} hat jetzt :clipboard: **{stat} {stat.name}**."
        )

    @commands.command()
    async def stats(self, ctx: Context, player: Optional[str] = None):
        if player:
            member = ctx.guild.get_member_named(player)

            if not member:
                await ctx.send(f"Spieler '{player}' nicht gefunden!")
                return
        else:
            member = ctx.message.author

        character = self.bot.get_character(member.id)

        if not character:
            await ctx.send(f"Charakter nicht gefunden!")
            return

        await ctx.send(str(character))

    @commands.command()
    async def spend(self, ctx: Context, num: int, attribute: str):
        member = ctx.message.author
        character = self.bot.get_character(member.id)

        if not character:
            await ctx.send(f"Spieler nicht gefunden!")
            return

        stat = character[attribute]

        if stat.value < num:
            await ctx.send(f"Du hast nur noch {stat.value} {attribute.capitalize()}!")
            return

        stat.value -= num
        character[attribute] = stat.value
        self.bot.save_stats()
        await (
            ctx.send(
                f":bust_in_silhouette: {character.name} :clipboard: :arrow_lower_right: **{stat} {attribute.capitalize()}**"
            )
        )

    @commands.command()
    async def gain(self, ctx: Context, num: int, attribute: str):
        member = ctx.message.author
        character = self.bot.get_character(member.id)

        if not character:
            await ctx.send(f"Spieler nicht gefunden!")
            return

        stat = character[attribute]

        if stat.value + num > stat.maximum:
            stat.value = stat.maximum
        else:
            stat.value += num

        character[attribute] = stat.value
        self.bot.save_stats()
        await (
            ctx.send(
                f":bust_in_silhouette: {character.name} :clipboard: :arrow_upper_right: **{stat} {attribute.capitalize()}**"
            )
        )

    @commands.command()
    async def roll(self, ctx, *args):
        """Rolls a dice in NdN format."""
        await self.bot.system.handle_roll(*self.bot.system.parse_roll_args(args))

    @roll.error
    async def roll_error(self, ctx, error):
        print(error)
        await ctx.send(self.bot.system.RollHelp)


def load_system(name: str) -> BaseSystem:
    from importlib import import_module

    return getattr(import_module(f".systems.{name}", "pnpbot"), "System")()
