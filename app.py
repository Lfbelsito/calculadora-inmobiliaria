def generar_pdf(datos, rol, total_final, mni_val):
    pdf = FPDF()
    pdf.add_page()
    
    # 1. ENCABEZADO (Bloque Verde Bosque)
    pdf.set_fill_color(11, 61, 46) 
    pdf.rect(0, 0, 210, 45, 'F') 
    
    try:
        # Logo centrado y más pequeño para evitar solapamiento
        pdf.image("logo_completo.png", x=65, y=8, w=80) 
    except:
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Arial", "B", 16)
        pdf.text(65, 25, "LLAMEDO PROPIEDADES")

    # 2. CUERPO DEL DOCUMENTO - Bajamos el cursor significativamente
    pdf.set_text_color(11, 61, 46)
    pdf.set_y(55) # Empieza bien abajo del bloque verde
    
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, f"SIMULACIÓN DE GASTOS: {rol.upper()}", ln=True, align="C")
    pdf.ln(2)
    
    # Datos de la Propiedad (Texto más chico: 10pt)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 6, f"Propiedad: {datos['direccion']} {datos['unidad']}", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 6, f"Valor Real Operación: USD {datos['p_real']:,.2f}", ln=True)
    pdf.cell(0, 6, f"Valor Escrituración: USD {datos['p_esc']:,.2f}", ln=True)
    pdf.ln(5)
    
    # 3. TABLA DE GASTOS (Más compacta)
    pdf.set_font("Arial", "B", 9)
    pdf.set_fill_color(249, 247, 242) # Tono Crema para la cabecera
    pdf.cell(80, 8, " Concepto", 1, 0, 'L', True)
    pdf.cell(45, 8, "Monto (USD)", 1, 0, 'C', True)
    pdf.cell(65, 8, " Base Imponible", 1, 1, 'L', True)
    
    pdf.set_font("Arial", "", 9)
    for item in datos['detalle']:
        pdf.cell(80, 7, f" {item[0]}", 1)
        pdf.cell(45, 7, f"USD {item[1]}", 1, 0, 'R')
        pdf.cell(65, 7, f" {item[2]}", 1, 1)
    
    # 4. TOTAL (Resaltado)
    pdf.ln(6)
    pdf.set_font("Arial", "B", 11)
    pdf.set_text_color(11, 61, 46)
    label = "NETO A RECIBIR" if rol == "Vendedor" else "TOTAL A DESEMBOLSAR"
    pdf.cell(0, 10, f"{label}: USD {total_final:,.2f}", ln=True, align="R")
    
    # 5. FIRMA PROFESIONAL
    pdf.ln(10)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Luciano Belsito", ln=True, align="R") #
    pdf.set_font("Arial", "", 9)
    pdf.cell(0, 5, "Martillero Público y Corredor Inmobiliario", ln=True, align="R") #
    pdf.cell(0, 5, "Matrícula CUCICBA", ln=True, align="R") #

    # 6. PIE DE PÁGINA (Aclaración legal)
    pdf.set_y(265)
    pdf.set_font("Arial", "I", 7)
    pdf.set_text_color(150, 150, 150)
    pdf.multi_cell(0, 3, txt="Aviso: Esta simulación es orientativa. Los valores definitivos surgirán "
                             "de las proformas de los escribanos y liquidaciones de impuestos "
                             "correspondientes previo al acto de escrituración.", align="C")
    
    return bytes(pdf.output())
