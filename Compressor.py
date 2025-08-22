#!/usr/bin/env python
# coding: utf-8

# In[1]:


# pm_compaction_app.py
# Streamlit app: PM uniaxial compaction tonnage calculator
# Run: streamlit run pm_compaction_app.py

import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import io
import csv
from datetime import datetime

# --- Constants ---
N_PER_TONF = 9806.65          # 1 metric ton-force = 9806.65 N
MPA_TO_PA = 1e6

# Default material database (example values)
DEFAULT_MATERIALS = {
    "Tungsten Carbide (WC-Co, example)": {
        "K": 1.96e-3, "A0": 0.357, "rho_theoretical": 15500
    },
    "Iron (Fe, example)": {
        "K": 2.10e-3, "A0": 0.25, "rho_theoretical": 7870
    },
    "Custom (enter your constants)": {
        "K": None, "A0": None, "rho_theoretical": None
    }
}

st.set_page_config(page_title="PM Compaction Tonnage", layout="wide")
st.title("Powder Metallurgy — Uniaxial Compaction Tonnage Calculator")
st.markdown(
    "Estimate the press tonnage required to reach a target green density using the **Heckel equation** "
    "for uniaxial compaction. All units are auto-handled."
)

# -----------------------
# Sidebar: material & constants
# -----------------------
st.sidebar.header("Material & Constants")
material_choice = st.sidebar.selectbox("Material", list(DEFAULT_MATERIALS.keys()))

mat_defaults = DEFAULT_MATERIALS[material_choice]
K_default = mat_defaults["K"] if mat_defaults["K"] else 1.5e-3
A0_default = mat_defaults["A0"] if mat_defaults["A0"] else 0.30
rho_th_default = mat_defaults["rho_theoretical"] if mat_defaults["rho_theoretical"] else 8000.0

K = st.sidebar.number_input("K (MPa⁻¹)", value=float(K_default), format="%.6e", step=1e-4)
A0 = st.sidebar.number_input("A₀", value=float(A0_default), format="%.6f", step=0.01)
rho_theoretical = st.sidebar.number_input("ρ_th (kg/m³)", value=float(rho_th_default), step=10.0)

st.sidebar.markdown(
    "Heckel: `ln(1/(1-D)) = K·P + A₀` → `P = (ln(1/(1-D)) - A₀)/K` (P in MPa)."
)

# -----------------------
# Inputs
# -----------------------
st.header("Part geometry & density input")
col1, col2 = st.columns(2)

with col1:
    shape = st.selectbox("Part shape", ["Solid Cylinder", "Hollow Cylinder"])
    outer_d_mm = st.number_input("Outer diameter (mm)", min_value=0.1, value=10.0, step=0.1)
    inner_d_mm = st.number_input("Inner diameter (mm)", min_value=0.0, value=5.0, step=0.1) if shape == "Hollow Cylinder" else 0.0

with col2:
    dens_type = st.selectbox("Density input", ["Green density (kg/m³)", "Relative density D"])
    if dens_type == "Green density (kg/m³)":
        rho_green = st.number_input("ρ_green (kg/m³)", min_value=1.0, value=10000.0, step=100.0)
        D = rho_green / rho_theoretical
    else:
        D = st.number_input("Relative density D", min_value=0.01, max_value=0.999, value=0.65, step=0.01)

SF = st.number_input("Safety factor", min_value=1.0, max_value=3.0, value=1.2, step=0.05)

# -----------------------
# Computations
# -----------------------
log_term = np.log(1.0 / (1.0 - D))
P_MPa = (log_term - A0) / K
area_m2 = (np.pi / 4.0) * ((outer_d_mm**2 - inner_d_mm**2) * 1e-6)
F_N = P_MPa * MPA_TO_PA * area_m2
tons_no_SF = F_N / N_PER_TONF
tons_with_SF = tons_no_SF * SF

# -----------------------
# Results
# -----------------------
st.header("Results")
st.latex(r"\ln\left(\tfrac{1}{1-D}\right) = K \cdot P + A_0")
st.latex(r"P = \tfrac{\ln(1/(1-D)) - A_0}{K} \quad (MPa)")
st.latex(r"F = P \cdot 10^6 \cdot A \quad (N)")
st.latex(r"T = \tfrac{F}{9806.65} \times SF \quad (tons)")

st.write(f"**Relative density (D):** {D:.4f}")
st.write(f"**Compaction pressure (P):** {P_MPa:,.2f} MPa")
st.write(f"**Projected area (A):** {area_m2:.6e} m²")
st.write(f"**Compaction force (F):** {F_N:,.0f} N")
st.write(f"**Tonnage (no SF):** {tons_no_SF:,.3f} t")
st.write(f"**Tonnage (with SF={SF}):** {tons_with_SF:,.3f} t")

# -----------------------
# Plots
# -----------------------
st.header("Plots")
D_vals = np.linspace(0.05, 0.95, 300)
P_vals = (np.log(1.0 / (1.0 - D_vals)) - A0) / K
T_vals = (P_vals * MPA_TO_PA * area_m2 / N_PER_TONF) * SF

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4))
ax1.plot(D_vals, P_vals); ax1.axvline(D, color="red", ls="--")
ax1.set_xlabel("Relative density D"); ax1.set_ylabel("Pressure (MPa)")
ax1.set_title("Pressure vs Density")

ax2.plot(D_vals, T_vals); ax2.axvline(D, color="red", ls="--")
ax2.set_xlabel("Relative density D"); ax2.set_ylabel("Tonnage (t)")
ax2.set_title("Tonnage vs Density")

st.pyplot(fig)

# -----------------------
# Download
# -----------------------
csv_buffer = io.StringIO()
writer = csv.writer(csv_buffer)
writer.writerow(["Material", material_choice])
writer.writerow(["K (MPa^-1)", K]); writer.writerow(["A0", A0])
writer.writerow(["ρ_th (kg/m³)", rho_theoretical])
writer.writerow(["Relative density D", D])
writer.writerow(["Outer diameter (mm)", outer_d_mm])
writer.writerow(["Inner diameter (mm)", inner_d_mm])
writer.writerow(["Pressure (MPa)", P_MPa])
writer.writerow(["Force (N)", F_N])
writer.writerow(["Tons (with SF)", tons_with_SF])
csv_data = csv_buffer.getvalue().encode("utf-8")

st.download_button("Download results CSV", data=csv_data, file_name="results.csv", mime="text/csv")


# In[ ]:




