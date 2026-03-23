import streamlit as st
import requests
from fpdf import FPDF
import urllib3

# Desactivar advertencias de certificados del BCRA
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 1. FUNCIÓN DE CONEXIÓN AL BCRA (BLINDADA CONTRA ERRORES DE LLAVE)
def obtener_dolar_bcra():
    fallback_val = 1414.02
    fallback_fecha = "20/03/2026"
    try:
        url = "https://api.bcra.gob.ar/estadisticas/v4.0/monetarias/4"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json'
        }
        response = requests.get(url, headers=headers, verify=False, timeout=10)
        if response.status_code == 200:
            datos = response.json()
            if 'results' in datos and len(datos['results']) > 0:
                ultimo = datos['results'][-1]
                if 'valor' in ultimo:
                    return float(ultimo['valor']), ultimo.get('fecha', fallback_fecha), "Conexión Exitosa"
                else:
                    return fallback_val, fallback_fecha, "BCRA: Dato no disponible"
            else:
                return fallback_val, fallback_fecha, "BCRA: Sin datos para hoy"
    except Exception:
        return fallback_val, fallback_fecha, "BCRA: Error de conexión"
    return fallback_val, fallback_fecha, "BCRA: Error desconocido"

# 2. CONFIGURACIÓN E IDENTIDAD VISUAL (BLINDAJE TOTAL CONTRA DARK MODE)
st.set_page_config(page_title="Simulador Llamedo - Profesional", page_icon="🏠")

if 'mostrar_caso_b' not in st.session_state:
    st.session_state.mostrar_caso_b = False

