import abc
import logging
from inspect import signature, Parameter
from typing import Tuple, List, Any, Optional

from discord.ext import commands
from discord.ext.commands import Context

from pnpbot.character import (
    Character,
    Attribute,
    AnonymousAttributeException,
    UnknownAttributeException,
    MissingAttributesException,
)


_logger = logging.getLogger("pnpbot")


class RollArgumentAnnotationMissingException(Exception):
    def __init__(self, param: str):
        super().__init__()
        self.param = param


class MissingBaseArgumentsException(Exception):
    def __init__(self, params: List[str]):
        super().__init__()
        self.params = params


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
    RollHelp = ""

    def __init__(self):
        # Automatically derive !roll parameter types from handle_roll's signature
        self._roll_params: List[type] = []
        child_signature = signature(self.handle_roll)
        base_signature = signature(__class__.handle_roll)

        # Remove 'self' and 'kwargs' from the parent implementation's parameters
        base_parameters = [
            p for p in base_signature.parameters.keys() if p not in ("self", "kwargs")
        ]
        for _, param in child_signature.parameters.items():
            if param.name in base_parameters or param.name == "self":
                base_parameters.remove(param.name)
                continue

            # Parameters have to be annotated, otherwise we can't determine their type
            if param.annotation == Parameter.empty:
                raise RollArgumentAnnotationMissingException(param)

            self._roll_params.append(param.annotation)

        # If not all of the parent's parameters also exist in the child, error out
        if base_parameters:
            raise MissingBaseArgumentsException(base_parameters)

    def parse_roll_args(self, args: List[Any]) -> List[Any]:
        final_args = []
        args = list(args)
        for arg_type in self._roll_params:
            arg = args.pop(0)
            _logger.debug(f"Converting argument '{arg}' to type {arg_type}")
            final_args.append(arg_type(arg))

        return final_args

    def find_proper_name(self, name: str) -> Optional[str]:
        for attribute_name in self.Attributes:
            if attribute_name.lower() == name.lower():
                return attribute_name

        return None

    def parse_attributes(self, attributes: List[str]) -> List[Attribute]:
        result = []
        defined = []
        for attribute in attributes:
            stat = Attribute.from_str(attribute)
            defined.append(stat.name.lower())

            if not stat.name:
                raise AnonymousAttributeException()

            proper_name = self.find_proper_name(stat.name)
            if not proper_name:
                raise UnknownAttributeException(stat.name)

            stat.name = proper_name

            result.append(stat)

        undefined = (attr for attr in self.Attributes if attr.lower() not in defined)

        if undefined:
            raise MissingAttributesException(undefined)

        return result

    @abc.abstractmethod
    def handle_roll(self, ctx: Context, character: Optional[Character], **kwargs: Any):
        raise NotImplementedError()
