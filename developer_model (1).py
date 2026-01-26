"""
Семантическая модель девелоперского проекта
На примере ЖК Касаткина
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import List, Dict, Optional
from enum import Enum
import numpy as np
import numpy_financial as npf


# =============================================================================
# БАЗОВЫЕ ТИПЫ
# =============================================================================

class AreaType(Enum):
    APARTMENTS = "apartments"
    APART_HOTEL = "apart_hotel"
    OFFICE = "office"
    RETAIL = "retail"
    RETAIL_MALL = "retail_mall"
    PARKING_RESIDENTIAL = "parking_res"
    PARKING_COMMERCIAL = "parking_com"


class OwnershipType(Enum):
    OWNED = "собственность"
    LEASED = "аренда"


@dataclass
class Money:
    """Деньги в млн.руб."""
    value: float
    
    def __add__(self, other): return Money(self.value + other.value)
    def __sub__(self, other): return Money(self.value - other.value)
    def __mul__(self, factor: float): return Money(self.value * factor)
    def __truediv__(self, factor: float): return Money(self.value / factor)
    def __neg__(self): return Money(-self.value)
    def __repr__(self): return f"{self.value:,.2f} млн"


# =============================================================================
# ПЛОЩАДИ
# =============================================================================

@dataclass
class AreaUnit:
    """Единица площади (квартиры, офисы, паркинг и т.д.)"""
    gross_area: float = 0.0          # Общая площадь, м²
    sellable_area: float = 0.0       # Полезная (продаваемая), м²
    unit_count: int = 0              # Количество лотов
    loss_factor: float = 0.0         # Коэфф. потерь (LF)
    
    @property
    def avg_unit_size(self) -> float:
        """Средняя площадь лота"""
        return self.sellable_area / self.unit_count if self.unit_count else 0


@dataclass 
class ParkingUnit(AreaUnit):
    """Паркинг"""
    spot_size_gross: float = 40.0    # м² на м/м (общая)
    spot_size_sellable: float = 15.0 # м² на м/м (полезная)


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


# =============================================================================
# СРОКИ
# =============================================================================

@dataclass
class Timeline:
    """Сроки проекта/очереди"""
    project_start: date = None           # Начало проекта
    ird_duration_quarters: int = 5       # Срок ИРД (до РнС)
    construction_months: int = 24        # Срок СМР
    sales_lag_after_rnv: int = 6         # Месяцев продаж после РнВ
    
    @property
    def rns_date(self) -> date:
        """РнС - разрешение на строительство"""
        if not self.project_start:
            return None
        months = self.ird_duration_quarters * 3
        return self.project_start + timedelta(days=months * 30)
    
    @property
    def rnv_date(self) -> date:
        """РнВ - разрешение на ввод"""
        if not self.rns_date:
            return None
        return self.rns_date + timedelta(days=self.construction_months * 30)
    
    @property
    def sales_end_date(self) -> date:
        """Окончание продаж"""
        if not self.rnv_date:
            return None
        return self.rnv_date + timedelta(days=self.sales_lag_after_rnv * 30)
    
    @property
    def total_quarters(self) -> int:
        """Всего кварталов проекта"""
        if not self.project_start or not self.sales_end_date:
            return 0
        days = (self.sales_end_date - self.project_start).days
        return int(days / 90) + 1


# =============================================================================
# ЦЕНЫ И ДОХОДЫ
# =============================================================================

@dataclass
class PricingModel:
    """Ценообразование для типа площади"""
    price_start: float = 0.0             # Цена старт, руб/м²
    price_escalation_quarterly: float = 0.02  # Эскалация, % в квартал
    sales_start_quarter: int = 1         # Начало продаж (квартал от РнС)
    
    def price_at_quarter(self, quarter: int) -> float:
        """Цена в конкретном квартале"""
        if quarter < self.sales_start_quarter:
            return self.price_start
        periods = quarter - self.sales_start_quarter
        return self.price_start * (1 + self.price_escalation_quarterly) ** periods


@dataclass
class SalesSchedule:
    """График продаж"""
    curve: List[float] = field(default_factory=list)  # % продаж по кварталам
    
    @classmethod
    def bell_curve(cls, total_quarters: int, peak_at: float = 0.5) -> 'SalesSchedule':
        """Генерация колоколообразной кривой продаж"""
        x = np.linspace(0, 1, total_quarters)
        # Простая параболическая кривая с пиком в peak_at
        curve = np.exp(-((x - peak_at) ** 2) / 0.1)
        curve = curve / curve.sum()  # Нормализация до 100%
        return cls(curve=curve.tolist())
    
    @classmethod
    def linear(cls, total_quarters: int) -> 'SalesSchedule':
        """Равномерный график"""
        return cls(curve=[1.0 / total_quarters] * total_quarters)


@dataclass
class RevenueModel:
    """Модель доходов для типа площади"""
    area_type: AreaType
    sellable_area: float                 # м²
    unit_count: int                      # лотов
    pricing: PricingModel
    schedule: SalesSchedule
    
    def revenue_at_quarter(self, quarter: int) -> Money:
        """Выручка в квартале"""
        if quarter < 0 or quarter >= len(self.schedule.curve):
            return Money(0)
        
        area_sold = self.sellable_area * self.schedule.curve[quarter]
        price = self.pricing.price_at_quarter(quarter)
        return Money(area_sold * price / 1_000_000)  # в млн
    
    @property
    def total_revenue(self) -> Money:
        """Выручка всего"""
        total = sum(
            self.revenue_at_quarter(q).value 
            for q in range(len(self.schedule.curve))
        )
        return Money(total)
    
    @property
    def avg_price(self) -> float:
        """Средневзвешенная цена реализации"""
        if self.sellable_area == 0:
            return 0
        return self.total_revenue.value * 1_000_000 / self.sellable_area


# =============================================================================
# ЗАТРАТЫ
# =============================================================================

@dataclass
class CostItem:
    """Статья затрат"""
    name: str
    total: Money = field(default_factory=lambda: Money(0))
    cost_per_sqm: float = 0.0            # руб/м² (если применимо)
    pct_of_base: float = 0.0             # % от базы (если применимо)
    schedule: List[float] = field(default_factory=list)  # График освоения
    
    def at_quarter(self, quarter: int) -> Money:
        """Затраты в квартале"""
        if not self.schedule or quarter >= len(self.schedule):
            return Money(0)
        return Money(self.total.value * self.schedule[quarter])


@dataclass
class ConstructionCosts:
    """Затраты на СМР"""
    residential: CostItem = field(default_factory=lambda: CostItem("СМР жилье"))
    office: CostItem = field(default_factory=lambda: CostItem("СМР офисы"))
    retail: CostItem = field(default_factory=lambda: CostItem("СМР ТЦ"))
    social: CostItem = field(default_factory=lambda: CostItem("СМР соц.объекты"))
    
    @property
    def total(self) -> Money:
        return (self.residential.total + self.office.total + 
                self.retail.total + self.social.total)


@dataclass
class CostStructure:
    """Полная структура затрат пускового комплекса"""
    # Вход
    land_acquisition: Money = field(default_factory=lambda: Money(0))
    finders_fee: Money = field(default_factory=lambda: Money(0))
    finders_fee_pct: float = 0.0
    
    # ВРИ
    vri_base: Money = field(default_factory=lambda: Money(0))
    vri_discount: Money = field(default_factory=lambda: Money(0))
    vri_benefit_purchase: Money = field(default_factory=lambda: Money(0))
    
    # Земля
    land_legal: Money = field(default_factory=lambda: Money(0))
    land_rent: Money = field(default_factory=lambda: Money(0))
    
    # Проектирование и согласования
    design: Money = field(default_factory=lambda: Money(0))
    approvals: Money = field(default_factory=lambda: Money(0))
    
    # СМР
    construction: ConstructionCosts = field(default_factory=ConstructionCosts)
    
    # Прочее строительство
    finishing: Money = field(default_factory=lambda: Money(0))
    utilities: Money = field(default_factory=lambda: Money(0))
    site_management: Money = field(default_factory=lambda: Money(0))
    monitoring: Money = field(default_factory=lambda: Money(0))
    project_management: Money = field(default_factory=lambda: Money(0))
    contingency: Money = field(default_factory=lambda: Money(0))
    contingency_pct: float = 0.05
    
    @property
    def total_land(self) -> Money:
        """Затраты на землю"""
        return (self.land_acquisition + self.finders_fee + 
                self.vri_base + self.vri_discount + self.vri_benefit_purchase +
                self.land_legal + self.land_rent)
    
    @property
    def total_construction(self) -> Money:
        """Затраты на строительство"""
        return (self.design + self.approvals + self.construction.total +
                self.finishing + self.utilities + self.site_management +
                self.monitoring + self.project_management + self.contingency)
    
    @property
    def total_investments(self) -> Money:
        """Инвестиции всего"""
        return self.total_land + self.total_construction


# =============================================================================
# РАСХОДЫ НА ПРОДАЖУ
# =============================================================================

@dataclass
class SalesExpenses:
    """Расходы на продажу"""
    admin_quarterly: Money = field(default_factory=lambda: Money(2.0))  # АХР
    marketing_pct: float = 0.03          # Маркетинг, % от выручки
    brokerage_pct: float = 0.03          # Брокеридж, % от выручки
    sales_management_pct: float = 0.012  # Управление продажами
    registration_per_unit: float = 30000 # Регистрация, руб/лот
    
    def calculate(self, total_revenue: Money, unit_count: int, 
                  quarters: int) -> Money:
        """Расчёт расходов на продажу"""
        admin = Money(self.admin_quarterly.value * quarters)
        marketing = total_revenue * self.marketing_pct
        brokerage = total_revenue * self.brokerage_pct
        sales_mgmt = total_revenue * self.sales_management_pct
        registration = Money(self.registration_per_unit * unit_count / 1_000_000)
        return admin + marketing + brokerage + sales_mgmt + registration


# =============================================================================
# ФИНАНСИРОВАНИЕ
# =============================================================================

@dataclass
class BridgeLoan:
    """Бридж-кредит"""
    limit: Money = field(default_factory=lambda: Money(0))
    margin_over_ks: float = 0.05         # Маржа над КС
    commitment_fee: float = 0.005        # Комиссия за резерв
    
    def interest_at_quarter(self, outstanding: Money, ks_rate: float) -> Money:
        """Проценты за квартал"""
        rate = (ks_rate + self.margin_over_ks) / 4  # Квартальная ставка
        return outstanding * rate


@dataclass
class ProjectFinance:
    """Проектное финансирование"""
    limit: Money = field(default_factory=lambda: Money(0))
    ltv: float = 0.70                    # % от стоимости
    margin_over_ks: float = 0.038        # Маржа над КС
    escrow_rate: float = 0.01            # Ставка под эскроу
    escrow_threshold: float = 1.0        # Порог покрытия для льготной ставки
    commitment_fee: float = 0.005
    
    def effective_rate(self, escrow_coverage: float, ks_rate: float) -> float:
        """Эффективная ставка с учётом покрытия эскроу"""
        if escrow_coverage >= self.escrow_threshold:
            return self.escrow_rate
        # Взвешенная ставка
        base_rate = ks_rate + self.margin_over_ks
        return base_rate * (1 - escrow_coverage) + self.escrow_rate * escrow_coverage
    
    def interest_at_quarter(self, outstanding: Money, escrow: Money, 
                            ks_rate: float) -> Money:
        """Проценты за квартал"""
        if outstanding.value == 0:
            return Money(0)
        coverage = escrow.value / outstanding.value if outstanding.value > 0 else 0
        rate = self.effective_rate(coverage, ks_rate) / 4
        return outstanding * rate


@dataclass
class FinancingStructure:
    """Структура финансирования"""
    equity: Money = field(default_factory=lambda: Money(0))
    equity_rate: float = 0.01            # Ставка займа акционеров
    bridge: BridgeLoan = field(default_factory=BridgeLoan)
    project_finance: ProjectFinance = field(default_factory=ProjectFinance)


# =============================================================================
# ПУСКОВОЙ КОМПЛЕКС (ОЧЕРЕДЬ)
# =============================================================================

@dataclass
class LaunchComplex:
    """Пусковой комплекс (очередь)"""
    id: int
    name: str
    
    # Компоненты
    timeline: Timeline = field(default_factory=Timeline)
    areas: AreaBreakdown = field(default_factory=AreaBreakdown)
    costs: CostStructure = field(default_factory=CostStructure)
    sales_expenses: SalesExpenses = field(default_factory=SalesExpenses)
    financing: FinancingStructure = field(default_factory=FinancingStructure)
    
    # Модели доходов по типам площадей
    revenue_models: Dict[AreaType, RevenueModel] = field(default_factory=dict)
    
    def setup_revenue_models(self, pricing: Dict[AreaType, PricingModel]):
        """Настройка моделей доходов"""
        quarters = self.timeline.total_quarters
        
        # Квартиры
        if self.areas.apartments.sellable_area > 0:
            self.revenue_models[AreaType.APARTMENTS] = RevenueModel(
                area_type=AreaType.APARTMENTS,
                sellable_area=self.areas.apartments.sellable_area,
                unit_count=self.areas.apartments.unit_count,
                pricing=pricing.get(AreaType.APARTMENTS, PricingModel()),
                schedule=SalesSchedule.bell_curve(quarters, peak_at=0.6)
            )
        
        # Ритейл
        if self.areas.retail.sellable_area > 0:
            self.revenue_models[AreaType.RETAIL] = RevenueModel(
                area_type=AreaType.RETAIL,
                sellable_area=self.areas.retail.sellable_area,
                unit_count=self.areas.retail.unit_count,
                pricing=pricing.get(AreaType.RETAIL, PricingModel()),
                schedule=SalesSchedule.linear(quarters)
            )
        
        # Паркинг
        if self.areas.parking_residential.sellable_area > 0:
            self.revenue_models[AreaType.PARKING_RESIDENTIAL] = RevenueModel(
                area_type=AreaType.PARKING_RESIDENTIAL,
                sellable_area=self.areas.parking_residential.sellable_area,
                unit_count=self.areas.parking_residential.unit_count,
                pricing=pricing.get(AreaType.PARKING_RESIDENTIAL, PricingModel()),
                schedule=SalesSchedule.bell_curve(quarters, peak_at=0.7)
            )
    
    # --- РАСЧЁТНЫЕ СВОЙСТВА ---
    
    @property
    def total_revenue(self) -> Money:
        """Выручка всего"""
        return Money(sum(rm.total_revenue.value for rm in self.revenue_models.values()))
    
    @property
    def total_sales_expenses(self) -> Money:
        """Расходы на продажу всего"""
        return self.sales_expenses.calculate(
            self.total_revenue,
            self.areas.total_units,
            self.timeline.total_quarters
        )
    
    @property
    def total_investments(self) -> Money:
        """Инвестиции всего"""
        return self.costs.total_investments
    
    @property
    def profit_before_tax(self) -> Money:
        """Прибыль до налогообложения"""
        # Упрощённо: Выручка - Инвестиции - Расходы на продажу
        # В реальности нужно учитывать проценты, налоги и т.д.
        return self.total_revenue - self.total_investments - self.total_sales_expenses
    
    @property
    def margin_before_tax(self) -> float:
        """Маржинальность до налогообложения"""
        if self.total_revenue.value == 0:
            return 0
        return self.profit_before_tax.value / self.total_revenue.value


# =============================================================================
# ПРОЕКТ
# =============================================================================

@dataclass
class LandPlot:
    """Земельный участок"""
    cadastral_number: str = ""
    area_sqm: float = 0.0
    ownership: OwnershipType = OwnershipType.LEASED
    density_limit: float = 35000         # м²/га


@dataclass
class MacroAssumptions:
    """Макро-предпосылки"""
    key_rate: float = 0.21               # Ключевая ставка
    profit_tax_rate: float = 0.20        # Налог на прибыль
    vat_rate: float = 0.20               # НДС
    discount_rate: float = 0.20          # Ставка дисконтирования


@dataclass
class Project:
    """Девелоперский проект"""
    name: str
    land: LandPlot = field(default_factory=LandPlot)
    macro: MacroAssumptions = field(default_factory=MacroAssumptions)
    launch_complexes: List[LaunchComplex] = field(default_factory=list)
    
    # --- АГРЕГАЦИЯ ПО ОЧЕРЕДЯМ ---
    
    @property
    def total_gross_area(self) -> float:
        """Общая площадь проекта"""
        return sum(lc.areas.total_gross for lc in self.launch_complexes)
    
    @property
    def total_sellable_area(self) -> float:
        """Полезная площадь проекта"""
        return sum(lc.areas.total_sellable for lc in self.launch_complexes)
    
    @property
    def total_units(self) -> int:
        """Всего лотов"""
        return sum(lc.areas.total_units for lc in self.launch_complexes)
    
    @property
    def total_revenue(self) -> Money:
        """Выручка проекта"""
        return Money(sum(lc.total_revenue.value for lc in self.launch_complexes))
    
    @property
    def total_investments(self) -> Money:
        """Инвестиции проекта"""
        return Money(sum(lc.total_investments.value for lc in self.launch_complexes))
    
    @property
    def total_sales_expenses(self) -> Money:
        """Расходы на продажу"""
        return Money(sum(lc.total_sales_expenses.value for lc in self.launch_complexes))
    
    @property
    def profit_before_tax(self) -> Money:
        """Прибыль до налогообложения"""
        return self.total_revenue - self.total_investments - self.total_sales_expenses
    
    @property
    def profit_after_tax(self) -> Money:
        """Прибыль после налогообложения"""
        tax = self.profit_before_tax * self.macro.profit_tax_rate
        return self.profit_before_tax - tax
    
    @property
    def margin_before_tax(self) -> float:
        """Маржинальность до Н/О"""
        if self.total_revenue.value == 0:
            return 0
        return self.profit_before_tax.value / self.total_revenue.value
    
    @property
    def margin_after_tax(self) -> float:
        """Маржинальность после Н/О"""
        if self.total_revenue.value == 0:
            return 0
        return self.profit_after_tax.value / self.total_revenue.value
    
    # --- CASH FLOW И IRR ---
    
    def build_cashflow(self) -> List[float]:
        """Построить денежный поток проекта (упрощённо)"""
        # Находим максимальное количество периодов
        max_quarters = max(
            (lc.timeline.total_quarters for lc in self.launch_complexes),
            default=0
        )
        
        if max_quarters == 0:
            return []
        
        cashflow = [0.0] * max_quarters
        
        for lc in self.launch_complexes:
            # Инвестиции (отрицательный поток в начале)
            invest_per_q = lc.total_investments.value / lc.timeline.ird_duration_quarters
            for q in range(min(lc.timeline.ird_duration_quarters, max_quarters)):
                cashflow[q] -= invest_per_q
            
            # Выручка (по графику продаж)
            for area_type, rm in lc.revenue_models.items():
                for q in range(min(len(rm.schedule.curve), max_quarters)):
                    cashflow[q] += rm.revenue_at_quarter(q).value
            
            # Расходы на продажу (пропорционально выручке)
            if lc.total_revenue.value > 0:
                expense_ratio = lc.total_sales_expenses.value / lc.total_revenue.value
                for q in range(max_quarters):
                    revenue_q = sum(
                        rm.revenue_at_quarter(q).value 
                        for rm in lc.revenue_models.values()
                    )
                    cashflow[q] -= revenue_q * expense_ratio
        
        return cashflow
    
    @property
    def irr(self) -> float:
        """IRR проекта"""
        cf = self.build_cashflow()
        if not cf or all(x >= 0 for x in cf) or all(x <= 0 for x in cf):
            return 0.0
        try:
            quarterly_irr = npf.irr(cf)
            annual_irr = (1 + quarterly_irr) ** 4 - 1  # Годовая ставка
            return annual_irr
        except:
            return 0.0
    
    @property
    def npv(self) -> Money:
        """NPV проекта"""
        cf = self.build_cashflow()
        if not cf:
            return Money(0)
        quarterly_rate = (1 + self.macro.discount_rate) ** 0.25 - 1
        try:
            return Money(npf.npv(quarterly_rate, cf))
        except:
            return Money(0)
    
    # --- ОПЕРАЦИИ ---
    
    def add_launch_complex(self, **kwargs) -> LaunchComplex:
        """Добавить пусковой комплекс"""
        lc_id = len(self.launch_complexes) + 1
        lc = LaunchComplex(id=lc_id, name=f"ПК{lc_id}", **kwargs)
        self.launch_complexes.append(lc)
        return lc
    
    def summary(self) -> str:
        """Резюме проекта"""
        return f"""
