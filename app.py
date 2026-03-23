import streamlit as st
import requests
from fpdf import FPDF

# 1. FUNCIÓN DE CONEXIÓN AL BCRA
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

# 2. CONFIGURACIÓN E IDENTIDAD VISUAL
st.set_page_config(page_title="Simulador Comparativo Llamedo", page_icon="🏠")

if 'mostrar_caso_b' not in st.session_state:
    st.session_state.mostrar_caso_b = False

st.markdown("""
    <style>
    .stApp { background-color: #F9F7F2; }
    h1, h2, h3 { color: #0B3D2E !important; font-family: 'Georgia', serif; }
    [data-testid="stSidebar"] { background-color: #0B3D2E; }
    [data-testid="stSidebar"] label, [data-testid="stSidebar"] .stCaption, [data-testid="stSidebar"] p { color: white !important; }
    [data-testid="stSidebar"] input { color: #0B3D2E !important; background-color: white !important; }
    .stButton>button { background-color: #0B3D2E; color: white !important; border-radius: 4px; font-weight: bold; width: 100%; }
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
    total_gastos = comision + iva_com + hono_esc + iva_esc + sellos_parte_usd
    return {
        'comision': comision, 'iva_com': iva_com, 
        'hono_esc': hono_esc, 'iva_esc': iva_esc, 
        'sellos': sellos_parte_usd, 'total_gastos': total_gastos
    }

# 4. GENERACIÓN DE PDF MULTI-PÁGINA CON RESUMEN COMPARATIVO
def generar_pdf_comparativo(casos, tc, mni_val):
    pdf = FPDF()
    
    # Páginas de Detalle (Caso A y Caso B)
    for caso in casos:
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
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, f"ESCENARIO {caso['nombre']} - PARTE {caso['rol'].upper()}", ln=True, align="C")
        pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 6, f"Referencia: {caso['direccion']} {caso['unidad']}", ln=True)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, f"Precio Real: USD {caso['p_real']:,.2f} | Precio Escritura: USD {caso['p_esc']:,.2f}", ln=True)
        pdf.cell(0, 6, f"Categoria: {caso['tipo']}", ln=True)
        pdf.ln(8)
        
        pdf.set_font("Helvetica", "B", 9)
        pdf.set_fill_color(245, 243, 235) 
        pdf.cell(85, 9, " Concepto", 1, 0, 'L', True)
        pdf.cell(45, 9, "Monto (USD)", 1, 0, 'C', True)
        pdf.cell(60, 9, " Base Imponible", 1, 1, 'L', True)
        
        pdf.set_font("Helvetica", "", 9)
        items = [
            ["Honorarios Inmobiliarios", f"{caso['res']['comision']:,.2f}", "Sobre Valor Real"],
            ["IVA s/ Honorarios", f"{caso['res']['iva_com']:,.2f}", "21% Profesional"],
            ["Honorarios Escribania", f"{caso['res']['hono_esc']:,.2f}", "Sobre Escritura"],
            ["IVA s/ Escribania", f"{caso['res']['iva_esc']:,.2f}", "21% Profesional"],
            ["Impuesto de Sellos (50%)", f"{caso['res']['sellos']:,.2f}", "Ley CABA 2026"]
        ]
        for item in items:
            pdf.cell(85, 8, f" {item[0]}", 1)
            pdf.cell(45, 8, f"{item[1]}", 1, 0, 'R')
            pdf.cell(60, 8, f" {item[2]}", 1, 1)
        
        pdf.ln(8)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(11, 61, 46)
        res_label = "NETO A RECIBIR" if caso['rol'] == "Vendedor" else "TOTAL A PAGAR"
        final_val = (caso['p_real'] - caso['res']['total_gastos']) if caso['rol'] == "Vendedor" else (caso['p_real'] + caso['res']['total_gastos'])
        pdf.cell(0, 10, f"{res_label}: USD {final_val:,.2f}", ln=True, align="R")

    # --- PÁGINA 3: RESUMEN COMPARATIVO (Solo si hay más de 1 caso) ---
    if len(casos) > 1:
        pdf.add_page()
        pdf.set_fill_color(11, 61, 46) 
        pdf.rect(0, 0, 210, 45, 'F') 
        try:
            pdf.image("logo_completo.png", x=65, y=5, w=80) 
        except: pass

        pdf.set_y(55)
        pdf.set_text_color(11, 61, 46)
        pdf.set_font("Helvetica", "B", 16)
        pdf.cell(0, 15, "RESUMEN COMPARATIVO DE ESCENARIOS", ln=True, align="C")
        pdf.ln(10)

        # Tabla Comparativa
        pdf.set_font("Helvetica", "B", 10)
        pdf.set_fill_color(245, 243, 235)
        pdf.cell(70, 12, "Concepto", 1, 0, 'C', True)
        pdf.cell(60, 12, "ESCENARIO A", 1, 0, 'C', True)
        pdf.cell(60, 12, "ESCENARIO B", 1, 1, 'C', True)

        pdf.set_font("Helvetica", "", 10)
        pdf.set_text_color(0, 0, 0)
        
        filas = [
            ["Precio Real (USD)", f"{casos[0]['p_real']:,.2f}", f"{casos[1]['p_real']:,.2f}"],
            ["Precio Escritura (USD)", f"{casos[0]['p_esc']:,.2f}", f"{casos[1]['p_esc']:,.2f}"],
            ["Categoría", casos[0]['tipo'], casos[1]['tipo']],
            ["Total Gastos (USD)", f"{casos[0]['res']['total_gastos']:,.2f}", f"{casos[1]['res']['total_gastos']:,.2f}"]
        ]
        
        for fila in filas:
            pdf.cell(70, 10, fila[0], 1)
            pdf.cell(60, 10, fila[1], 1, 0, 'C')
            pdf.cell(60, 10, fila[2], 1, 1, 'C')

        # Resultado Final Destacado
        pdf.ln(10)
        pdf.set_font("Helvetica", "B", 12)
        pdf.set_text_color(11, 61, 46)
        label_a = "NETO A" if casos[0]['rol'] == "Vendedor" else "TOTAL A"
        val_a = (casos[0]['p_real'] - casos[0]['res']['total_gastos']) if casos[0]['rol'] == "Vendedor" else (casos[0]['p_real'] + casos[0]['res']['total_gastos'])
        val_b = (casos[1]['p_real'] - casos[1]['res']['total_gastos']) if casos[1]['rol'] == "Vendedor" else (casos[1]['p_real'] + casos[1]['res']['total_gastos'])
        
        pdf.cell(70, 12, "RESULTADO FINAL", 1)
        pdf.cell(60, 12, f"USD {val_a:,.2f}", 1, 0, 'C')
        pdf.cell(60, 12, f"USD {val_b:,.2f}", 1, 1, 'C')

    # Footer común
    pdf.set_y(260)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(100, 100, 100)
    pdf.multi_cell(0, 4, txt="SIMULACION NO VINCULANTE. Documento generado para analisis comparativo de Llamedo Propiedades. "
                             "Los valores definitivos seran provistos por escribania mediante proforma.", align="C")
    
    return bytes(pdf.output())

# 5. INTERFAZ DE USUARIO
st.title("💼 Simulador de Escenarios")

with st.sidebar:
    st.image("logo_completo.png", use_container_width=True)
    st.markdown("---")
    fuente_dolar = st.radio("Dolar:", ["Oficial BCRA", "Manual"])
    val_bcra, fecha_bcra = obtener_dolar_bcra()
    tc = st.number_input("Valor USD", value=val_bcra, disabled=(fuente_dolar=="Oficial BCRA"))
    mni = st.number_input("Tope Sellos CABA (ARS)", value=226100000)

# ESCENARIO A
st.header("📍 Escenario A")
c_a1, c_a2 = st.columns([3, 1])
dir_a = c_a1.text_input("Direccion (Caso A)", "Propiedad Ejemplo")
uni_a = c_a2.text_input("Unidad (A)", "Piso/Depto")

col_a1, col_a2 = st.columns(2)
rol_a = col_a1.selectbox("Rol (A)", ["Vendedor", "Comprador"], key="rol_a")
p_real_a = col_a1.number_input("Precio Real (A)", value=100000.0, key="pr_a")
com_a = col_a1.number_input("% Comision (A)", value=3.0, key="c_a")
tipo_a = col_a2.selectbox("Tipo (A)", ["Primera Vivienda", "Segunda Vivienda", "Inversion"], key="t_a")
p_esc_a = col_a2.number_input("Precio Escritura (A)", value=80000.0, key="pe_a")
esc_a = col_a2.number_input("% Escribano (A)", value=2.0, key="e_a")

res_a = calcular_operacion(p_real_a, p_esc_a, com_a, esc_a, tipo_a, tc, mni)
final_a = (p_real_a - res_a['total_gastos']) if rol_a == "Vendedor" else (p_real_a + res_a['total_gastos'])

# CASO B
if not st.session_state.mostrar_caso_b:
    if st.button("➕ Comparar con Escenario B"):
        st.session_state.mostrar_caso_b = True
        st.rerun()

lista_casos = [{'nombre': 'A', 'rol': rol_a, 'p_real': p_real_a, 'p_esc': p_esc_a, 'tipo': tipo_a, 'direccion': dir_a, 'unidad': uni_a, 'res': res_a}]

if st.session_state.mostrar_caso_b:
    st.divider()
    st.header("📍 Escenario B")
    c_b1, c_b2 = st.columns([3, 1])
    dir_b = c_b1.text_input("Direccion (Caso B)", dir_a)
    uni_b = c_b2.text_input("Unidad (B)", uni_a)
    
    col_b1, col_b2 = st.columns(2)
    rol_b = col_b1.selectbox("Rol (B)", ["Vendedor", "Comprador"], key="rol_b")
    p_real_b = col_b1.number_input("Precio Real (B)", value=p_real_a, key="pr_b")
    com_b = col_b1.number_input("% Comision (B)", value=com_a, key="c_b")
    tipo_b = col_b2.selectbox("Tipo (B)", ["Primera Vivienda", "Segunda Vivienda", "Inversion"], index=1, key="t_b")
    p_esc_b = col_b2.number_input("Precio Escritura (B)", value=p_esc_a, key="pe_b")
    esc_b = col_b2.number_input("% Escribano (B)", value=esc_a, key="e_b")
    
    res_b = calcular_operacion(p_real_b, p_esc_b, com_b, esc_b, tipo_b, tc, mni)
    final_b = (p_real_b - res_b['total_gastos']) if rol_b == "Vendedor" else (p_real_b + res_b['total_gastos'])
    lista_casos.append({'nombre': 'B', 'rol': rol_b, 'p_real': p_real_b, 'p_esc': p_esc_b, 'tipo': tipo_b, 'direccion': dir_b, 'unidad': uni_b, 'res': res_b})
    
    if st.button("🗑️ Eliminar Escenario B"):
        st.session_state.mostrar_caso_b = False
        st.rerun()

st.divider()
m1, m2 = st.columns(2)
m1.metric(f"Neto A ({rol_a})", f"USD {final_a:,.2f}")
if st.session_state.mostrar_caso_b:
    m2.metric(f"Neto B ({rol_b})", f"USD {final_b:,.2f}")

# EXPORTAR PDF (1, 2 o 3 páginas según corresponda)
pdf_bytes = generar_pdf_comparativo(lista_casos, tc, mni)
st.download_button(
    label="📄 Descargar Informe Comparativo (PDF)",
    data=pdf_bytes,
    file_name="Comparativa_Llamedo_Propiedades.pdf",
    mime="application/pdf"
)
