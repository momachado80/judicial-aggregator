from fastapi import APIRouter, Query, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime
from typing import Optional

from src.database import get_db
from src.normalization.models import Process

router = APIRouter()

@router.get("/export-pdf")
async def export_pdf(
    tribunal: Optional[str] = Query(None),
    classe_tpu: Optional[str] = Query(None),
    relevance: Optional[str] = Query(None),
    numero_cnj: Optional[str] = Query(None),
    db: Session = Depends(get_db)
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
    
    title = Paragraph(f"<b>Judicial Aggregator - Relatório de Processos</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    info = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}<br/>Total: {len(processes)} processos", styles['Normal'])
    elements.append(info)
    elements.append(Spacer(1, 20))
    
    data = [['CNJ', 'Tribunal', 'Tipo', 'Comarca', 'Valor (R$)', 'Relevância']]
    
    for p in processes:
        tipo = 'Divórcio' if p.classe_tpu == '8015' else 'Inventário'
        valor = f"{p.valor_causa:,.0f}".replace(',', '.')
        data.append([
            p.numero_cnj[:18],
            p.tribunal,
            tipo[:10],
            p.comarca[:12],
            valor,
            p.relevance[:8]
        ])
    
    table = Table(data, colWidths=[1.8*inch, 0.7*inch, 0.9*inch, 1.1*inch, 0.9*inch, 0.8*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6366f1')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 7),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
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
