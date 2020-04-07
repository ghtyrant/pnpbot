import pytest
from typing import Optional
from discord.ext.commands import Context
from pnpbot.systems.base import (
    BaseSystem,
    Dice,
    RollArgumentAnnotationMissingException,
    MissingBaseArgumentsException,
)
from pnpbot.character import Character


class MyEmptySystem(BaseSystem):
    def handle_roll(self, ctx: Context, character: Optional[Character]):
        pass


class MyUnannotatedSystem(BaseSystem):
    def handle_roll(self, ctx: Context, character: Optional[Character], test):
        pass


class MyMissingSystem(BaseSystem):
    def handle_roll(self):
        pass


class MySystem(BaseSystem):
    Attributes = ["Stärke", "Intelligenz", "gEsChIcK"]

    def handle_roll(
        self,
        ctx: Context,
        character: Optional[Character],
        dice: Dice,
        int1: int,
        str1: str,
        float1: float,
        int2: int,
    ):
        pass


class TestSystem:
    def test_empty_roll_args(self):
        sys = MyEmptySystem()
        assert sys._roll_params == []

    def test_unannotated_roll_args(self):
        with pytest.raises(RollArgumentAnnotationMissingException):
            sys = MyUnannotatedSystem()

    def test_missing_roll_args(self):
        with pytest.raises(MissingBaseArgumentsException) as e:
            sys = MyMissingSystem()
            assert e.missing == ["ctx", "character"]

    def test_roll_args(self):
        sys = MySystem()
        assert sys._roll_params == [Dice, int, str, float, int]

    def test_parse_roll_args(self):
        sys = MySystem()
        parsed = sys.parse_roll_args(["1d6", "26", "Hello", "1.0", "123"])
        assert isinstance(parsed[0], Dice)
        assert parsed[1:] == [26, "Hello", 1.0, 123]

    def test_attribute_name(self):
        sys = MySystem()

        for attribute in sys.Attributes:
            assert sys.find_proper_name(attribute.lower()) == attribute

        assert sys.find_proper_name("unknown") == None