╔══════════════════════════════════════════════════════════════════╗
║  ПРОЕКТ: {self.name:^54} ║
╠══════════════════════════════════════════════════════════════════╣
║  Площадь ЗУ:        {self.land.area_sqm:>15,.0f} м²                      ║
║  Общая площадь:     {self.total_gross_area:>15,.0f} м²                      ║
║  Полезная площадь:  {self.total_sellable_area:>15,.0f} м²                      ║
║  Всего лотов:       {self.total_units:>15,}                            ║
╠══════════════════════════════════════════════════════════════════╣
║  ФИНАНСОВЫЕ ПОКАЗАТЕЛИ                                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Выручка:           {self.total_revenue.value:>15,.2f} млн                     ║
║  Инвестиции:        {self.total_investments.value:>15,.2f} млн                     ║
║  Расходы на продажу:{self.total_sales_expenses.value:>15,.2f} млн                     ║
║  Прибыль до Н/О:    {self.profit_before_tax.value:>15,.2f} млн                     ║
║  Прибыль после Н/О: {self.profit_after_tax.value:>15,.2f} млн                     ║
╠══════════════════════════════════════════════════════════════════╣
║  Маржа до Н/О:      {self.margin_before_tax:>15.1%}                            ║
║  Маржа после Н/О:   {self.margin_after_tax:>15.1%}                            ║
║  IRR проекта:       {self.irr:>15.1%}                            ║
║  NPV:               {self.npv.value:>15,.2f} млн                     ║
╚══════════════════════════════════════════════════════════════════╝
"""


# =============================================================================
# ПРИМЕР: ЗАГРУЗКА КАСАТКИНА
# =============================================================================

def create_kasatkina() -> Project:
    """Создание проекта Касаткина из данных Excel"""
    
    project = Project(
        name="КАСАТКИНА",
        land=LandPlot(
            cadastral_number="77:02:0019010:102",
            area_sqm=47_620,
            ownership=OwnershipType.LEASED,
            density_limit=35_000
        ),
        macro=MacroAssumptions(
            key_rate=0.21,
            discount_rate=0.20
        )
    )
    
    # === ОЧЕРЕДЬ 1 ===
    lc1 = project.add_launch_complex()
    lc1.name = "1 очередь"
    
    lc1.timeline = Timeline(
        project_start=date(2025, 4, 1),
        ird_duration_quarters=5,
        construction_months=24,
        sales_lag_after_rnv=15
    )
    
    lc1.areas = AreaBreakdown(
        apartments=AreaUnit(
            gross_area=100_892,
            sellable_area=70_624,
            unit_count=1_332,
            loss_factor=0.30
        ),
        retail=AreaUnit(
            gross_area=5_160,
            sellable_area=3_870,
            unit_count=39,
            loss_factor=0.25
        ),
        parking_residential=ParkingUnit(
            gross_area=28_480,
            sellable_area=10_680,
            unit_count=712
        )
    )
    
    lc1.costs = CostStructure(
        land_acquisition=Money(2_457.79),
        finders_fee=Money(0),
        vri_base=Money(5_412.33),
        vri_discount=Money(-5_412.33),
        vri_benefit_purchase=Money(3_000.39),
        land_legal=Money(3_151.22),
        land_rent=Money(150.99),
        design=Money(982.96),
        approvals=Money(134.46),
        construction=ConstructionCosts(
            residential=CostItem("СМР жилье", Money(18_422.08)),
            social=CostItem("СМР соц", Money(2_795.43))
        ),
        finishing=Money(103.58),
        utilities=Money(739.49),
        site_management=Money(0),
        monitoring=Money(336.24),
        project_management=Money(959.16),
        contingency=Money(470.30)
    )
    
    lc1.setup_revenue_models({
        AreaType.APARTMENTS: PricingModel(
            price_start=580_000,
            price_escalation_quarterly=0.02,
            sales_start_quarter=1
        ),
        AreaType.RETAIL: PricingModel(
            price_start=700_000,
            price_escalation_quarterly=0.01,
            sales_start_quarter=4
        ),
        AreaType.PARKING_RESIDENTIAL: PricingModel(
            price_start=300_000,  # за м/м
            price_escalation_quarterly=0.01,
            sales_start_quarter=6
        )
    })
    
    # === ОЧЕРЕДЬ 2 ===
    lc2 = project.add_launch_complex()
    lc2.name = "2 очередь"
    
    lc2.timeline = Timeline(
        project_start=date(2026, 7, 1),
        ird_duration_quarters=5,
        construction_months=24,
        sales_lag_after_rnv=12
    )
    
    lc2.areas = AreaBreakdown(
        apartments=AreaUnit(
            gross_area=56_683,
            sellable_area=39_678,
            unit_count=749,
            loss_factor=0.30
        ),
        retail=AreaUnit(
            gross_area=2_938,
            sellable_area=2_203,
            unit_count=22,
            loss_factor=0.25
        ),
        parking_residential=ParkingUnit(
            gross_area=16_000,
            sellable_area=6_000,
            unit_count=400
        )
    )
    
    lc2.costs = CostStructure(
        land_acquisition=Money(1_383.56),
        vri_base=Money(3_046.01),
        vri_discount=Money(-3_046.01),
        vri_benefit_purchase=Money(1_688.90),
        land_legal=Money(1_773.99),
        land_rent=Money(84.93),
        design=Money(553.35),
        approvals=Money(75.69),
        construction=ConstructionCosts(
            residential=CostItem("СМР жилье", Money(10_368.91)),
            social=CostItem("СМР соц", Money(1_573.81))
        ),
        finishing=Money(58.30),
        utilities=Money(416.35),
        monitoring=Money(189.14),
        project_management=Money(540.23),
        contingency=Money(264.70)
    )
    
    lc2.setup_revenue_models({
        AreaType.APARTMENTS: PricingModel(
            price_start=620_000,
            price_escalation_quarterly=0.02,
            sales_start_quarter=1
        ),
        AreaType.RETAIL: PricingModel(
            price_start=700_000,
            price_escalation_quarterly=0.01,
            sales_start_quarter=4
        ),
        AreaType.PARKING_RESIDENTIAL: PricingModel(
            price_start=300_000,
            price_escalation_quarterly=0.01,
            sales_start_quarter=6
        )
    })
    
    return project


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    # Создаём проект
    project = create_kasatkina()
    
    # Выводим резюме
    print(project.summary())
    
    # Детали по очередям
    for lc in project.launch_complexes:
        print(f"\n--- {lc.name} ---")
        print(f"Площадь общая:    {lc.areas.total_gross:,.0f} м²")
        print(f"Площадь полезная: {lc.areas.total_sellable:,.0f} м²")
        print(f"Выручка:          {lc.total_revenue}")
        print(f"Инвестиции:       {lc.total_investments}")
        print(f"Маржа:            {lc.margin_before_tax:.1%}")
    
    # Пример: добавить 3-ю очередь
    print("\n" + "="*60)
    print("ДОБАВЛЯЕМ 3-Ю ОЧЕРЕДЬ...")
    print("="*60)
    
    lc3 = project.add_launch_complex()
    lc3.name = "3 очередь"
    lc3.timeline = Timeline(
        project_start=date(2028, 1, 1),
        ird_duration_quarters=4,
        construction_months=20
    )
    lc3.areas = AreaBreakdown(
        apartments=AreaUnit(
            gross_area=45_000,
            sellable_area=31_500,
            unit_count=600,
            loss_factor=0.30
        )
    )
    lc3.costs = CostStructure(
        land_acquisition=Money(1_000),
        construction=ConstructionCosts(
            residential=CostItem("СМР жилье", Money(8_000))
        )
    )
    lc3.setup_revenue_models({
        AreaType.APARTMENTS: PricingModel(
            price_start=650_000,
            price_escalation_quarterly=0.02
        )
    })
    
    # Новое резюме
    print(project.summary())
