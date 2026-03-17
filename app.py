import streamlit as st
from fpdf import FPDF

st.set_page_config(page_title="Simulador Llamedo Propiedades", page_icon="🏠")

# --- FUNCIÓN PARA GENERAR PDF CORREGIDA ---
def generar_pdf(datos, rol, total_final, mni_ref):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    
    # Encabezado con el nombre de tu oficina
    pdf.cell(200, 10, txt="Llamedo Propiedades - Simulación de Gastos", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(200, 10, txt="Operación Inmobiliaria CABA 2026", ln=True, align="C")
    pdf.ln(10)
    
    # Resumen de Operación
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt=f"Resumen para el {rol}", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, txt=f"Precio Real de Transacción: USD {datos['p_real']:,.2f}", ln=True)
    pdf.cell(0, 8, txt=f"Precio de Escrituración: USD {datos['p_esc']:,.2f}", ln=True)
    pdf.ln(5)
    
    # Tabla de Gastos
    pdf.set_font("Arial", "B", 11)
    pdf.cell(70, 10, "Concepto", 1)
    pdf.cell(60, 10, "Monto (USD)", 1)
    pdf.cell(60, 10, "Observación", 1)
    pdf.ln()
    
    pdf.set_font("Arial", "", 10)
    for item in datos['detalle']:
        pdf.cell(70, 8, item[0], 1)
        pdf.cell(60, 8, item[1], 1)
        pdf.cell(60, 8, item[2], 1)
        pdf.ln()
    
    pdf.ln(10)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, txt=f"TOTAL FINAL ESTIMADO: USD {total_final:,.2f}", ln=True)
    
    # Descargo de Responsabilidad solicitado
    pdf.ln(20)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 5, txt="ACLARACIÓN: Los valores aquí expresados son aproximados y de carácter meramente informativo. "
                             "Los valores definitivos surgirán de las proformas oficiales de los correspondientes escribanos intervinientes "
                             "y la liquidación final de impuestos.")
    
    # EL TRUCO: Convertir explícitamente a bytes
    return bytes(pdf.output())

# --- INTERFAZ STREAMLIT ---
st.title("🏠 Simulador Inmobiliario")

with st.sidebar:
    st.header("Parámetros")
    tc = st.number_input("Dólar (ARS)", value=1415)
    mni_pesos = st.number_input("Tope Exención Sellos (ARS)", value=226100000)

col1, col2 = st.columns(2)
with col1:
    rol = st.selectbox("Parte Interesada", ["Vendedor", "Comprador"])
    p_real = st.number_input("Precio Real (USD)", value=100000)
    com_pct = st.number_input("% Comisión", value=3.0)
with col2:
    tipo_op = st.selectbox("Tipo de Vivienda", ["Primera Vivienda", "Segunda Vivienda", "Inversión"])
    p_esc = st.number_input("Precio Escritura (USD)", value=80000)
    esc_pct = st.number_input("% Honorarios Escribanía", value=2.0)

# Cálculos de Honorarios + IVA (21%)
comision = p_real * (com_pct / 100)
iva_com = comision * 0.21
hono_esc = p_esc * (esc_pct / 100)
iva_esc = hono_esc * 0.21

# Lógica de Sellos CABA 2026 (Compartido 50/50)
p_esc_pesos = p_esc * tc
if tipo_op == "Primera Vivienda":
    sellos_tot = max(0, (p_esc_pesos - mni_pesos) * 0.035)
elif tipo_op == "Segunda Vivienda":
    sellos_tot = (min(p_esc_pesos, mni_pesos) * 0.027) + (max(0, p_esc_pesos - mni_pesos) * 0.035)
else:
    sellos_tot = p_esc_pesos * 0.035
sellos_usd = (sellos_tot / 2) / tc

total_gastos = comision + iva_com + hono_esc + iva_esc + sellos_usd
monto_final = (p_real - total_gastos) if rol == "Vendedor" else (p_real + total_gastos)

st.divider()

# Preparar datos para el PDF
datos_pdf = {
    'p_real': p_real,
    'p_esc': p_esc,
    'detalle': [
        ["Comisión Inmob.", f"{comision:,.2f}", "Sobre Real"],
        ["IVA s/Comisión", f"{iva_com:,.2f}", "Profesional"],
        ["Hono. Escribano", f"{hono_esc:,.2f}", "Sobre Escritura"],
        ["IVA s/Escribano", f"{iva_esc:,.2f}", "Profesional"],
        ["Sellos (50%)", f"{sellos_usd:,.2f}", "CABA 2026"]
    ]
}

# Generar el archivo en bytes
try:
    pdf_bytes = generar_pdf(datos_pdf, rol, monto_final, mni_pesos)

    st.download_button(
        label="📩 Descargar Simulación en PDF",
        data=pdf_bytes,
        file_name=f"Simulacion_Llamedo_{rol.lower()}.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"Hubo un problema al generar el PDF: {e}")
