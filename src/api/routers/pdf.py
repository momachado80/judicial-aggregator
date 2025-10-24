from fastapi import APIRouter, Query
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from sqlalchemy.orm import Session
from io import BytesIO
from datetime import datetime
from src.database import get_db
from src.normalization.models import Process
from typing import Optional

router = APIRouter()

@router.get("/export-pdf")
async def export_processes_pdf(
    tribunal: Optional[str] = Query(None),
    classe_tpu: Optional[str] = Query(None),
    relevance: Optional[str] = Query(None),
    numero_cnj: Optional[str] = Query(None),
    db: Session = next(get_db())
):
    query = db.query(Process)
    
    if tribunal:
        query = query.filter(Process.tribunal == tribunal)
    if classe_tpu:
        query = query.filter(Process.classe_tpu == classe_tpu)
    if relevance:
        query = query.filter(Process.relevance == relevance)
    if numero_cnj:
        query = query.filter(Process.numero_cnj.ilike(f"%{numero_cnj}%"))
    
    processes = query.limit(1000).all()
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#6366f1'),
        spaceAfter=30,
    )
    
    title = Paragraph("⚖️ Judicial Aggregator", title_style)
    elements.append(title)
    
    subtitle = Paragraph(f"Relatório gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", styles['Normal'])
    elements.append(subtitle)
    elements.append(Spacer(1, 20))
    
    info = Paragraph(f"<b>Total de processos:</b> {len(processes)}", styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 20))
    
    data = [['CNJ', 'Tribunal', 'Tipo', 'Comarca', 'Valor', 'Relevância']]
    
    for p in processes:
        tipo = 'Divórcio' if p.classe_tpu == '8015' else 'Inventário'
        valor = f"R$ {p.valor_causa:,.0f}".replace(',', '.')
        data.append([
            p.numero_cnj[:20],
            p.tribunal,
            tipo,
            p.comarca[:15],
            valor,
            p.relevance
        ])
    
    table = Table(data, colWidths=[2*inch, 0.8*inch, 1*inch, 1.2*inch, 1*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
    ]))
    
    elements.append(table)
    doc.build(elements)
    
    buffer.seek(0)
    filename = f"processos_{datetime.now().strftime('%Y-%m-%d')}.pdf"
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
