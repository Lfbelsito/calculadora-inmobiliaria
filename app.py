import streamlit as st
import requests
from fpdf import FPDF

# 1. FUNCIÓN DE CONEXIÓN AL BCRA (ID 4 - MINORISTA VENDEDOR)
def obtener_dolar_bcra():
    try:
        url = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/4"
        headers = {'User-Agent': 'Mozilla/5.0'} 
        response = requests.get(url, headers=headers, verify=False, timeout=8)
        if response.status_code == 200:
            datos = response.json()
            ultimo = datos['results'][-1]
            return float(ultimo['valor']), ultimo['fecha']
    except Exception:
        return 1414.02, "20/03/2026" 
    return 1414.02, "20/03/2026"

# 2. CONFIGURACIÓN E IDENTIDAD VISUAL LLAMEDO PROPIEDADES
st.set_page_config(page_title="Llamedo Propiedades - Simulador", page_icon="🏠")

# --- CSS MEJORADO PARA VISIBILIDAD TOTAL ---
st.markdown("""
    <style>
    /* Fondo general en tono Crema suave */
    .stApp { background-color: #F9F7F2; }
    
    /* Títulos en Verde Oscuro */
    h1, h2, h3 { color: #0B3D2E !important; font-family: 'Georgia', serif; }
    
    /* Sidebar en Verde Oscuro */
    [data-testid="stSidebar"] { background-color: #0B3D2E; }
    
    /* TODO el texto de la barra lateral en blanco (etiquetas, radio buttons, captions) */
    [data-testid="stSidebar"] label, 
    [data-testid="stSidebar"] .stCaption, 
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div[data-testid="stMarkdownContainer"] p { 
        color: white !important; 
    }
    
    /* TEXTO DENTRO DE LOS INPUTS (Verde oscuro sobre fondo blanco) */
    [data-testid="stSidebar"] input { 
        color: #0B3D2E !important; 
        background-color: white !important;
        -webkit-text-fill-color: #0B3D2E !important;
    }
    
    /* Estilo específico para input deshabilitado */
    [data-testid="stSidebar"] .stNumberInput div[data-baseweb="input"] input:disabled {
        opacity: 0.9;
    }

    /* Botón de descarga en Verde Llamedo */
    .stButton>button { 
        background-color: #0B3D2E; 
        color: white !important; 
        border-radius: 4px; 
        font-weight: bold;
        width: 100%;
        border: none;
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

# 3. GENERACIÓN DE PDF PROFESIONAL (DISEÑO LIMPIO)
def generar_pdf(datos, rol, total_final, mni_val):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_fill_color(11, 61, 46) 
    pdf.rect(0, 0, 210, 45, 'F') 
    try:
        pdf.image("logo_completo.png", x=65, y=5, w=80) 
    except:
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 16)
        pdf.text(65, 25, "LLAMEDO PROPIEDADES")

    pdf.set_y(55) 
    pdf.set_text_color(11, 61, 46)
    pdf.set_font("Helvetica", "B", 12)
    pdf.cell(0, 10, f"SIMULACIÓN DE GASTOS ESTIMADOS - PARTE {rol.upper()}", ln=True, align="C")
    pdf.ln(5)
    
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, f"Referencia: {datos['direccion']} {datos['unidad']}", ln=True)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, f"Valor Real de Transacción: USD {datos['p_real']:,.2f}", ln=True)
    pdf.cell(0, 6, f"Valor de Escrituración: USD {datos['p_esc']:,.2f}", ln=True)
    pdf.ln(8)
    
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(245, 243, 235) 
    pdf.cell(85, 9, " Concepto", 1, 0, 'L', True)
    pdf.cell(45, 9, "Monto (USD)", 1, 0, 'C', True)
    pdf.cell(60, 9, " Base Imponible", 1, 1, 'L', True)
    
    pdf.set_font("Helvetica", "", 9)
    for item in datos['detalle']:
        pdf.cell(85, 8, f" {item[0]}", 1)
        pdf.cell(45, 8, f"{item[1]}", 1, 0, 'R')
        pdf.cell(60, 8, f" {item[2]}", 1, 1)
    
    pdf.ln(8)
    pdf.set_font("Helvetica", "B", 11)
    pdf.set_text_color(11, 61, 46)
    label = "NETO A RECIBIR" if rol == "Vendedor" else "TOTAL A DESEMBOLSAR"
    pdf.cell(0, 10, f"{label}: USD {total_final:,.2f}", ln=True, align="R")
    
    pdf.set_y(245)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "DOCUMENTO NO VINCULANTE", ln=True, align="C")
    pdf.set_font("Helvetica", "I", 8)
    pdf.multi_cell(0, 4, txt="Esta simulación se emite con fines orientativos. "
                             "Los valores definitivos surgirán de las proformas oficiales de los escribanos "
                             "intervinientes y de las liquidaciones finales de impuestos vigentes al momento de la firma.", 
                   align="C")
    return bytes(pdf.output())

# 4. LÓGICA DE INTERFAZ
st.title("💼 Simulador de Gastos")

# Sidebar: Control de Cotización
with st.sidebar:
    try:
        st.image("logo_completo.png", use_container_width=True)
    except:
        pass
    st.markdown("---")
    
    # Fuente del Dólar
    fuente_dolar = st.radio("Fuente del Tipo de Cambio:", ["Oficial BCRA", "Manual / Especulativo"])
    
    val_bcra, fecha_bcra = obtener_dolar_bcra()
    
    if fuente_dolar == "Oficial BCRA":
        st.caption(f"Última actualización: {fecha_bcra}")
        tc = st.number_input("Dólar (ARS)", value=val_bcra, disabled=True)
    else:
        st.caption("Modo edición manual habilitado")
        tc = st.number_input("Dólar (ARS)", value=val_bcra, disabled=False, step=1.0)
    
    mni = st.number_input("Tope Sellos CABA (ARS)", value=226100000)

# Inputs de la Propiedad
st.subheader("Datos de la Operación")
c_p1, c_p2 = st.columns([3, 1])
with c_p1:
    direccion = st.text_input("Ubicación", "Propiedad en CABA")
with c_p2:
    unidad = st.text_input("Unidad", "Piso/Depto")

col1, col2 = st.columns(2)
with col1:
    rol = st.selectbox("Perfil del Cliente", ["Vendedor", "Comprador"])
    p_real = st.number_input("Precio Real (USD)", value=100000.0)
    com_pct = st.number_input("% Honorarios Inmob.", value=3.0)
with col2:
    tipo = st.selectbox("Categoría del Inmueble", ["Primera Vivienda", "Segunda Vivienda", "Inversión"])
    p_esc = st.number_input("Precio de Escrituración (USD)", value=80000.0)
    esc_pct = st.number_input("% Honorarios Escribano", value=2.0)

# Cálculos Finales
comision = p_real * (com_pct / 100)
iva_com = comision * 0.21
hono_esc = p_esc * (esc_pct / 100)
iva_esc = hono_esc * 0.21
p_esc_pesos = p_esc * tc

# Lógica Sellos CABA 2026
if tipo == "Primera Vivienda":
    sellos_tot = max(0, (p_esc_pesos - mni) * 0.035)
elif tipo == "Segunda Vivienda":
    sellos_tot = (min(p_esc_pesos, mni) * 0.027) + (max(0, p_esc_pesos - mni) * 0.035)
else:
    sellos_tot = p_esc_pesos * 0.035

sellos_parte_usd = (sellos_tot / 2) / tc
total_gastos = comision + iva_com + hono_esc + iva_esc + sellos_parte_usd
resultado = (p_real - total_gastos) if rol == "Vendedor" else (p_real + total_gastos)

st.divider()
st.metric(f"RESULTADO ESTIMADO PARA {rol.upper()}", f"USD {resultado:,.2f}")

# Datos para el PDF
datos_pdf = {
    'direccion': direccion, 'unidad': unidad,
    'p_real': p_real, 'p_esc': p_esc,
    'detalle': [
        ["Honorarios Inmobiliarios", f"{comision:,.2f}", "Sobre Valor Real"],
        ["IVA s/ Honorarios (21%)", f"{iva_com:,.2f}", "Servicio Profesional"],
        ["Honorarios Escribanía", f"{hono_esc:,.2f}", "Sobre Escrituración"],
        ["IVA s/ Escribanía (21%)", f"{iva_esc:,.2f}", "Servicio Profesional"],
        ["Impuesto de Sellos (50%)", f"{sellos_parte_usd:,.2f}", "Normativa CABA 2026"]
    ]
}

try:
    pdf_bytes = generar_pdf(datos_pdf, rol, resultado, mni)
    st.download_button(
        label="📄 DESCARGAR SIMULACIÓN EN PDF",
        data=pdf_bytes,
        file_name=f"Simulacion_Gastos_{rol}.pdf",
        mime="application/pdf"
    )
except Exception as e:
    st.error(f"Error técnico: {e}")
