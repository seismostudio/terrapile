import math


def compute_pile_tip_area_m2_from_diameter(diameter_m: float) -> float:
    if diameter_m <= 0.0:
        raise ValueError("Diameter harus > 0")
    return math.pi * (diameter_m ** 2) / 4.0


def compute_pile_perimeter_m_from_diameter(diameter_m: float) -> float:
    if diameter_m <= 0.0:
        raise ValueError("Diameter harus > 0")
    return math.pi * diameter_m


