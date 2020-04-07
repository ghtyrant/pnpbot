import pytest
from pnpbot.systems.base import Dice


class TestDice:
    @pytest.mark.par
    def test_parse_dice(self):
        d = Dice("1d6")

        assert d.number == 1
        assert d.sides == 6

    def test_parse_dice_failure(self):
        with pytest.raises(ValueError):
            Dice("ad6")

    def test_output_dice(self):
        input = "1d6"
        assert str(Dice(input)) == input
