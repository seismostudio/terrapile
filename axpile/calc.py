from __future__ import annotations

from math import tan
from typing import Optional, Tuple

import numpy as np
import pandas as pd

from .geometry import (
    compute_pile_perimeter_m_from_diameter,
    compute_pile_tip_area_m2_from_diameter,
)
from .models import PileData_alpha, SoilLayer, PileData_beta, Kdp


def expand_layers_to_depth(layers: list[SoilLayer], pile_depth_m: float) -> list[Tuple[float, SoilLayer]]:
    depths: list[Tuple[float, SoilLayer]] = []
    z_top = 0.0
    for layer in layers:
        z_bot = z_top + layer.thickness_m
        if z_top >= pile_depth_m:
            break
        use_bot = min(z_bot, pile_depth_m)
        seg = SoilLayer(
            thickness_m=use_bot - z_top,
            soil_behavior=layer.soil_behavior,
            soil_type=layer.soil_type,
            nspt=layer.nspt,
            su=layer.su,
            alpha_tomlinson=layer.alpha_tomlinson,
            gamma_eff=layer.gamma_eff,
            phi=layer.phi
        )
        depths.append((z_top, seg))
        z_top = z_bot
    return depths

def compute_nspt_average(
    z_tip: float,
    diameter_m: float,
    layers: list[Tuple[float, SoilLayer]]
) -> Optional[float]:
    """Hitung NSPT rata-rata di zona 4D atas dan bawah ujung tiang."""
    z_top_avg = z_tip - 4 * diameter_m
    z_bot_avg = z_tip + 4 * diameter_m
    total_thickness = 0.0
    weighted_sum = 0.0

    for z_top, lyr in layers:
        z_bot = z_top + lyr.thickness_m
        # Cek overlap antara layer dan rentang target
        overlap_top = max(z_top, z_top_avg)
        overlap_bot = min(z_bot, z_bot_avg)
        overlap = overlap_bot - overlap_top
        if overlap > 0:
            if lyr.nspt is not None and lyr.nspt > 0:
                weighted_sum += lyr.nspt * overlap
                total_thickness += overlap

    if total_thickness == 0:
        # Tidak ada data di sekitar ujung tiang
        return None
    return weighted_sum / total_thickness

