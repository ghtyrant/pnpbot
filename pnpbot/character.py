from typing import Optional, List, Union


class AttributeParseException(Exception):
    def __init__(self, stat_name: str):
        super().__init__()
        self.stat_name = stat_name


class AnonymousAttributeException(Exception):
    pass


class UnknownAttributeException(Exception):
    def __init__(self, stat_name: str):
        super().__init__()
        self.stat_name = stat_name


class MissingAttributesException(Exception):
    def __init__(self, missing: List[str]):
        super().__init__()
        self.missing = missing


class UnderflowAttributeException(Exception):
    def __init__(self, current: int, new: int, minimum: int):
        self.current = current
        self.new = new
        self.minium = minimum


class OverflowAttributeException(Exception):
    def __init__(self, current: int, new: int, maximum: int):
        self.current = current
        self.new = new
        self.maximum = maximum


class NotSpendableException(Exception):
    pass


class Attribute:
    def __init__(
        self,
        value: int = 0,
        minimum: int = 0,
        maximum: int = 0,
        limited: bool = False,
        spendable: bool = False,
        name: str = "",
    ):
        self.name = name
        self.value = value
        self.minimum = minimum
        self.maximum = maximum
        self.limited = limited
        self.spendable = spendable

    @staticmethod
    def from_str(text: str) -> "Attribute":
        name = ""
        if "=" in text:
            sep_pos = text.find("=")
            name = text[:sep_pos].strip()
            text = text[sep_pos + 1 :].strip()

        if "/" not in text:
            try:
                value = int(text)
            except Exception:
                raise AttributeParseException(name)

            return Attribute(name=name, value=value)

        parts = text.split("/")

        limited = False
        minimum = 0
        try:
            limited = True
            if len(parts) == 3:
                minimum = int(parts.pop(0))

            value, maximum = map(int, parts)
        except Exception:
            raise AttributeParseException(name)

        if minimum > maximum:
            raise AttributeParseException(name)

        return Attribute(
            name=name, value=value, minimum=minimum, maximum=maximum, limited=limited
        )

    def __str__(self) -> str:
        if self.limited:
            return f"{self.value}/{self.maximum}"
        else:
            return f"{self.value}"

    def spend(self, amount: int) -> None:
        if not self.spendable:
            raise NotSpendableException()

        new_value = self.value - amount

        if self.limited:
            if new_value < self.minimum:
                raise UnderflowAttributeException(self.value, new_value, self.minimum)

        self.value = new_value

    def gain(self, amount: int) -> None:
        if not self.spendable:
            raise NotSpendableException()

        new_value = self.value + amount

        if self.limited:
            if new_value > self.maximum:
                raise OverflowAttributeException(self.value, new_value, self.maximum)

        self.value = new_value

    def update(self, value: Union[int, "Attribute"]):
        if isinstance(value, int):
            self.value = value
        elif isinstance(value, Attribute):
            self.value = value.value

            if value.limited:
                self.minimum = value.minimum
                self.maximum = value.maximum


class Character:
    def __init__(self, name: str, stats: List[Attribute]):
        self.name = name
        self.attributes = {stat.name.lower(): stat for stat in stats}

    def has_attribute(self, name: str) -> bool:
        return name.lower() in self.attributes

    def get_attribute(self, name: str) -> Optional[Attribute]:
        return self.attributes.get(name.lower(), None)

    def __str__(self) -> str:
        attributes = []
        for name, stat in self.attributes.items():
            attributes.append(f"{stat.name}: **{stat}**")
        attributes_str = ", ".join(attributes)
        return f":bust_in_silhouette: {self.name} (:clipboard: {attributes_str})"
