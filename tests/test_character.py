from pnpbot.character import Attribute, Character


class TestCharacter:
    def test_create(self):
        attr = Attribute(name="Test")
        c = Character("Test", [attr])

        print(c.attributes)
        assert c.has_attribute("Test") == True
        assert c.has_attribute("Test") == True
        assert c.get_attribute("test") == attr
        assert "test" in c.attributes
