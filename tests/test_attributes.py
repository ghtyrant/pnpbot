import pytest
from pnpbot.character import (
    Attribute,
    AttributeParseException,
    NotSpendableException,
    UnderflowAttributeException,
    OverflowAttributeException,
)


class TestAttributes:
    @pytest.mark.parametrize("input", ["a", "a/b", "a/b/c"])
    def test_invalid_value(self, input: str):
        with pytest.raises(AttributeParseException):
            attr = Attribute.from_str(input)

    def test_invalid_minimum(self):
        with pytest.raises(AttributeParseException):
            attr = Attribute.from_str("10/0/5")

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

    def test_invalid_attribute_max(self):
        with pytest.raises(OverflowAttributeException):
            Attribute(value=5, minimum=0, maximum=2, limited=True, spendable=True)

    def test_invalid_attribute_min(self):
        with pytest.raises(UnderflowAttributeException):
            Attribute(value=1, minimum=2, maximum=5, limited=True, spendable=True)

    def test_spend_spendable(self):
        attr = Attribute(value=5, spendable=True)
        attr.spend(2)
        assert attr.value == 3

    def test_spend_spendable_limited(self):
        attr = Attribute(value=5, minimum=0, maximum=5, limited=True, spendable=True)
        with pytest.raises(UnderflowAttributeException):
            attr.spend(7)
        assert attr.value == 5

    def test_gain_spendable_limited(self):
        attr = Attribute(value=5, maximum=5, limited=True, spendable=True)
        with pytest.raises(OverflowAttributeException):
            attr.gain(1)
        assert attr.value == 5

    def test_gain_spendable(self):
        attr = Attribute(value=5, spendable=True)
        attr.gain(2)
        assert attr.value == 7

    def test_spend_unspendable(self):
        attr = Attribute(value=5, spendable=False)
        with pytest.raises(NotSpendableException):
            attr.spend(2)
        assert attr.value == 5

    def test_gain_unspendable(self):
        attr = Attribute(value=5, spendable=False)
        with pytest.raises(NotSpendableException):
            attr.gain(2)
        assert attr.value == 5

    def test_update_with_int(self):
        attr = Attribute(value=5)
        attr.update(2)
        assert attr.value == 2

    def test_update_limited_with_int_max(self):
        attr = Attribute(value=5, maximum=5, limited=True)
        with pytest.raises(OverflowAttributeException):
            attr.update(7)
        assert attr.value == 5

    def test_update_limited_with_int_min(self):
        attr = Attribute(value=5, minimum=5, maximum=5, limited=True)
        with pytest.raises(UnderflowAttributeException):
            attr.update(2)
        assert attr.value == 5

    def test_update_with_attribute(self):
        attr = Attribute(value=5)
        other = Attribute(value=6)
        attr.update(other)
        assert attr.value == 6

    def test_update_with_limited_attribute(self):
        attr = Attribute(value=5)
        other = Attribute(value=6, limited=True, minimum=1, maximum=7)
        attr.update(other)
        assert attr.value == 6
        assert attr.minimum == 1
        assert attr.maximum == 7
