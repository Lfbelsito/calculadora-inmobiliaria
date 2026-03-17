import streamlit as st

st.set_page_config(page_title="Calculadora Llamedo", page_icon="🏠")

st.title("🏠 Simulador de Gastos Inmobiliarios")
st.write("Herramienta exclusiva para la gestión de operaciones.")

# --- ENTRADAS ---
with st.sidebar:
    st.header("Configuración")
    tc = st.number_input("Tipo de Cambio (ARS)", value=1415)
    mni = st.number_input("MNI Sellos CABA (USD)", value=65000)

col1, col2 = st.columns(2)

with col1:
    rol = st.selectbox("Parte Interesada", ["Vendedor", "Comprador"])
    p_real = st.number_input("Precio Real de Transacción (USD)", value=100000)
    comision_pct = st.number_input("% Comisión Inmobiliaria", value=3.0)

with col2:
    vivienda = st.selectbox("Tipo de Vivienda", ["Única y Permanente", "Segunda / Inversión"])
    p_escritura = st.number_input("Precio de Escrituración (USD)", value=70000)
    escribania_pct = st.number_input("% Gastos Escribanía", value=2.0)

# --- LÓGICA DE SELLOS 2026 ---
def calc_sellos(precio, mni_val, tipo):
    if tipo == "Única y Permanente":
        return max(0, (precio - mni_val) * 0.035)
    else:
        # 2,7% hasta el tope, 3,5% sobre el excedente
        if precio <= mni_val:
            return precio * 0.027
        else:
            return (mni_val * 0.027) + ((precio - mni_val) * 0.035)

sellos = calc_sellos(p_escritura, mni, vivienda)
comision = p_real * (comision_pct / 100)
escribania = p_escritura * (escribania_pct / 100)
iva_ars = (comision * tc) * 0.21

total_gastos = sellos + comision + escribania

# --- RESULTADOS ---
st.divider()
if rol == "Vendedor":
    resultado = p_real - total_gastos
    st.metric("Neto a Recibir", f"USD {resultado:,.0f}")
else:
    resultado = p_real + total_gastos
    st.metric("Total a Desembolsar", f"USD {resultado:,.0f}")

st.table({
    "Concepto": ["Comisión", "Sellos (CABA 2026)", "Escribanía", "IVA (en ARS)"],
    "Monto": [f"USD {comision:,.2f}", f"USD {sellos:,.2f}", f"USD {escribania:,.2f}", f"$ {iva_ars:,.0f}"]
})
