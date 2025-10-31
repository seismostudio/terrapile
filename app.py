from typing import List

import streamlit as st

from axpile.models import PileData_alpha, SoilLayer, validate_inputs, SoilBehavior, SoilType, Method
from axpile.calc import compute_distributions
from axpile.plots import plot_depth_vs_components, plot_depth_vs_qall, plot_soil_profile, plot_pilecap_layout
from axpile.geometry import (
    compute_pile_perimeter_m_from_diameter,
    compute_pile_tip_area_m2_from_diameter
)

def main() -> None:
    st.set_page_config(page_title="Dahar AxPile", layout="wide")
    st.title("Calculate Axial Bearing Capacity")
    st.caption("Unit: kPa, m, kN.")

    tab1, tab2 = st.tabs(["Single Pile Analysis","Group Pile Analysis"])
    with tab1:
        pile = list (PileData_alpha.keys())

        with st.sidebar:

            st.header("Analysis Method")
            method = st.selectbox(
                "Method",
                options=Method
            )
            fs = st.number_input("Safety Factor (FS)", min_value=0.0, format="%.1f")

            if method == "Decourt-Quaresma" or method =="Mayerhof":
                st.header("Pile Input")
                diameter_m = st.number_input("Pile Diameter (m)", min_value=0.0, format="%.3f")
                # share pile diameter across tabs
                st.session_state["pile_diameter_m"] = diameter_m
                pile_depth_m = st.number_input("Depth of Pile (m)", min_value=0.0, format="%.2f")
                cutoff_m= st.number_input("Cut-Off Pile (m)", min_value=0.0, format="%.2f")
                if method=="Decourt-Quaresma":
                    pile_types = st.selectbox(
                        "Pile Type",
                        pile
                    )
                if method == "Mayerhof":
                    pile_material = st.selectbox(
                        "Pile Material",
                        options=(
                            "Steel","Concrete","Timber"
                        )
                    )
                    if pile_material == "Concrete":
                        pile_types = st.selectbox(
                            "Pile Type",
                            options=(
                                "Driven Pile","Bored Pile"
                            )
                        )
                    else:
                        pile_types="Driven Pile"

                dz=st.number_input("Vertical Increment", min_value = 0.05, format ="%.2f" )
            else:
                st.header("Pile Input")
                st.subheader("Coming Soon, Under Developement..")
            
        #INPUT
        if method=="Decourt-Quaresma" or method == "Mayerhof":

            with st.expander("Soil Layer Along Pile Shaft", expanded=True):
                st.caption(f"Analysis Method: {method}")


                n_layers = st.number_input("Number of Layer", min_value=0, step=1)

                layers: List[SoilLayer] = []
                for i in range(int(n_layers)):
                    with st.expander(f"Layer #{i+1}", expanded=True):
                        col1, col2, col3, col4= st.columns(4)
                        thickness = col1.number_input(
                            f"Thickness #{i+1} (m)", min_value=0.0, format="%.1f", key=f"th_{i}"
                        )

                        # DECOURT-QUARESMA METHOD INPUT
                        if method=="Decourt-Quaresma":
                            soil_behavior = col2.selectbox(
                                f"Soil Behavior #{i+1}", options=SoilBehavior, key=f"behavior_{i}"
                            )                
                            soil_type = col3.selectbox(
                                f"Soil Type #{i+1}", options=SoilType[soil_behavior], key=f"type_{i}"
                            )
                            if soil_behavior == "clay":
                                nspt=col4.number_input(
                                    f"NSPT #{i+1}", min_value=1, key=f"nspt_{i}"
                                )
                                layers.append(
                                    SoilLayer(
                                        thickness_m=thickness,
                                        soil_behavior=soil_behavior,
                                        soil_type=soil_type,
                                        nspt=nspt
                                    )
                                )
                            if soil_behavior =="silt":
                                nspt=col4.number_input(
                                    f"NSPT #{i+1}", min_value=1, key=f"nspt_{i}"
                                )
                                layers.append(
                                    SoilLayer(
                                        thickness_m=thickness,
                                        soil_behavior=soil_behavior,
                                        soil_type=soil_type,
                                        nspt=nspt
                                    )
                                )
                            if soil_behavior =="sand":
                                nspt=col4.number_input(
                                    f"NSPT #{i+1}", min_value=1, key=f"nspt_{i}"
                                )
                                layers.append(
                                    SoilLayer(
                                        thickness_m=thickness,
                                        soil_behavior=soil_behavior,
                                        soil_type=soil_type,
                                        nspt=nspt
                                    )
                                )

                        # MAYERHOF METHOD INPUT
                        if method=="Mayerhof":
                            soil_behavior = col2.selectbox(
                                f"Soil Behavior #{i+1}", options=("clay","sand"), key=f"behavior_{i}"
                            )
                            if soil_behavior == "clay":
                                su=col3.number_input(
                                    f"Su #{i+1} (kPa)", min_value=0.0, format="%.2f", key=f"su_{i}"
                                )
                                alpha=col4.number_input(
                                    f"Adhesive Factor, Alpha #{i+1}", min_value=0.0, format="%.2f", key=f"alpha_{i}"
                                )
                                gamma_eff=col1.number_input(
                                    f"Effective Unit Weight #{i+1} (kN/m3)", min_value=0, key=f"gamma'_{i}"
                                )
                                layers.append(
                                    SoilLayer(
                                        thickness_m=thickness,
                                        soil_behavior=soil_behavior,
                                        soil_type=soil_behavior,
                                        su=su,
                                        alpha_tomlinson=alpha,
                                        gamma_eff=gamma_eff
                                    )
                                )  
                            if soil_behavior == "sand":
                                gamma_eff=col3.number_input(
                                    f"Effective Unit Weight #{i+1} (kN/m3)", min_value=0, key=f"gamma'_{i}"
                                )
                                phi=col4.number_input(
                                    f"Friction Angle #{i+1} (degree)", min_value=0, key=f"phi_{i}"
                                )
                                layers.append(
                                    SoilLayer(
                                        thickness_m=thickness,
                                        soil_behavior=soil_behavior,
                                        soil_type=soil_behavior,
                                        gamma_eff=gamma_eff,
                                        phi=phi
                                    )
                                )
            st.divider()
            run = st.button("Run")

            if run:
                try:
                    # Initialize pile_material for Decourt-Quaresma (not used but needed for function call)
                    if method == "Decourt-Quaresma":
                        pile_material = None
                    
                    validate_inputs(method, diameter_m, pile_depth_m, cutoff_m, fs, dz, layers)
                    df, recap = compute_distributions(method, diameter_m, pile_depth_m, cutoff_m, fs, pile_material, pile_types, dz, layers)
                    # simpan hasil single-pile agar persisten antar rerun
                    st.session_state["single_df"] = df
                    st.session_state["single_recap"] = recap


                    st.subheader("Summary")
                    colA, colB, colC, colD = st.columns(4)
                    colA.metric("Ab (m²)", f"{recap['Ab_m2']:.4f}")
                    colA.metric("Perimeter (m)", f"{recap['Perimeter_m']:.3f}")
                    colB.metric("Pile Length (m)", f"{recap['Pilelength_m']:.2f}")            
                    colB.metric("Cut-off Pile (m)", f"{recap['Cutoff_m']:.2f}")
                    colC.metric("Qb @tip (kN)", f"{recap['Qb_at_tip_kN']:.1f}")
                    colC.metric("Qfs total (kN)", f"{recap['Qfs_total_kN']:.1f}")
                    colD.metric("Qult total (kN)", f"{recap['Qult_total_kN']:.1f}")
                    colD.metric("Qall total (kN)", f"{recap['Qall_total_kN']:.1f}")

                    col1A, col2A = st.columns(2)
                    plot_height = 800
                    with col1A:
                        st.subheader("Depth vs Qall")
                        fig1 = plot_depth_vs_qall(df)
                        fig1.update_layout(height=plot_height)
                        st.plotly_chart(fig1, width="stretch")

                        st.subheader("Depth vs Qfs, Qb, Qult, Qall")
                        fig2 = plot_depth_vs_components(df)
                        fig2.update_layout(height=plot_height)
                        st.plotly_chart(fig2, width="stretch")

                    with col2A:
                        st.subheader("Soil Profile")
                        fig3 = plot_soil_profile(layers, pile_depth_m, cutoff_m)
                        fig3.update_layout(height=plot_height)
                        st.plotly_chart(fig3, width="stretch")

                        st.subheader("Summary Data")
                        st.dataframe(df, width="stretch", height=800)
                except Exception as exc:
                    st.error(str(exc))

        else:
            st.subheader(f"Coming Soon, {method}'s Method is Under Developement..")

    with tab2:
        st.caption("Group Pile Analysis")
        col1, col2, col3, col4 = st.columns(4)
        spacing = col1.number_input("Spacing (m)", min_value=0.0, format="%.2f", key="spacing")

        n_group = st.number_input("Number of Groups", min_value=1, step=1, key="n_groups")
        for g in range(1, int(n_group) + 1):
            with st.expander(f"Group #{g}", expanded=True):
                col1, col2, col3 = st.columns(3)
                n_pile = col1.number_input("Number of Piles", min_value=1, step=1, key=f"n_pile_{g}")
                w_pilecap = col2.number_input("Width of PileCap", min_value=0.0, format="%.2f", key=f"w_pilecap_{g}")
                l_pilecap = col3.number_input("Length of PileCap", min_value=0.0, format="%.2f", key=f"l_pilecap_{g}")
                import pandas as pd
                state_key = f"group_{g}_df"
                if state_key not in st.session_state:
                    st.session_state[state_key] = pd.DataFrame({
                        "Pile Number": list(range(1, int(n_pile) + 1)),
                        "X (m)": [0.0] * int(n_pile),
                        "Y (m)": [0.0] * int(n_pile),
                    })
                else:
                    df = st.session_state[state_key]
                    current_rows = len(df)
                    target_rows = int(n_pile)
                    if target_rows != current_rows:
                        new_df = pd.DataFrame({
                            "Pile Number": list(range(1, target_rows + 1)),
                            "X (m)": [0.0] * target_rows,
                            "Y (m)": [0.0] * target_rows,
                        })
                        rows_to_copy = min(current_rows, target_rows)
                        if rows_to_copy > 0:
                            new_df.loc[:rows_to_copy - 1, ["X (m)", "Y (m)"]] = df.loc[:rows_to_copy - 1, ["X (m)", "Y (m)"]].values
                        st.session_state[state_key] = new_df

                df_to_edit = st.session_state[state_key]
                edited = st.data_editor(
                    df_to_edit,
                    num_rows="fixed",
                    use_container_width=True,
                    column_config={
                        "Pile Number": st.column_config.NumberColumn(disabled=True),
                        "X (m)": st.column_config.NumberColumn(format="%.3f"),
                        "Y (m)": st.column_config.NumberColumn(format="%.3f"),
                    },
                    key=f"editor_group_{g}",
                )
                st.session_state[state_key] = edited
                
                # Visualization below the table
                st.subheader("Pilecap Layout")
                fig_layout = plot_pilecap_layout(
                    edited,
                    width_m=st.session_state.get(f"w_pilecap_{g}", 0.0),
                    length_m=st.session_state.get(f"l_pilecap_{g}", 0.0),
                    pile_diameter_m=st.session_state.get("pile_diameter_m", 0.0),
                )
                st.plotly_chart(fig_layout, width="stretch")

        # --- PILE GROUP EFFICIENCY CALCULATION ---
        st.divider()
        if st.button("Calculate Pile Efficiency", key="calc_eff_all"):
            try:
                import math
                import pandas as pd
                # Jalankan ulang single pile analysis (kalau belum ada di session_state)
                if "single_recap" not in st.session_state or "single_df" not in st.session_state:
                    if method == "Decourt-Quaresma":
                        pile_material = None
                    validate_inputs(method, diameter_m, pile_depth_m, cutoff_m, fs, dz, layers)
                    df, recap = compute_distributions(method, diameter_m, pile_depth_m, cutoff_m, fs, pile_material, pile_types, dz, layers)
                    st.session_state["single_df"] = df
                    st.session_state["single_recap"] = recap
                else:
                    recap = st.session_state["single_recap"]

                Qall_single = recap["Qall_total_kN"]
                d = st.session_state.get("pile_diameter_m", 0.0)
                s = st.session_state.get("spacing", 0.0)

                if d <= 0 or s <= 0:
                    st.error("Please input valid pile diameter and spacing before calculation.")
                else:
                    results =[]
                    with st.expander ("Pile Group Summary", expanded=True):
                        st.caption("Converse – Labarre Method")
                        for g in range(1, int(n_group) + 1):
                            
                                edited = st.session_state.get(f"group_{g}_df", None)
                                n_pile = st.session_state.get(f"n_pile_{g}", 0)

                                if edited is None or n_pile == 0:
                                    st.warning(f"Group #{g} data is incomplete.")
                                    continue

                                # Hitung parameter dasar
                                alpha_deg = math.degrees(math.atan(d / s))
                                n_cols = len(edited["X (m)"].unique())
                                n_rows = len(edited["Y (m)"].unique())

                                # Efisiensi kelompok
                                η = 1 - (alpha_deg * ((n_cols - 1) * n_rows + (n_rows - 1) * n_cols)) / (90 * n_rows * n_cols)
                                η = max(0, η)

                                # Kapasitas total
                                Qgroup_effsingle = η * Qall_single
                                Qgroup_eff = η * Qall_single * int(n_pile)

                                # Simpan ke list hasil
                                results.append({
                                    "Group": g,
                                    "Rows (m)": n_rows,
                                    "Columns (n)": n_cols,
                                    "α (deg)": round(alpha_deg, 2),
                                    "η (Efficiency)": round(η, 3),
                                    "Single Pile, Qall (kN)": round(Qall_single, 1),
                                    "Single Pile After Efficiency, Qall (kN)": round(Qgroup_effsingle, 1),
                                    "Total Piles": int(n_pile),
                                    "Group, Qall (kN)": round(Qgroup_eff, 1)
                                })

                                # Tampilkan hasil per group
                                st.subheader(f"Group #{g} Efficiency Summary")
                                colA, colB, colC, colD = st.columns(4)
                                colA.metric("Rows (m)", f"{n_rows}")
                                colA.metric("Columns (n)", f"{n_cols}")
                                colB.metric("α (deg)", f"{alpha_deg:.2f}")
                                colB.metric("η (Efficiency)", f"{η:.3f}")
                                colC.metric("Single Pile, Qall (kN)", f"{Qall_single:.1f}")
                                colC.metric("Total Piles", f"{int(n_pile)}")
                                colD.metric("Single Pile After Efficiency, Qall (kN)", f"{Qgroup_effsingle:.1f}")
                                colD.metric("Group, Qall (kN)", f"{Qgroup_eff:.1f}")

                    # Setelah semua group dihitung, ubah ke DataFrame dan tampilkan
                    if results:
                        df_result = pd.DataFrame(results)
                        st.subheader("Pile Group Efficiency Summary Table")
                        st.dataframe(df_result, use_container_width=True)

            except Exception as e:
                st.error(f"Error calculating efficiency: {e}")


if __name__ == "__main__":
    main()


