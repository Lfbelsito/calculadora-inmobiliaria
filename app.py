import streamlit as st
from fpdf import FPDF

# Configuración de página
st.set_page_config(page_title="Llamedo Propiedades - Gestión", page_icon="🏠")

# --- CSS PERSONALIZADO (CORREGIDO) ---
st.markdown("""
    <style>
    /* Fondo general en tono Crema */
    .stApp { background-color: #F9F7F2; }
    
    /* Títulos en Verde Oscuro */
    h1, h2, h3 { color: #0B3D2E !important; font-family: 'Georgia', serif; }
    
    /* Sidebar en Verde Oscuro */
    [data-testid="stSidebar"] { background-color: #0B3D2E; }
    
    /* Etiquetas de la barra lateral en blanco */
    [data-testid="stSidebar"] label { color: white !important; }
    
    /* TEXTO DENTRO DE LOS INPUTS (La corrección técnica) */
    [data-testid="stSidebar"] input { 
        color: #0B3D2E !important; /* Verde oscuro para que se vea sobre el fondo blanco del cuadro */
        background-color: white !important;
    }

    /* Botón de descarga en Verde Llamedo */
    .stButton>button { 
        background-color: #0B3D2E; 
        color: white !important; 
        border-radius: 4px; 
        border: 1px solid #0B3D2E;
        font-weight: bold;
    }
    
    /* Tarjetas de métricas */
    [data-testid="stMetric"] {
        background-color: #ffffff;
        border-left: 5px solid #0B3D2E;
        padding: 20px;
        border-radius: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- EL RESTO DEL CÓDIGO SE MANTIENE IGUAL ---

def generar_pdf(datos, rol, total_final):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(11, 61, 46) 
    pdf.rect(0, 0, 210, 45, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Arial", "B", 20)
    pdf.cell(0, 25, "LLAMEDO PROPIEDADES", ln=True, align="C")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 5, "Servicios Inmobiliarios Profesionales", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(25)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"INFORME DE GASTOS ESTIMADOS - PARTE {rol.upper()}", ln=True)
    pdf.ln(5)
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Valor Real de la Operacion: USD {datos['p_real']:,.2f}", ln=True)
    pdf.cell(0, 8, f"Valor de Escrituracion: USD {datos['p_esc']:,.2f}", ln=True)
    pdf.ln(10)
    pdf.set_font("Arial", "B", 10)
    pdf.set_fill_color(245, 245, 220) 
    pdf.cell(85, 10, "Concepto", 1, 0, 'C', True)
    pdf.cell(45, 10, "Monto (USD)", 1, 0, 'C', True)
    pdf.cell(60, 10, "Base Imponible", 1, 1, 'C', True)
    pdf.set_font("Arial", "", 10)
    for item in datos['detalle']:
        pdf.cell(85, 8, item[0], 1)
        pdf.cell(45, 8, f"USD {item[1]}", 1, 0, 'R')
        pdf.cell(60, 8, item[2], 1)
        pdf.ln()
    pdf.ln(10)
    pdf.set_font("Arial", "B", 14)
    pdf.set_text_color(11, 61, 46)
    label = "NETO A RECIBIR" if rol == "Vendedor" else "TOTAL A DESEMBOLSAR"
    pdf.cell(0, 10, f"{label}: USD {total_final:,.2f}", ln=True, align="R")
    pdf.ln(30)
    pdf.set_font("Arial", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, txt="Nota: Esta simulacion es orientativa. Los valores definitivos seran "
                             "proporcionados por el escribano designado mediante las proformas correspondientes "
                             "previo al acto de escrituracion.")
    return bytes(pdf.output())

st.title("💼 Simulador de Operaciones")

with st.sidebar:
    st.markdown("### Configuración")
    tc = st.number_input("Dólar (ARS)", value=1415)
    mni = st.number_input("Tope Sellos CABA (ARS)", value=226100000)
    st.markdown("---")
    st.write("Llamedo Propiedades")

c1, c2 = st.columns(2)
with c1:
    rol = st.selectbox("Perfil del Cliente", ["Vendedor", "Comprador"])
    p_real = st.number_input("Precio Transacción (USD)", value=100000)
    com_pct = st.number_input("% Comisión", value=3.0)
with c2:
    tipo = st.selectbox("Categoría Inmueble", ["Primera Vivienda", "Segunda Vivienda", "Inversión"])
    p_esc = st.number_input("Precio Escritura (USD)", value=80000)
    esc_pct = st.number_input("% Honorarios Escribanía", value=2.0)

comision = p_real * (com_pct / 100)
iva_com = comision * 0.21
hono_esc = p_esc * (esc_pct / 100)
iva_esc = hono_esc * 0.21
p_esc_pesos = p_esc * tc
if tipo == "Primera Vivienda":
    sellos_tot = max(0, (p_esc_pesos - mni) * 0.035)
elif tipo == "Segunda Vivienda":
    sellos_tot = (min(p_esc_pesos, mni) * 0.027) + (max(0, p_esc_pesos - mni) * 0.035)
else:
    sellos_tot = p_esc_pesos * 0.035
sellos_usd = (sellos_tot / 2) / tc
total_gastos = comision + iva_com + hono_esc + iva_esc + sellos_usd
final = (p_real - total_gastos) if rol == "Vendedor" else (p_real + total_gastos)

st.divider()
st.metric(f"RESULTADO PARA EL {rol.upper()}", f"USD {final:,.2f}")

datos_pdf = {
    'p_real': p_real, 'p_esc': p_esc,
    'detalle': [
        ["Comisión Inmobiliaria", f"{comision:,.2f}", "Sobre Precio Real"],
        ["IVA sobre Comisión", f"{iva_com:,.2f}", "21% Profesional"],
        ["Honorarios Escribano", f"{hono_esc:,.2f}", "Sobre Escrituración"],
        ["IVA sobre Escribanía", f"{iva_esc:,.2f}", "21% Profesional"],
        ["Impuesto Sellos (50%)", f"{sellos_usd:,.2f}", "Ley CABA 2026"]
    ]
}

pdf_bytes = generar_pdf(datos_pdf, rol, final)
st.download_button(
    label="📄 DESCARGAR INFORME PROFESIONAL",
    data=pdf_bytes,
    file_name=f"Informe_Llamedo_{rol}.pdf",
    mime="application/pdf"
)
