import pytest
from pnpbot.character import Attribute


class TestAttributes:
    @pytest.mark.parametrize("name, input", [("", "5"), ("strength", "strength=5")])
    def test_single_value(self, name: str, input: str):
        attr = Attribute.from_str(input)

        assert attr.name == name
        assert attr.limited == False
        assert attr.value == 5
        assert attr.minimum == 0
        assert attr.maximum == 0

    @pytest.mark.parametrize(
        "name, input", [("", "5/10"), ("strength", "strength=5/10")]
    )
    def test_current_maximum(self, name: str, input: str):
        attr = Attribute.from_str(input)

        assert attr.name == name
        assert attr.limited == True
        assert attr.value == 5
        assert attr.minimum == 0
        assert attr.maximum == 10

    @pytest.mark.parametrize(
        "name, input", [("", "2/5/10"), ("strength", "strength=2/5/10")]
    )
    def test_minimum_current_maximum(self, name: str, input: str):
        attr = Attribute.from_str(input)

        assert attr.name == name
        assert attr.limited == True
        assert attr.value == 5
        assert attr.minimum == 2
        assert attr.maximum == 10
