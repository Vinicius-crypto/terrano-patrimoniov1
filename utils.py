"""
Utilitários do Sistema de Controle de Patrimônio
Funções auxiliares e helpers
"""
import os
from io import BytesIO
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# Extensões permitidas para upload
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def criar_termo_cautela_pdf(dados, pdf_buffer):
    """Criar PDF do Termo de Cautela"""
    
    # Configurar documento
    doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    
    # Estilo customizado
    titulo_style = ParagraphStyle(
        'TituloTermo',
        parent=styles['Heading1'],
        fontSize=16,
        textColor=colors.darkgreen,
        alignment=1,  # Centralizado
        spaceAfter=20
    )
    
    subtitulo_style = ParagraphStyle(
        'SubtituloTermo',
        parent=styles['Heading2'],
        fontSize=12,
        textColor=colors.black,
        alignment=1,
        spaceAfter=15
    )
    
    normal_style = ParagraphStyle(
        'NormalTermo',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.black,
        spaceBefore=5,
        spaceAfter=5
    )
    
    # Conteúdo do PDF
    story = []
    
    # Cabeçalho
    story.append(Paragraph("TERMO DE CAUTELA DE EQUIPAMENTO", titulo_style))
    story.append(Paragraph("SISTEMA DE CONTROLE PATRIMONIAL", subtitulo_style))
    story.append(Spacer(1, 20))
    
    # Dados do equipamento em tabela
    equipamento_data = [
        ['DADOS DO EQUIPAMENTO', ''],
        ['Patrimônio:', dados.get('patrimonio', 'N/A')],
        ['Tipo:', dados.get('tipo', 'N/A')],
        ['Categoria:', dados.get('categoria', 'N/A')],
        ['Marca:', dados.get('marca', 'N/A')],
        ['Modelo:', dados.get('modelo', 'N/A')],
        ['Número de Série:', dados.get('num_serie', 'N/A')],
        ['Código de Barras:', dados.get('codigo_barras', 'N/A')],
        ['Valor:', f"R$ {dados.get('valor', '0,00')}"],
        ['Fornecedor:', dados.get('fornecedor', 'N/A')],
        ['Localização:', dados.get('localizacao', 'N/A')],
    ]
    
    equipamento_table = Table(equipamento_data, colWidths=[4*72, 4*72])
    equipamento_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    
    story.append(equipamento_table)
    story.append(Spacer(1, 20))
    
    # Responsabilidade
    story.append(Paragraph("TERMO DE RESPONSABILIDADE", subtitulo_style))
    
    texto_responsabilidade = f"""
    Eu, <b>{dados.get('responsavel', '__________________')}</b>, declaro ter recebido em perfeitas 
    condições o equipamento acima descrito, comprometendo-me a:
    
    • Utilizar o equipamento exclusivamente para fins profissionais;
    • Zelar pela conservação e guarda do equipamento;
    • Comunicar imediatamente qualquer problema, dano ou furto;
    • Devolver o equipamento quando solicitado pela empresa;
    • Responsabilizar-me por eventuais danos causados por mau uso.
    
    <b>Observações:</b> {dados.get('observacoes', 'Nenhuma observação especial.')}
    """
    
    story.append(Paragraph(texto_responsabilidade, normal_style))
    story.append(Spacer(1, 30))
    
    # QR Code (simulado como texto)
    qr_text = f"QR: PAT-{dados.get('patrimonio', 'XXX')} | {dados.get('tipo', 'N/A')}"
    story.append(Paragraph(f"<b>Código QR:</b> {qr_text}", normal_style))
    story.append(Spacer(1, 30))
    
    # Assinaturas
    assinatura_data = [
        ['ASSINATURAS', '', ''],
        ['', '', ''],
        ['_' * 30, '_' * 30, '_' * 30],
        ['Responsável pelo Equipamento', 'Setor de TI/Patrimônio', 'Data'],
        [dados.get('responsavel', ''), dados.get('usuario_emitente', ''), dados.get('data_emissao', '')]
    ]
    
    assinatura_table = Table(assinatura_data, colWidths=[2.5*72, 2.5*72, 1.5*72])
    assinatura_table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('TOPPADDING', (0, 3), (-1, 3), 10),
    ]))
    
    story.append(assinatura_table)
    story.append(Spacer(1, 20))
    
    # Rodapé
    story.append(Paragraph(f"<i>Documento gerado automaticamente em {dados.get('data_emissao', 'N/A')} pelo Sistema de Controle Patrimonial.</i>", 
                          ParagraphStyle('Rodape', parent=styles['Normal'], fontSize=8, textColor=colors.grey, alignment=1)))
    
    # Construir PDF
    doc.build(story)
    return doc

def format_currency(value):
    """Formatar valor como moeda brasileira"""
    if not value:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(',', 'X').replace('.', ',').replace('X', '.')

def validate_cnpj(cnpj):
    """Validar CNPJ (implementação básica)"""
    if not cnpj:
        return True  # CNPJ é opcional
    
    # Remove caracteres não numéricos
    cnpj = ''.join(filter(str.isdigit, cnpj))
    
    # Verifica se tem 14 dígitos
    return len(cnpj) == 14

def sanitize_filename(filename):
    """Sanitizar nome de arquivo para upload"""
    if not filename:
        return None
    
    # Remove caracteres perigosos
    import re
    filename = re.sub(r'[^\w\-_\.]', '_', filename)
    return filename

def get_file_size_mb(file_path):
    """Obter tamanho do arquivo em MB"""
    if not os.path.exists(file_path):
        return 0
    return os.path.getsize(file_path) / (1024 * 1024)

def is_image_file(filename):
    """Verificar se é arquivo de imagem"""
    image_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in image_extensions

def is_pdf_file(filename):
    """Verificar se é arquivo PDF"""
    if not filename:
        return False
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'pdf'