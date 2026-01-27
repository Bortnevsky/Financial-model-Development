"""
Площади - структура и расчёты
"""

from dataclasses import dataclass, field


@dataclass
class AreaUnit:
    """Единица площади (квартиры, офисы и т.д.)"""
    gross_area: float = 0.0          # Общая площадь, м²
    sellable_area: float = 0.0       # Полезная (продаваемая), м²
    unit_count: int = 0              # Количество лотов
    loss_factor: float = 0.0         # Коэфф. потерь (LF)

    @property
    def avg_unit_size(self) -> float:
        """Средняя площадь лота"""
        return self.sellable_area / self.unit_count if self.unit_count else 0

    @property
    def efficiency(self) -> float:
        """Коэффициент эффективности (полезная/общая)"""
        return self.sellable_area / self.gross_area if self.gross_area else 0


@dataclass
class ParkingUnit(AreaUnit):
    """Паркинг"""
    spot_size_gross: float = 40.0    # м² на м/м (общая)
    spot_size_sellable: float = 15.0 # м² на м/м (полезная)

    @property
    def spot_count(self) -> int:
        """Количество машиномест"""
        return self.unit_count


@dataclass
class SocialUnit:
    """Социальный объект"""
    capacity: int = 0                # Мест
    gross_area: float = 0.0          # Площадь
    compensation_amount: float = 0.0 # Компенсация, млн


@dataclass
class AreaBreakdown:
    """Полный состав площадей пускового комплекса"""
    apartments: AreaUnit = field(default_factory=AreaUnit)
    apart_hotel: AreaUnit = field(default_factory=AreaUnit)
    office: AreaUnit = field(default_factory=AreaUnit)
    retail: AreaUnit = field(default_factory=AreaUnit)
    retail_mall: AreaUnit = field(default_factory=AreaUnit)
    parking_residential: ParkingUnit = field(default_factory=ParkingUnit)
    parking_commercial: ParkingUnit = field(default_factory=ParkingUnit)
    school: SocialUnit = field(default_factory=SocialUnit)
    kindergarten: SocialUnit = field(default_factory=SocialUnit)

    @property
    def total_gross(self) -> float:
        """Общая площадь наземной + подземной части"""
        return (self.apartments.gross_area + self.apart_hotel.gross_area +
                self.office.gross_area + self.retail.gross_area +
                self.retail_mall.gross_area + self.school.gross_area +
                self.kindergarten.gross_area +
                self.parking_residential.gross_area +
                self.parking_commercial.gross_area)

    @property
    def total_sellable(self) -> float:
        """Полезная площадь всего"""
        return (self.apartments.sellable_area + self.apart_hotel.sellable_area +
                self.office.sellable_area + self.retail.sellable_area +
                self.retail_mall.sellable_area +
                self.parking_residential.sellable_area +
                self.parking_commercial.sellable_area)

    @property
    def total_units(self) -> int:
        """Всего лотов"""
        return (self.apartments.unit_count + self.apart_hotel.unit_count +
                self.office.unit_count + self.retail.unit_count +
                self.retail_mall.unit_count +
                self.parking_residential.unit_count +
                self.parking_commercial.unit_count)

    @property
    def residential_area(self) -> float:
        """Жилая площадь"""
        return self.apartments.sellable_area + self.apart_hotel.sellable_area

    @property
    def commercial_area(self) -> float:
        """Коммерческая площадь"""
        return (self.office.sellable_area + self.retail.sellable_area +
                self.retail_mall.sellable_area)

    @property
    def total_parking_spots(self) -> int:
        """Всего машиномест"""
        return (self.parking_residential.unit_count +
                self.parking_commercial.unit_count)
