from dataclasses import dataclass
from typing import Literal, Optional

from pandas.core.computation.ops import Op

Method =[
    "Decourt-Quaresma",
    "Mayerhof",
    "Reese & Wright",
    "Schmertmann"
]

PileData_alpha = {
    "Prefabricated driven piles or steel piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Franki piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Driven wooden piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Vibrating or vibropressed": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Cast in place screw piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Prefabricated screw piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Cast in place screw piles with additional grouting": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Prefabricated screw piles with additional grouting": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Steel tubular piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Continuous flight auger piles (CFA)": {"sand": 0.3, "clay": 0.3, "silt": 0.3},
    "Bored piles or piles sheeted by bentonite suspense": {"sand": 0.5, "clay": 0.85, "silt": 0.6},
    "Bore piles with steel casing": {"sand": 0.5, "clay": 0.85, "silt": 0.6},
}

PileData_beta = {
    "Prefabricated driven piles or steel piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Franki piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Driven wooden piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Vibrating or vibropressed": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Cast in place screw piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Prefabricated screw piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Cast in place screw piles with additional grouting": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Prefabricated screw piles with additional grouting": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Steel tubular piles": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Continuous flight auger piles (CFA)": {"sand": 1.0, "clay": 1.0, "silt": 1.0},
    "Bored piles or piles sheeted by bentonite suspense": {"sand": 0.5, "clay": 0.8, "silt": 0.65},
    "Bore piles with steel casing": {"sand": 0.5, "clay": 0.8, "silt": 0.65},
}

Kdp={
    "sand":400,
    "clayey sand":400,
    "silty - clayey sand":400,
    "clayey - silty sand":400,
    "silty sand":400,
    "clay":120,
    "sandy clay":120,
    "silty - sandy clay":120,
    "sandy - silty clay":120,
    "silty clay":120,
    "silt":200,
    "sandy silt":250,
    "clayey - sandy silt":250,
    "sandy - clayey silt":200,
    "clayey silt":200
}

SoilType = {
    "sand":{"sand","clayey sand", "silty - clayey sand", "clayey - silty sand", "silty sand"},
    "clay":{"clay", "sandy clay", "silty - sandy clay", "sandy - silty clay", "silty clay"},
    "silt":{"silt", "sandy silt", "clayey - sandy silt", "sandy - clayey silt", "clayey silt"}
}

SoilBehavior = ["clay", "silt", "sand"]



@dataclass
class SoilLayer:
    thickness_m: float
    soil_behavior: SoilBehavior
    soil_type:Optional[str]
    # Clay params
    nspt: Optional[float] = None
    su:Optional[float] = None
    alpha_tomlinson:Optional[float] = None
    gamma_eff: Optional[float] = None
    # Silt params
    nspt: Optional[float] = None
    # Sand params
    nspt: Optional[float] = None
    gamma_eff: Optional[float] = None
    phi: Optional[float] = None

def validate_inputs(
    method:str,
    diameter_m: float,
    pile_depth_m: float,
    cutoff_m:float,
    fs: float,
    dz: float,
    layers: list[SoilLayer],
) -> None:
    if diameter_m <= 0.0:
        raise ValueError("Pile Diameter should > 0")
    if pile_depth_m <= 0.0:
        raise ValueError("Depth of Pile should > 0")
    if cutoff_m < 0.0:
        raise ValueError("Cut Off Should have positive number")
    if fs <= 0.0:
        raise ValueError("Safety of Factor should > 0")
    if dz <= 0.0:
        raise ValueError("Vertical Increment should > 0")
    if len(layers) == 0:
        raise ValueError("1 layer minimun required")
    for i, layer in enumerate(layers, start=1):
        if layer.thickness_m <= 0.0:
            raise ValueError(f"layer #{i} thickness should > 0")

        if method == "Decourt-Quaresma":
            if layer.soil_behavior == "clay":
                if layer.nspt is None:
                    raise ValueError(f"Clay Layer #{i}: Fill NSPT")
                if layer.nspt <= 0.0:
                    raise ValueError(f"Clay Layer #{i}: NSPT should > 0")
            if layer.soil_behavior == "silt":
                if layer.nspt is None:
                    raise ValueError(f"Silt Layer #{i}: Fill NSPT")
                if layer.nspt <= 0.0:
                    raise ValueError(f"Silt Layer #{i}: NSPT should > 0")
            if layer.soil_behavior == "sand":
                if layer.nspt is None:
                    raise ValueError(f"Sand Layer #{i}: Fill NSPT")
                if layer.nspt <= 0.0:
                    raise ValueError(f"Sand Layer #{i}: NSPT should > 0")

        if method == "Mayerhof":
            if layer.soil_behavior == "clay":
                if layer.su is None:
                    raise ValueError(f"Clay Layer #{i}: Fill Su")
                if layer.su <= 0.0:
                    raise ValueError(f"Clay Layer #{i}: Su should > 0")
                if layer.alpha_tomlinson is None:
                    raise ValueError(f"Clay Layer #{i}: Fill Alpha")
                if layer.alpha_tomlinson <= 0.0:
                    raise ValueError(f"Clay Layer #{i}: Alpha should > 0")
            if layer.soil_behavior == "sand":
                if layer.gamma_eff is None:
                    raise ValueError(f"Sand Layer #{i}: Fill Effective Unit Weight")
                if layer.gamma_eff <= 0.0:
                    raise ValueError(f"Sand Layer #{i}: Effective Unit Weight should > 0")
                if layer.phi is None:
                    raise ValueError(f"Sand Layer #{i}: Fill Friction Angle")
                if layer.phi <= 0.0:
                    raise ValueError(f"Sand Layer #{i}: Fill Friction Angle should > 0")


