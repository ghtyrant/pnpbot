import logging
import random
import pickle

from typing import Optional, Union, Any, Dict
from pathlib import Path

from discord.ext import commands
from discord.ext.commands import Context, command

from .systems.base import BaseSystem
from .character import (
    Character,
    AttributeParseException,
    Attribute,
    AnonymousAttributeException,
    MissingAttributesException,
    UnknownAttributeException,
    NotSpendableException,
    OverflowAttributeException,
    UnderflowAttributeException,
)


_logger = logging.getLogger("pnpbot")


class PnPBot(commands.Bot):
    def __init__(self, system: str, channel_id: int):
        super().__init__(
            command_prefix="!", description="",
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
            attributes = self.bot.system.parse_attributes(list(raw_attributes))
        except (AnonymousAttributeException, AttributeParseException) as e:
            error_stat = ""
            if e.stat_name:
                error_stat = f"Fehler im Attribut '{e.stat_name}'! "

            await ctx.send(
                f"{error_stat}Alle Attribute müssen im Format _name=wert/maximum_ (z.B. Stärke=5/12) angegeben werden!"
            )
            return
        except UnknownAttributeException as e:
            await ctx.send(f"Unbekanntes Attribut '{e.stat_name}'!")
            return
        except MissingAttributesException as e:
            await ctx.send(f"Folgende Attribute fehlen: {', '.join(e.missing)}!")
            return

        character = self.bot.add_character(member.id, character_name, attributes)

        await ctx.send(f"Charakter für '{player}' ({member.id}) hinzugefügt!")

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
    async def set(self, ctx: Context, player: str, value: str):
        member = ctx.guild.get_member_named(player)

        if not member:
            await ctx.send(f"Spieler '{player}' nicht gefunden!")
            return

        character = self.bot.get_character(member.id)
        if not character:
            await ctx.send(f"Spieler '{player}' hat keinen Charakter!")
            return

        try:
            new_stat = Attribute.from_str(value)
        except AttributeParseException:
            await ctx.send(
                "Der Wert muss entweder eine Zahl oder im Format x/y (z.B. 5/8) sein."
            )
            return

        if not new_stat.name:
            await ctx.send(
                "Verwendung: !set *player* *attributname*=*wert* (z.B.: !set MyPlayer intelligenz=5, !set MyPlayer hp=3/12"
            )
            return

        if not character.has_attribute(new_stat.name):
            await ctx.send(
                f"Der Charakter {character.name} hat kein Attribut namens '{new_stat.name}'!"
            )
            return
        stat = character.get_attribute(new_stat.name)

        stat.update(new_stat)

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
    async def spend(self, ctx: Context, amount: int, attribute_name: str):
        member = ctx.message.author
        character = self.bot.get_character(member.id)

        if not character:
            await ctx.send(f"Spieler nicht gefunden!")
            return

        attribute = character.get_attribute(attribute_name)

        if not attribute:
            await ctx.send(
                f"Der Charakter {character.name} hat kein Attribut namens '{attribute_name}'!"
            )
            return

        try:
            attribute.spend(amount)
        except NotSpendableException:
            await ctx.send(f"Das Attribut {attribute.name} kann man nicht ausgeben!")
            return
        except UnderflowAttributeException as e:
            await ctx.send(
                f"Du hast nur noch {e.current} {attribute.name} und kannst nicht unter {e.minium} sein!"
            )
            return

        self.bot.save_stats()
        await (
            ctx.send(
                f":bust_in_silhouette: {character.name} :clipboard: :arrow_lower_right: **{attribute} {attribute.name}**"
            )
        )

    @commands.command()
    async def gain(self, ctx: Context, amount: int, attribute_name: str):
        member = ctx.message.author
        character = self.bot.get_character(member.id)

        if not character:
            await ctx.send(f"Spieler nicht gefunden!")
            return

        attribute = character.get_attribute(attribute_name)

        if not attribute:
            await ctx.send(
                f"Der Charakter {character.name} hat kein Attribut namens '{attribute_name}'!"
            )
            return

        try:
            attribute.gain(amount)
        except NotSpendableException:
            await ctx.send(f"Das Attribut {attribute.name} kann man nicht ausgeben!")
            return
        except OverflowAttributeException as e:
            # For convenience, we simply set the attribute to its maximum instead of demanding a user action
            attribute.update(e.maximum)

        self.bot.save_stats()
        await (
            ctx.send(
                f":bust_in_silhouette: {character.name} :clipboard: :arrow_upper_right: **{attribute} {attribute.name}**"
            )
        )

    @commands.command()
    async def roll(self, ctx, *args):
        """Rolls a dice in NdN format."""
        member = ctx.message.author
        character = self.bot.get_character(member.id)

        await self.bot.system.handle_roll(
            ctx, character, **self.bot.system.parse_roll_args(args)
        )

    @roll.error
    async def roll_error(self, ctx, error):
        await ctx.send(self.bot.system.RollHelp)


def load_system(name: str) -> BaseSystem:
    from importlib import import_module

    return getattr(import_module(f".systems.{name}", "pnpbot"), "System")()
