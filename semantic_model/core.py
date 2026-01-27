"""
Базовые типы семантической модели
"""

from dataclasses import dataclass
from enum import Enum


class AreaType(Enum):
    """Тип площади"""
    APARTMENTS = "apartments"
    APART_HOTEL = "apart_hotel"
    OFFICE = "office"
    RETAIL = "retail"
    RETAIL_MALL = "retail_mall"
    PARKING_RESIDENTIAL = "parking_res"
    PARKING_COMMERCIAL = "parking_com"


class OwnershipType(Enum):
    """Форма владения"""
    OWNED = "собственность"
    LEASED = "аренда"


class AggOp(Enum):
    """Оператор агрегации для иерархий (как в MDX)"""
    ADD = "+"      # Сложение (по умолчанию)
    SUB = "-"      # Вычитание
    SKIP = "~"     # Пропуск (не участвует в агрегации)


@dataclass
class Money:
    """
    Деньги в млн.руб.

    Семантически типизированное значение для финансовых расчётов.
    Предотвращает ошибки смешения разных величин.
    """
    value: float

    def __add__(self, other: 'Money') -> 'Money':
        if isinstance(other, Money):
            return Money(self.value + other.value)
        return Money(self.value + other)

    def __radd__(self, other) -> 'Money':
        if other == 0:  # для sum()
            return self
        return Money(other + self.value)

    def __sub__(self, other: 'Money') -> 'Money':
        if isinstance(other, Money):
            return Money(self.value - other.value)
        return Money(self.value - other)

    def __mul__(self, factor: float) -> 'Money':
        return Money(self.value * factor)

    def __rmul__(self, factor: float) -> 'Money':
        return Money(self.value * factor)

    def __truediv__(self, factor: float) -> 'Money':
        return Money(self.value / factor)

    def __neg__(self) -> 'Money':
        return Money(-self.value)

    def __lt__(self, other: 'Money') -> bool:
        return self.value < (other.value if isinstance(other, Money) else other)

    def __le__(self, other: 'Money') -> bool:
        return self.value <= (other.value if isinstance(other, Money) else other)

    def __gt__(self, other: 'Money') -> bool:
        return self.value > (other.value if isinstance(other, Money) else other)

    def __ge__(self, other: 'Money') -> bool:
        return self.value >= (other.value if isinstance(other, Money) else other)

    def __eq__(self, other) -> bool:
        if isinstance(other, Money):
            return abs(self.value - other.value) < 1e-9
        return abs(self.value - other) < 1e-9

    def __repr__(self) -> str:
        return f"{self.value:,.2f} млн"

    def __float__(self) -> float:
        return self.value

    @classmethod
    def zero(cls) -> 'Money':
        return cls(0.0)

    @classmethod
    def from_rub(cls, rub: float) -> 'Money':
        """Конвертация из рублей в млн"""
        return cls(rub / 1_000_000)