def compute_distributions(
    method: str,
    diameter_m: float,
    pile_depth_m: float,
    cutoff_m:float,
    fs: float,
    pile_material: str,
    pile_types: str,    
    dz: float,
    layers: list[SoilLayer],
):
    pile_type = pile_types
    ab_m2 = compute_pile_tip_area_m2_from_diameter(diameter_m)
    perim_m = compute_pile_perimeter_m_from_diameter(diameter_m)
    pilelength_m = pile_depth_m - cutoff_m
    segs = expand_layers_to_depth(layers, pile_depth_m)
    if len(segs) == 0:
        raise ValueError("Kedalaman tiang berada di atas semua lapisan (periksa input)")

    z_vals = np.arange(dz, pile_depth_m + dz, dz)
    alpha_vals= np.zeros_like(z_vals)
    beta_vals= np.zeros_like(z_vals)
    kdp_vals= np.zeros_like(z_vals)
    su_vals= np.zeros_like(z_vals)
    # ks_vals= np.zeros_like(z_vals)
    sum_sigma_eff_vals= np.zeros_like(z_vals)
    soil_vals= np.empty_like(z_vals, dtype=object)
    soiltype_vals= np.empty_like(z_vals, dtype=object)
    qb_vals = np.zeros_like(z_vals)
    qs_vals = np.zeros_like(z_vals)
    qult_vals = np.zeros_like(z_vals)
    qall_vals = np.zeros_like(z_vals)

    for i, z in enumerate(z_vals):
        # defaults to avoid unbound local errors for branches not taken
        tip_layer: Optional[SoilLayer] = None
        for z_top, lyr in segs:
            z_bot = z_top + lyr.thickness_m
            if z >= z_top and z <= z_bot + 1e-9:
                tip_layer = lyr
                break

        if tip_layer is None:
            raise ValueError("No layer found at specified depth (check input)")

        # Qb Calculation
        if tip_layer.soil_behavior in ["clay", "silt", "sand"]:

            # Decourt Quaresma
            if method =="Decourt-Quaresma":
                alpha = PileData_alpha[pile_type][tip_layer.soil_behavior]
                kdp = Kdp[tip_layer.soil_type]

                # Hitung NSPT rata-rata di sekitar ujung tiang
                n_avg = compute_nspt_average(z, diameter_m, segs)
                if n_avg is None:
                    # Tidak ada data cukup di 4D atas/bawah
                    qb_kPa = np.nan
                else:
                    qb_kPa = alpha * kdp * n_avg

                qb_kN = qb_kPa * ab_m2

            # Mayerhof
            if method =="Mayerhof":
                if tip_layer.soil_behavior == "clay":
                    if tip_layer.su is not None:
                        qb_kPa = 9 * tip_layer.su
                        qb_kN = qb_kPa * ab_m2
                    else:
                        qb_kPa = 0.0
                        qb_kN = 0.0
                elif tip_layer.soil_behavior == "sand":
                    # Mayerhof method for sand requires Nq from phi
                    # For now, placeholder - needs full implementation
                    if tip_layer.phi <= 42:
                        f_qb = (280.19 * tip_layer.phi) - 7845.177
                    else:
                        f_qb = (280.19 * 42) - 7845.177
                    qb_kPa = f_qb
                    qb_kN = qb_kPa * ab_m2
                else:
                    qb_kPa = 0.0
                    qb_kN = 0.0


        # Qfs Calculation (exclude part above cutoff)
        qs_sum_kN = 0.0
        sum_sigma_eff: Optional[float] = 0.0
        for z_top, lyr in segs:
            z_bot = z_top + lyr.thickness_m
            overlap = max(0.0, min(z_bot, z) - z_top)
            if method == "Mayerhof":
                if overlap > 0 and hasattr(lyr, "gamma_eff"):
                    sum_sigma_eff += lyr.gamma_eff * overlap

            # hanya hitung bagian yang berada DI BAWAH cutoff
            effective_layer_top = max(z_top, cutoff_m)
            effective_layer_bot = min(z_bot, z)  # hanya sampai kedalaman z
            overlap = max(0.0, effective_layer_bot - effective_layer_top)

            if overlap <= 0.0:
                continue

            if lyr.soil_behavior in ["clay", "silt", "sand"]:
                # Decourt Quaresma
                if method == "Decourt-Quaresma":
                    beta = PileData_beta[pile_type][lyr.soil_behavior]
                    qs_kPa = beta * 10 * ((lyr.nspt / 3) + 1)
                    qs_sum_kN += qs_kPa * perim_m * overlap

                # Mayerhof
                elif method == "Mayerhof":
                    if lyr.soil_behavior == "clay":
                        if lyr.alpha_tomlinson is not None and lyr.su is not None:
                            qs_kPa = lyr.alpha_tomlinson * lyr.su
                            qs_sum_kN += qs_kPa * perim_m * overlap
                    elif lyr.soil_behavior == "sand":
                        # For sand in Mayerhof, need to compute from phi and gamma_eff
                        # This will be implemented based on Mayerhof's formula
                        if pile_material == "Steel":
                            delta=20
                            if lyr.phi > 45: 
                                ks=1
                            ks=0.029412*lyr.phi-0.32353
                        elif pile_material == "Concrete":
                            delta=(3/4)*lyr.phi
                            if lyr.phi > 45: 
                                ks=2
                            ks=0.029412*lyr.phi+0.67647059
                        elif pile_material == "Timber":
                            delta=(2/3)*lyr.phi
                            if lyr.phi > 45: 
                                ks=4
                            ks=0.1470588*lyr.phi-2.6176470588
                        # else:
                        #     delta = 0.75 * lyr.phi
                        #     ks=1
                        # gunakan sum_sigma_eff sampai kedalaman z (sudah dihitung di atas)
                        qs_kPa = ks * sum_sigma_eff * tan(delta * np.pi / 180.0)  # tan expects radians
                        qs_sum_kN += qs_kPa * perim_m * overlap
        
        # Decourt Quaresma
        if method =="Decourt-Quaresma":
            alpha=PileData_alpha[pile_type][tip_layer.soil_behavior]
            alpha_vals[i]=alpha         

            beta=PileData_beta[pile_type][tip_layer.soil_behavior]
            beta_vals[i]=beta

            kdp=Kdp[tip_layer.soil_type]
            kdp_vals[i]=kdp
        
            soiltype_vals[i]=tip_layer.soil_type
        
        # Mayerhof
        if method =="Mayerhof":
            alpha_vals[i]=tip_layer.alpha_tomlinson if tip_layer.alpha_tomlinson is not None else 0.0
            su_vals[i]=tip_layer.su if tip_layer.su is not None else 0.0
            # ks_vals[i]=ks if ks is not None else 0.0
            sum_sigma_eff_vals[i]=sum_sigma_eff
        # else:
        #     # Ensure arrays stay defined for Decourt-Quaresma path
        #     ks_vals[i]=0.0
        #     sum_sigma_eff_vals[i]=0.0

        soil_vals[i]=tip_layer.soil_behavior
        qs_vals[i] = qs_sum_kN
        qb_vals[i] = qb_kN
        qult_vals[i] = qb_vals[i] + qs_vals[i]
        qall_vals[i] = qult_vals[i] / fs
        
    # Decourt Quaresma
    if method =="Decourt-Quaresma":
        df = pd.DataFrame(
            {
                "Depth_m": z_vals,
                "Soil Behavior": soil_vals,
                "Soil Type": soiltype_vals,
                "Alpha": alpha_vals,
                "Beta": beta_vals,
                "kdp_kPa": kdp_vals,
                "Qb_kN": qb_vals,
                "Qfs_kN": qs_vals,
                "Qult_kN": qult_vals,
                "Qall_kN": qall_vals,
            }
        )

    # Mayerhof
    if method =="Mayerhof":
        df = pd.DataFrame(
            {
                "Depth_m": z_vals,
                "Soil Behavior": soil_vals,
                "Alpha": alpha_vals,
                "Su_kPa": su_vals,
                # "Ks":ks_vals,
                "Sigma_eff_kPa": sum_sigma_eff_vals,
                "Qb_kN": qb_vals,
                "Qfs_kN": qs_vals,
                "Qult_kN": qult_vals,
                "Qall_kN": qall_vals,
            }
        )

    cols = ["Qb_kN", "Qfs_kN", "Qult_kN", "Qall_kN"]
    df[cols] = df[cols].round(2)

    recap = {
        "Ab_m2": ab_m2,
        "Perimeter_m": perim_m,
        "Depth_m": pile_depth_m,
        "Cutoff_m": cutoff_m,
        "Pilelength_m": pilelength_m,
        "FS": fs,
        "Qb_at_tip_kN": float(qb_vals[-1]),
        "Qfs_total_kN": float(qs_vals[-1]),
        "Qult_total_kN": float(qult_vals[-1]),
        "Qall_total_kN": float(qall_vals[-1]),
    }
    return df, recap



