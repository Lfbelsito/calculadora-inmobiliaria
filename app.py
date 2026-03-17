import streamlit as st

st.set_page_config(page_title="Simulador Llamedo Propiedades", page_icon="🏠")

st.title("🏠 Calculadora Inmobiliaria CABA 2026")
st.info("Configuración técnica: Honorarios + IVA + Sellos compartidos")

# --- BARRA LATERAL ---
with st.sidebar:
    st.header("Parámetros de Mercado")
    tc = st.number_input("Cotización Dólar (ARS)", value=1415)
    mni_pesos = st.number_input("Tope Exención Sellos (ARS)", value=226100000)

# --- ENTRADAS ---
col1, col2 = st.columns(2)

with col1:
    rol = st.selectbox("Parte a calcular", ["Vendedor", "Comprador"])
    p_real_usd = st.number_input("Precio Real (USD)", value=100000)
    com_pct = st.number_input("% Comisión Inmobiliaria", value=3.0)

with col2:
    tipo_op = st.selectbox("Categoría Propiedad", 
                          ["Primera Vivienda (Exenta)", "Segunda Vivienda (Reducida)", "Inversión / Otros"])
    p_esc_usd = st.number_input("Precio Escrituración (USD)", value=80000)
    esc_pct = st.number_input("% Honorarios Escribano", value=2.0)

# --- CÁLCULOS PROFESIONALES + IVA ---
# Inmobiliaria
comision_usd = p_real_usd * (com_pct / 100)
iva_comision_usd = comision_usd * 0.21

# Escribanía
honorarios_esc_usd = p_esc_usd * (esc_pct / 100)
iva_escribano_usd = honorarios_esc_usd * 0.21

# --- CÁLCULO DE SELLOS (50/50) ---
p_esc_pesos = p_esc_usd * tc
if tipo_op == "Primera Vivienda (Exenta)":
    excedente = max(0, p_esc_pesos - mni_pesos)
    total_sellos_pesos = excedente * 0.035
elif tipo_op == "Segunda Vivienda (Reducida)":
    dentro_tope = min(p_esc_pesos, mni_pesos)
    excedente = max(0, p_esc_pesos - mni_pesos)
    total_sellos_pesos = (dentro_tope * 0.027) + (excedente * 0.035)
else:
    total_sellos_pesos = p_esc_pesos * 0.035

sellos_parte_usd = (total_sellos_pesos / 2) / tc

# --- GRAN TOTAL ---
gastos_totales_usd = comision_usd + iva_comision_usd + honorarios_esc_usd + iva_escribano_usd + sellos_parte_usd

# --- RESULTADOS ---
st.divider()
if rol == "Vendedor":
    resultado = p_real_usd - gastos_totales_usd
    st.subheader(f"💰 Neto a recibir: USD {resultado:,.2f}")
else:
    resultado = p_real_usd + gastos_totales_usd
    st.subheader(f"💸 Total a desembolsar: USD {resultado:,.2f}")

st.table({
    "Concepto": ["Comisión Inmobiliaria", "IVA s/ Comisión (21%)", "Honorarios Escribano", "IVA s/ Escribano (21%)", "Impuesto Sellos (50%)"],
    "Monto (USD)": [
        f"{comision_usd:,.2f}", 
        f"{iva_comision_usd:,.2f}", 
        f"{honorarios_esc_usd:,.2f}", 
        f"{iva_escribano_usd:,.2f}", 
        f"{sellos_parte_usd:,.2f}"
    ],
    "Detalle": ["Sobre Valor Real", "Profesional", "Sobre Escritura", "Profesional", "CABA 2026"]
})
