from typing import Optional, List, Union


class CharStatParseException(Exception):
    pass


class CharStat:
    def __init__(self, value: int, maximum: int, name: str = ""):
        self.name = name
        self.value = value
        self.maximum = maximum

    @staticmethod
    def from_str(name: str, text: str) -> "CharStat":
        if "/" not in text:
            raise CharStatParseException()

        try:
            value, maximum = map(int, text.split("/"))
        except Exception:
            raise CharStatParseException()

        return CharStat(value, maximum, name=name)

    def __str__(self) -> str:
        return f"{self.value}/{self.maximum}"

    def update(self, value: Union[int, "CharStat"]):
        if isinstance(value, int):
            self.value = value
        elif isinstance(value, CharStat):
            self.value = value.value
            self.maximum = value.maximum


class Character:
    def __init__(self, name: str, stats: List[CharStat]):
        self.name = name
        self.stats = {stat.name.lower(): stat for stat in stats}

    def __getitem__(self, item: str) -> Optional[CharStat]:
        return self.stats.get(item.lower(), None)

    def __setitem__(self, item: str, value: Union[CharStat, int]):
        item = item.lower()
        if isinstance(value, CharStat):
            self.stats[item].value = value.value
            self.stats[item].maximum = value.maximum
        else:
            self.stats[item].value = value

    def has_stat(self, name: str) -> bool:
        return name.lower() in self.stats

    def __str__(self) -> str:
        attributes = []
        for name, stat in self.stats.items():
            attributes.append(f"{stat.name}: **{stat}**")
        attributes_str = ", ".join(attributes)
        return f":bust_in_silhouette: {self.name} (:clipboard: {attributes_str})"
