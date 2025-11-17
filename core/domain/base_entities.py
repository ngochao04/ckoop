from dataclasses import dataclass
from typing import Any
@dataclass(frozen=True)
class ValueObject:
    def __eq__(self, other: Any) -> bool:
        return isinstance(other, self.__class__) and self.__dict__ == other.__dict__
class Entity: id: Any
class AggregateRoot(Entity): pass
