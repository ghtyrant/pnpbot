import abc
import logging
from typing import Tuple, List, Any

from discord.ext import commands

from pnpbot.character import CharStat


_logger = logging.getLogger("pnpbot")


class Dice:
    def __init__(self, dice: str):
        try:
            self.number, self.sides = map(int, dice.lower().split("d"))
        except Exception:
            raise ValueError(f"{dice} is not a valid Dice value!")

    def __str__(self) -> str:
        return f"{self.number}d{self.sides}"


class BaseSystem(abc.ABC):
    Name = "Base"
    Attributes: List[str] = []
    RollArgs: List[type] = []
    RollHelp = ""

    def __init__(self):
        pass

    def parse_roll_args(self, args: List[Any]) -> List[Any]:
        final_args = []
        args = list(args)
        for arg_type in self.RollArgs:
            arg = args.pop(0)
            _logger.debug(f"Converting argument '{arg}' to type {arg_type}")
            final_args.append(arg_type(arg))

        print(final_args)
        return final_args

    def parse_attributes(self, attributes: List[str]) -> List[CharStat]:
        result = []
        attributes = list(attributes)
        for name in self.Attributes:
            result.append(CharStat.from_str(name, attributes.pop(0)))
        return result

    @abc.abstractmethod
    def handle_roll(self, args: Any):
        raise NotImplementedError()
