import streamlit as st
import requests
from fpdf import FPDF

# 1. FUNCIÓN DE CONEXIÓN AL BCRA (Dólar Oficial)
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

# 2. CONFIGURACIÓN E IDENTIDAD VISUAL (FORZADO PARA DARK MODE)
st.set_page_config(page_title="Simulador Llamedo - Profesional", page_icon="🏠")

if 'mostrar_caso_b' not in st.session_state:
    st.session_state.mostrar_caso_b = False

st.markdown("""
    <style>
    .stApp { background-color: #F9F7F2 !important; }
    h1, h2, h3, label, .stMarkdown p { color: #0B3D2E !important; font-family: 'Georgia', serif; }
    [data-testid="stSidebar"] { background-color: #0B3D2E !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] p { color: white !important; }
    input, div[data-baseweb="select"] > div { background-color: white !important; color: #0B3D2E !important; }
    .stButton>button { background-color: #0B3D2E; color: white !important; border-radius: 4px; font-weight: bold; width: 100%; }
    .stMetric { background-color: #ffffff; border-left: 5px solid #0B3D2E; padding: 20px; border-radius: 8px; border: 1px solid #E0DED7; }
    /* Estilo para las tablas de vista previa */
    .stTable { background-color: white; border-radius: 8px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# 3. LÓGICA DE CÁLCULO
def calcular_operacion(p_real, p_esc, com_pct, esc_pct, tipo, tc, mni):
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

    sellos_parte_usd = (sellos_tot / 2) / tc
    total_gastos = comision + iva_com + hono_esc + iva_esc + sellos_parte_usd
    return {
        'comision': comision, 'iva_com': iva_com, 
        'hono_esc': hono_esc, 'iva_esc': iva_esc, 
        'sellos': sellos_parte_usd, 'total_gastos': total_gastos
    }

# 4. FUNCIÓN PARA EL DISCLAIMER EN CADA HOJA DEL PDF
def agregar_disclaimer(pdf):
    pdf.set_y(250)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "DOCUMENTO NO VINCULANTE", ln=True, align="C")
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 3, txt="Esta simulación se emite con fines orientativos e informativos. No constituye una oferta, compromiso ni asesoramiento profesional. Los valores definitivos surgirán de las proformas oficiales de los escribanos y de las liquidaciones finales de impuestos vigentes al momento de la firma.", align="C")

# 5. GENERACIÓN DE PDF
def generar_pdf_comparativo(casos, tc, mni_val):
    pdf = FPDF()
    for caso in casos:
        pdf.add_page()
        pdf.set_fill_color(11, 61, 46); pdf.rect(0, 0, 210, 45, 'F')
        try: pdf.image("logo_completo.png", x=65, y=5, w=80)
        except: pdf.text(65, 25, "LLAMEDO PROPIEDADES")
        pdf.set_y(55); pdf.set_text_color(11, 61, 46); pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"ESCENARIO {caso['nombre']} - PARTE {caso['rol'].upper()}", ln=True, align="C")
        pdf.ln(5); pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"Referencia: {caso['direccion']}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Precio Real: USD {caso['p_real']:,.2f} | Precio Escritura: USD {caso['p_esc']:,.2f}", ln=True)
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(245, 243, 235)
        pdf.cell(85, 9, " Concepto", 1, 0, 'L', True); pdf.cell(45, 9, "Monto (USD)", 1, 0, 'C', True); pdf.cell(60, 9, " Base Imponible", 1, 1, 'L', True)
        pdf.set_font("Helvetica", "", 9)
        items = [["Honorarios Inmobiliarios", f"{caso['res']['comision']:,.2f}", "Valor Real"], ["IVA s/ Honorarios", f"{caso['res']['iva_com']:,.2f}", "21% Profesional"], ["Honorarios Escribanía", f"{caso['res']['hono_esc']:,.2f}", "Valor Escritura"], ["IVA s/ Escribanía", f"{caso['res']['iva_esc']:,.2f}", "21% Profesional"], ["Impuesto Sellos (50%)", f"{caso['res']['sellos']:,.2f}", "Ley CABA 2026"]]
        for item in items:
            pdf.cell(85, 8, f" {item[0]}", 1); pdf.cell(45, 8, item[1], 1, 0, 'R'); pdf.cell(60, 8, f" {item[2]}", 1, 1)
        pdf.ln(8); pdf.set_font("Helvetica", "B", 12); pdf.set_text_color(11, 61, 46)
        final_val = (caso['p_real'] - caso['res']['total_gastos']) if caso['rol'] == "Vendedor" else (caso['p_real'] + caso['res']['total_gastos'])
        pdf.cell(0, 10, f"TOTAL ESTIMADO: USD {final_val:,.2f}", ln=True, align="R")
        agregar_disclaimer(pdf)
    if len(casos) > 1:
        pdf.add_page(); pdf.set_fill_color(11, 61, 46); pdf.rect(0, 0, 210, 45, 'F')
        try: pdf.image("logo_completo.png", x=65, y=5, w=80) 
        except: pass
        pdf.set_y(55); pdf.set_text_color(11, 61, 46); pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 15, "RESUMEN COMPARATIVO", ln=True, align="C"); pdf.ln(10)
        pdf.set_font("Helvetica", "B", 10); pdf.set_fill_color(245, 243, 235)
        pdf.cell(70, 12, "Concepto", 1, 0, 'C', True); pdf.cell(60, 12, "ESCENARIO A", 1, 0, 'C', True); pdf.cell(60, 12, "ESCENARIO B", 1, 1, 'C', True)
        pdf.set_font("Helvetica", "", 10); pdf.set_text_color(0, 0, 0)
        val_a = (casos[0]['p_real'] - casos[0]['res']['total_gastos']) if casos[0]['rol'] == "Vendedor" else (casos[0]['p_real'] + casos[0]['res']['total_gastos'])
        val_b = (casos[1]['p_real'] - casos[1]['res']['total_gastos']) if casos[1]['rol'] == "Vendedor" else (casos[1]['p_real'] + casos[1]['res']['total_gastos'])
        filas = [["Precio Real (USD)", f"{casos[0]['p_real']:,.2f}", f"{casos[1]['p_real']:,.2f}"], ["Categoría", casos[0]['tipo'], casos[1]['tipo']], ["RESULTADO FINAL", f"USD {val_a:,.2f}", f"USD {val_b:,.2f}"]]
        for i, fila in enumerate(filas):
            if i == len(filas) - 1: pdf.set_font("Helvetica", "B", 10); pdf.set_text_color(11, 61, 46)
            pdf.cell(70, 10, fila[0], 1); pdf.cell(60, 10, fila[1], 1, 0, 'C'); pdf.cell(60, 10, fila[2], 1, 1, 'C')
        agregar_disclaimer(pdf)
    return bytes(pdf.output())

# 6. INTERFAZ
st.title("💼 Simulador de Operaciones")

with st.sidebar:
    st.image("logo_completo.png", use_container_width=True)
    st.markdown("---")
    fuente = st.radio("Cotización:", ["Oficial BCRA", "Manual"])
    val_bcra, _ = obtener_dolar_bcra()
    tc = st.number_input("Valor USD", value=val_bcra, disabled=(fuente=="Oficial BCRA"))
    mni = st.number_input("Tope Sellos CABA (ARS)", value=226100000)

# ESCENARIO A
st.header("📍 Escenario A")
dir_a = st.text_input("Dirección (A)", "Propiedad Ejemplo")
col_a1, col_a2 = st.columns(2)
rol_a = col_a1.selectbox("Rol (A)", ["Vendedor", "Comprador"])
p_real_a = col_a1.number_input("Precio Real (A)", value=100000.0)
tipo_a = col_a2.selectbox("Tipo (A)", ["Primera Vivienda", "Segunda Vivienda", "Inversion"])
p_esc_a = col_a2.number_input("Precio Escritura (A)", value=80000.0)

res_a = calcular_operacion(p_real_a, p_esc_a, 3.0, 2.0, tipo_a, tc, mni)
final_a = (p_real_a - res_a['total_gastos']) if rol_a == "Vendedor" else (p_real_a + res_a['total_gastos'])

# CUADRO DE VISTA PREVIA (CASO A)
with st.expander("🔍 Ver desglose de gastos Escenario A", expanded=True):
    st.table({
        "Concepto": ["Comisión", "IVA s/ Com.", "Escribanía", "IVA s/ Esc.", "Sellos (50%)"],
        "Monto USD": [f"{res_a['comision']:,.2f}", f"{res_a['iva_com']:,.2f}", f"{res_a['hono_esc']:,.2f}", f"{res_a['iva_esc']:,.2f}", f"{res_a['sellos']:,.2f}"]
    })
    st.metric(f"Neto estimado ({rol_a})", f"USD {final_a:,.2f}")

# ESCENARIO B
if not st.session_state.mostrar_caso_b:
    if st.button("➕ Comparar con Escenario B"):
        st.session_state.mostrar_caso_b = True; st.rerun()

lista_casos = [{'nombre': 'A', 'rol': rol_a, 'p_real': p_real_a, 'p_esc': p_esc_a, 'tipo': tipo_a, 'direccion': dir_a, 'res': res_a}]

if st.session_state.mostrar_caso_b:
    st.divider(); st.header("📍 Escenario B")
    dir_b = st.text_input("Dirección (B)", dir_a)
    col_b1, col_b2 = st.columns(2)
    rol_b = col_b1.selectbox("Rol (B)", ["Vendedor", "Comprador"])
    p_real_b = col_b1.number_input("Precio Real (B)", value=p_real_a)
    tipo_b = col_b2.selectbox("Tipo (B)", ["Primera Vivienda", "Segunda Vivienda", "Inversion"], index=1)
    p_esc_b = col_b2.number_input("Precio Escritura (B)", value=p_esc_a)
    
    res_b = calcular_operacion(p_real_b, p_esc_b, 3.0, 2.0, tipo_b, tc, mni)
    final_b = (p_real_b - res_b['total_gastos']) if rol_b == "Vendedor" else (p_real_b + res_b['total_gastos'])
    lista_casos.append({'nombre': 'B', 'rol': rol_b, 'p_real': p_real_b, 'p_esc': p_esc_b, 'tipo': tipo_b, 'direccion': dir_b, 'res': res_b})
    
    # CUADRO DE VISTA PREVIA (CASO B)
    with st.expander("🔍 Ver desglose de gastos Escenario B", expanded=True):
        st.table({
            "Concepto": ["Comisión", "IVA s/ Com.", "Escribanía", "IVA s/ Esc.", "Sellos (50%)"],
            "Monto USD": [f"{res_b['comision']:,.2f}", f"{res_b['iva_com']:,.2f}", f"{res_b['hono_esc']:,.2f}", f"{res_b['iva_esc']:,.2f}", f"{res_b['sellos']:,.2f}"]
        })
        st.metric(f"Neto estimado ({rol_b})", f"USD {final_b:,.2f}")

    if st.button("🗑️ Eliminar Escenario B"):
        st.session_state.mostrar_caso_b = False; st.rerun()

st.divider()
st.download_button("📄 Descargar Informe Comparativo Completo (PDF)", generar_pdf_comparativo(lista_casos, tc, mni), "Simulacion_Llamedo.pdf", "application/pdf")
