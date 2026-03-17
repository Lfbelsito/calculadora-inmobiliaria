import streamlit as st

st.set_page_config(page_title="Simulador Llamedo Propiedades", page_icon="🏠")

st.title("🏠 Calculadora Inmobiliaria CABA 2026")
st.markdown("---")

# --- BARRA LATERAL: AJUSTES DE LEY ---
with st.sidebar:
    st.header("Parámetros de Ley")
    tc = st.number_input("Cotización Dólar (ARS)", value=1415)
    # MNI según tu dato: 226.100.000 ARS
    mni_pesos = st.number_input("Toque Exención (Pesos ARS)", value=226100000, step=1000000)

# --- ENTRADAS DE LA OPERACIÓN ---
col1, col2 = st.columns(2)

with col1:
    rol = st.selectbox("Parte que calculamos", ["Vendedor", "Comprador"])
    p_real_usd = st.number_input("Precio Real de Transacción (USD)", value=100000)
    comision_pct = st.number_input("% Comisión Inmobiliaria", value=3.0)

with col2:
    tipo_op = st.selectbox("Categoría de la Propiedad", 
                          ["Primera Vivienda (Exenta)", 
                           "Segunda Vivienda (Reducida)", 
                           "Inversión / Otros (Total)"])
    p_esc_usd = st.number_input("Precio de Escrituración (USD)", value=80000)
    escribania_pct = st.number_input("% Gastos Escribanía (Tasa/Aportes)", value=2.0)

# --- CÁLCULO DE SELLOS (LÓGICA 2026) ---
p_esc_pesos = p_esc_usd * tc
total_sellos_pesos = 0

if tipo_op == "Primera Vivienda (Exenta)":
    # 0% hasta el tope, 3.5% sobre el excedente
    excedente = max(0, p_esc_pesos - mni_pesos)
    total_sellos_pesos = excedente * 0.035

elif tipo_op == "Segunda Vivienda (Reducida)":
    # 2.7% hasta el tope, 3.5% sobre el excedente
    dentro_del_tope = min(p_esc_pesos, mni_pesos)
    excedente = max(0, p_esc_pesos - mni_pesos)
    total_sellos_pesos = (dentro_del_tope * 0.027) + (excedente * 0.035)

else: # Inversión / Otros
    # 3.5% parejo sobre el total
    total_sellos_pesos = p_esc_pesos * 0.035

# El impuesto se divide entre las dos partes
sellos_parte_usd = (total_sellos_pesos / 2) / tc

# --- OTROS GASTOS ---
comision_usd = p_real_usd * (comision_pct / 100)
iva_comision_ars = (comision_usd * tc) * 0.21
escribania_usd = p_esc_usd * (escribania_pct / 100)

gastos_totales_usd = comision_usd + sellos_parte_usd + escribania_usd

# --- RESULTADOS FINALES ---
st.markdown("---")
st.subheader(f"Resumen Estimado para {rol}")

if rol == "Vendedor":
    final = p_real_usd - gastos_totales_usd
    st.metric("Neto a Cobrar", f"USD {final:,.0f}")
else:
    final = p_real_usd + gastos_totales_usd
    st.metric("Total a Desembolsar", f"USD {final:,.0f}")

st.table({
    "Concepto": ["Comisión Inmob.", "Impuesto Sellos (50%)", "Escribanía", "IVA s/ Comisión"],
    "Base Usada": ["Precio Real", "Precio Escritura", "Precio Escritura", "Comisión"],
    "Monto (USD)": [f"USD {comision_usd:,.2f}", f"USD {sellos_parte_usd:,.2f}", f"USD {escribania_usd:,.2f}", "-"],
    "Monto (ARS)": ["-", f"$ {total_sellos_pesos/2:,.0f}", "-", f"$ {iva_comision_ars:,.0f}"]
})