st.markdown("""
    <style>
    /* 1. Fondo e Identidad General */
    .stApp { background-color: #F9F7F2 !important; }
    h1, h2, h3, label, .stMarkdown p { color: #0B3D2E !important; font-family: 'Georgia', serif; }
    
    /* 2. Barra Lateral (Siempre Verde) */
    [data-testid="stSidebar"] { background-color: #0B3D2E !important; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] p { color: white !important; }
    
    /* 3. BLINDAJE DE INPUTS (Para que no desaparezca el valor del dólar) */
    input { 
        color: #0B3D2E !important; 
        background-color: white !important; 
        -webkit-text-fill-color: #0B3D2E !important; 
    }
    /* Asegura que incluso deshabilitado se vea oscuro */
    input:disabled { 
        opacity: 1 !important; 
        -webkit-text-fill-color: #0B3D2E !important; 
    }

    /* 4. BLINDAJE DE MÉTRICAS (Para que no desaparezca el Neto a Recibir) */
    [data-testid="stMetricValue"] > div { color: #0B3D2E !important; }
    [data-testid="stMetricLabel"] > div { color: #0B3D2E !important; }
    
    /* 5. Tablas de Desglose */
    [data-testid="stTable"] { background-color: white !important; border-radius: 8px; }
    [data-testid="stTable"] td, [data-testid="stTable"] th { 
        color: #0B3D2E !important; 
        background-color: white !important; 
    }
    
    /* 6. Botones */
    .stButton>button { background-color: #0B3D2E; color: white !important; border-radius: 4px; font-weight: bold; }
    .stMetric { background-color: #ffffff; border-left: 5px solid #0B3D2E; padding: 20px; border-radius: 8px; border: 1px solid #E0DED7; }
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
    return {
        'comision': comision, 'iva_com': iva_com, 'hono_esc': hono_esc, 
        'iva_esc': iva_esc, 'sellos': sellos_parte_usd, 
        'total_gastos': comision + iva_com + hono_esc + iva_esc + sellos_parte_usd
    }

# 4. DISCLAIMER LEGAL EN CADA HOJA DEL PDF
def agregar_disclaimer(pdf):
    pdf.set_y(250)
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, "DOCUMENTO NO VINCULANTE", ln=True, align="C")
    pdf.set_font("Helvetica", "I", 7)
    pdf.multi_cell(0, 3, txt="Esta simulación se emite con fines orientativos. Los valores definitivos surgirán de las proformas oficiales de los escribanos y liquidaciones de impuestos vigentes al momento de la firma.", align="C")

# 5. GENERACIÓN DE PDF MULTI-PÁGINA
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
        pdf.ln(8); pdf.set_font("Helvetica", "B", 9); pdf.set_fill_color(245, 243, 235)
        pdf.cell(85, 9, " Concepto", 1, 0, 'L', True); pdf.cell(45, 9, "Monto (USD)", 1, 0, 'C', True); pdf.cell(60, 9, " Base Imponible", 1, 1, 'L', True)
        pdf.set_font("Helvetica", "", 9)
        items = [["Comisión Inmob.", f"{caso['res']['comision']:,.2f}", f"{caso['com_pct']}% s/ Real"], ["IVA s/ Comisión", f"{caso['res']['iva_com']:,.2f}", "21% Profesional"], ["Honorarios Escribanía", f"{caso['res']['hono_esc']:,.2f}", f"{caso['esc_pct']}% s/ Escritura"], ["IVA s/ Escribanía", f"{caso['res']['iva_esc']:,.2f}", "21% Profesional"], ["Impuesto Sellos (50%)", f"{caso['res']['sellos']:,.2f}", "CABA 2026"]]
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
    val_bcra, fecha_bcra, estado_bcra = obtener_dolar_bcra()
    st.caption(f"Status: {estado_bcra} ({fecha_bcra})")
    tc = st.number_input("Valor USD", value=val_bcra, disabled=(fuente=="Oficial BCRA"))
    mni = st.number_input("Tope Sellos CABA (ARS)", value=226100000)

# ESCENARIO A
st.header("📍 Escenario A")
dir_a = st.text_input("Dirección (A)", "Propiedad Ejemplo")
col_a1, col_a2 = st.columns(2)
rol_a = col_a1.selectbox("Rol (A)", ["Vendedor", "Comprador"])
p_real_a = col_a1.number_input("Precio Real (A)", value=100000.0)
com_a = col_a1.number_input("% Comisión (A)", value=3.0)
tipo_a = col_a2.selectbox("Tipo (A)", ["Primera Vivienda", "Segunda Vivienda", "Inversion"])
p_esc_a = col_a2.number_input("Precio Escritura (A)", value=80000.0)
esc_a = col_a2.number_input("% Escribano (A)", value=2.0)

res_a = calcular_operacion(p_real_a, p_esc_a, com_a, esc_a, tipo_a, tc, mni)
final_a = (p_real_a - res_a['total_gastos']) if rol_a == "Vendedor" else (p_real_a + res_a['total_gastos'])

with st.expander("🔍 Ver desglose Escenario A", expanded=True):
    st.table({"Concepto": ["Comisión", "IVA Com.", "Escribanía", "IVA Esc.", "Sellos (50%)"], "USD": [f"{res_a['comision']:,.2f}", f"{res_a['iva_com']:,.2f}", f"{res_a['hono_esc']:,.2f}", f"{res_a['iva_esc']:,.2f}", f"{res_a['sellos']:,.2f}"]})
    st.metric(f"Neto A", f"USD {final_a:,.2f}")

if not st.session_state.mostrar_caso_b:
    if st.button("➕ Comparar con Escenario B"):
        st.session_state.mostrar_caso_b = True; st.rerun()

lista_casos = [{'nombre': 'A', 'rol': rol_a, 'p_real': p_real_a, 'p_esc': p_esc_a, 'tipo': tipo_a, 'direccion': dir_a, 'com_pct': com_a, 'esc_pct': esc_a, 'res': res_a}]

if st.session_state.mostrar_caso_b:
    st.divider(); st.header("📍 Escenario B")
    dir_b = st.text_input("Dirección (B)", dir_a)
    col_b1, col_b2 = st.columns(2)
    rol_b = col_b1.selectbox("Rol (B)", ["Vendedor", "Comprador"])
    p_real_b = col_b1.number_input("Precio Real (B)", value=p_real_a)
    com_b = col_b1.number_input("% Comisión (B)", value=com_a)
    tipo_b = col_b2.selectbox("Tipo (B)", ["Primera Vivienda", "Segunda Vivienda", "Inversion"], index=1)
    p_esc_b = col_b2.number_input("Precio Escritura (B)", value=p_esc_a)
    esc_b = col_b2.number_input("% Escribano (B)", value=esc_a)
    
    res_b = calcular_operacion(p_real_b, p_esc_b, com_b, esc_b, tipo_b, tc, mni)
    final_b = (p_real_b - res_b['total_gastos']) if rol_b == "Vendedor" else (p_real_b + res_b['total_gastos'])
    lista_casos.append({'nombre': 'B', 'rol': rol_b, 'p_real': p_real_b, 'p_esc': p_esc_b, 'tipo': tipo_b, 'direccion': dir_b, 'com_pct': com_b, 'esc_pct': esc_b, 'res': res_b})
    
    with st.expander("🔍 Ver desglose Escenario B", expanded=True):
        st.table({"Concepto": ["Comisión", "IVA Com.", "Escribanía", "IVA Esc.", "Sellos (50%)"], "USD": [f"{res_b['comision']:,.2f}", f"{res_b['iva_com']:,.2f}", f"{res_b['hono_esc']:,.2f}", f"{res_b['iva_esc']:,.2f}", f"{res_b['sellos']:,.2f}"]})
        st.metric("Neto B", f"USD {final_b:,.2f}")
    if st.button("🗑️ Eliminar Escenario B"):
        st.session_state.mostrar_caso_b = False; st.rerun()

st.divider()
st.download_button("📄 Descargar Informe Comparativo (PDF)", generar_pdf_comparativo(lista_casos, tc, mni), "Simulacion_Llamedo.pdf", "application/pdf")
