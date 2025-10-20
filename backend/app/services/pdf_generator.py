from io import BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

def generate_pdf_report(report_data: dict) -> bytes:
    """
    Генерирует PDF отчет на основе данных проверки рекламы.
    """
    
    # Регистрируем DejaVu шрифты с поддержкой кириллицы
    font_name = 'DejaVuSans'
    font_name_bold = 'DejaVuSans-Bold'
    
    try:
        # Пути к шрифтам в контейнере Linux
        dejavu_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
        dejavu_bold_path = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
        
        # Регистрируем шрифты
        if os.path.exists(dejavu_path):
            pdfmetrics.registerFont(TTFont(font_name, dejavu_path))
            print(f"Зарегистрирован шрифт: {font_name}")
        else:
            font_name = 'Times-Roman'
            print(f"DejaVu не найден, используем fallback: {font_name}")
            
        if os.path.exists(dejavu_bold_path):
            pdfmetrics.registerFont(TTFont(font_name_bold, dejavu_bold_path))
            print(f"Зарегистрирован жирный шрифт: {font_name_bold}")
        else:
            font_name_bold = 'Times-Bold'
            print(f"DejaVu Bold не найден, используем fallback: {font_name_bold}")
            
    except Exception as e:
        print(f"Ошибка регистрации DejaVu шрифтов: {e}")
        font_name = 'Times-Roman'
        font_name_bold = 'Times-Bold'
        print(f"Fallback на Times шрифты: {font_name}, {font_name_bold}")
    
    # Создаем буфер для PDF
    buffer = BytesIO()
    
    # Создаем документ
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=50,
        leftMargin=50,
        topMargin=50,
        bottomMargin=50
    )
    
    # Элементы документа
    story = []
    
    # Стили с поддержкой кириллицы
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=TA_CENTER,
        textColor=HexColor('#1f2937'),
        fontName=font_name
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        spaceAfter=12,
        spaceBefore=20,
        textColor=HexColor('#1f2937'),
        fontName=font_name
    )
    
    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        textColor=HexColor('#374151'),
        fontName=font_name
    )
    
    # Заголовок
    story.append(Paragraph("Отчет о проверке рекламы", title_style))
    story.append(Spacer(1, 20))
    
    # Исходный текст рекламы (если есть)
    if report_data.get('input_text'):
        story.append(Paragraph("Исходный текст рекламы", heading_style))
        
        # Стиль для текста рекламы
        ad_text_style = ParagraphStyle(
            'AdText',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=8,
            alignment=TA_LEFT,
            textColor=HexColor('#374151'),
            fontName=font_name,
            leftIndent=10,
            rightIndent=10,
            borderColor=HexColor('#e5e7eb'),
            borderWidth=1,
            borderPadding=10,
            backColor=HexColor('#f9fafb')
        )
        
        # Заменяем переносы строк на <br/> для сохранения форматирования
        ad_text = report_data.get('input_text', '').replace('\n', '<br/>')
        story.append(Paragraph(ad_text, ad_text_style))
        story.append(Spacer(1, 20))
    
    # Информация о проверке
    story.append(Paragraph("Информация о проверке", heading_style))
    
    info_data = [
        ['Дата проверки:', report_data.get('check_date_formatted', 'Не указана')],
        ['Закон:', report_data.get('law_name', 'Не указан')],
        ['Статус:', 'Соответствует законодательству' if report_data.get('is_ok') else 'Не соответствует законодательству']
    ]
    
    info_table = Table(info_data, colWidths=[2*inch, 4*inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), HexColor('#f9fafb')),
        ('TEXTCOLOR', (0, 0), (-1, -1), black),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (0, -1), font_name_bold),
        ('FONTNAME', (1, 0), (-1, -1), font_name),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('GRID', (0, 0), (-1, -1), 1, HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [HexColor('#ffffff'), HexColor('#f9fafb')])
    ]))
    
    story.append(info_table)
    story.append(Spacer(1, 20))
    
    # Результат проверки
    story.append(Paragraph("Результат проверки", heading_style))
    
    # Индикаторы (флаги)
    flags = report_data.get('flags', [])
    for flag in flags:
        flag_text = flag.get('text', '')
        if flag.get('type') == 'ok':
            story.append(Paragraph(f"✓ {flag_text}", normal_style))
        else:
            story.append(Paragraph(f"⚠ {flag_text}", normal_style))
    
    story.append(Spacer(1, 20))
    
    # Нарушения (если есть)
    violations = report_data.get('violations', [])
    if violations:
        story.append(Paragraph("Выявленные нарушения из Федерального закона «О рекламе»", heading_style))
        
        for i, violation in enumerate(violations, 1):
            # Заголовок нарушения
            violation_title = ParagraphStyle(
                'ViolationTitle',
                parent=styles['Heading3'],
                fontSize=12,
                spaceAfter=8,
                spaceBefore=12,
                textColor=HexColor('#dc2626'),
                fontName=font_name
            )
            
            story.append(Paragraph(violation.get('title', f'Нарушение {i}'), violation_title))
            
            # Текст нарушения
            violation_text = violation.get('text', 'Описание недоступно')
            story.append(Paragraph(violation_text, normal_style))
            
            # Рекомендации по исправлению
            if violation.get('fix'):
                story.append(Paragraph("<b>Рекомендации по исправлению:</b>", normal_style))
                story.append(Paragraph(violation.get('fix'), normal_style))
            
            story.append(Spacer(1, 12))
    
    # Судебная практика (если есть)
    cases = report_data.get('cases', [])
    if cases:
        story.append(Paragraph("Релевантная судебная практика", heading_style))
        
        for case in cases:
            case_title = ParagraphStyle(
                'CaseTitle',
                parent=styles['Heading4'],
                fontSize=11,
                spaceAfter=6,
                textColor=HexColor('#1f2937'),
                fontName=font_name
            )
            
            story.append(Paragraph(case.get('title', 'Судебное дело'), case_title))
            story.append(Paragraph(case.get('text', 'Описание недоступно'), normal_style))
            story.append(Spacer(1, 10))
    
    # Заключительная информация
    story.append(Spacer(1, 30))
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        alignment=TA_CENTER,
        textColor=HexColor('#6b7280'),
        fontName=font_name
    )
    
    story.append(Paragraph("Результаты проверки носят рекомендательный характер", footer_style))
    story.append(Paragraph(f"Отчет сгенерирован: {datetime.now().strftime('%d.%m.%Y в %H:%M')}", footer_style))
    
    # Примечание
    if report_data.get('footer_note'):
        story.append(Spacer(1, 10))
        story.append(Paragraph(report_data.get('footer_note'), footer_style))
    
    # Генерируем PDF
    doc.build(story)
    
    # Получаем байты
    pdf_bytes = buffer.getvalue()
    buffer.close()
    
    return pdf_bytes
