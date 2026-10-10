import io
from html import escape
from datetime import datetime, timezone
from decimal import Decimal
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from app.services.rules import DISCLAIMER

def make_pdf(summary, inventory):
    output = io.BytesIO()
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SmallText', fontSize=8, leading=12, textColor=colors.HexColor('#475569')))
    styles['Title'].textColor = colors.HexColor('#0f172a')
    styles['Heading2'].textColor = colors.HexColor('#2563eb')
    story = []
    def text(value, style='BodyText'):
        return Paragraph(escape(str(value)), styles[style])
    def heading(value):
        story.extend([Spacer(1, 6*mm), text(value, 'Heading2')])
    def table(headers, rows, widths=None):
        content = [[text(v, 'SmallText') for v in headers]] + [[text(v, 'SmallText') for v in row] for row in rows]
        t = Table(content, colWidths=widths, repeatRows=1, hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eff6ff')), ('VALIGN',(0,0),(-1,-1),'TOP'), ('LINEBELOW',(0,0),(-1,0),.5,colors.HexColor('#bfdbfe')), ('BOTTOMPADDING',(0,0),(-1,-1),8), ('TOPPADDING',(0,0),(-1,-1),8)]))
        story.append(t)
    timestamp = datetime.now(timezone.utc).isoformat()
    story += [text('TaxReady AI', 'Title'), text('Filing Preparation Readiness Report', 'Heading1'), text('Organize Smarter. Verify Faster. File With Confidence.', 'SmallText'), Spacer(1,5*mm)]
    profile = summary['profile']
    story += [text('Prepared for: ' + profile['answers']['name']), text('Financial year: ' + profile['financial_year']), text('Employment: ' + profile['answers']['employment_type']), text('Generated (UTC): ' + timestamp, 'SmallText')]
    heading('Preparation readiness: ' + summary['readiness_score'] + '%')
    table(['Component', 'Score', 'Weight', 'Contribution'], [[k.replace('_',' ').title(), v['score']+'%', v['weight']+'%', v['contribution']] for k,v in summary['components'].items()], [80*mm,25*mm,25*mm,35*mm])
    story.append(text(summary['scoring_notes'], 'SmallText'))
    if summary['high_severity_issues']:
        story.append(text(f"Attention: {summary['high_severity_issues']} unresolved high-severity issue(s), regardless of numerical score."))
    heading('Profile and declared sources')
    story.append(text(', '.join(k.replace('_',' ').title() for k in ['salary','freelance','business','bank_interest','capital_gains','rental','deductions'] if profile['answers'].get(k)) or 'No income sources declared.'))
    if profile['answers'].get('other_income'):
        story.append(text('Other income: ' + profile['answers']['other_income']))
    heading('Personalized document checklist')
    table(['Record', 'Status', 'Guidance'], [[i['title'], i['status'].replace('_',' ').title(), i['description']] for i in summary['checklist']], [48*mm,30*mm,87*mm])
    heading('Uploaded document inventory')
    table(['File', 'Category', 'Status'], [[d.filename,d.document_type,d.processing_status] for d in inventory] or [['No documents uploaded','','']], [85*mm,35*mm,45*mm])
    heading('Verified income summary')
    table(['Source', 'Verified amount (INR)', 'Source document IDs'], [[i['label'], format(Decimal(i['amount']), ',.2f'), ', '.join(i['source_document_ids']) or 'No verified source'] for i in summary['income_summary']], [35*mm,45*mm,85*mm])
    story.append(text('Only verified annual Form 16 salary and bank interest records are summarized. Ambiguous repeated sources and other income types are excluded; this is not a total taxable-income calculation.', 'SmallText'))
    heading('Unresolved validation findings')
    unresolved = [i for i in summary['issues'] if i['status'] != 'resolved']
    if not unresolved:
        story.append(text('No unresolved findings in the implemented checks.'))
    for item in unresolved:
        d = item['details']
        story.append(text(d['title'] + ' - ' + item['severity'].upper(), 'Heading3'))
        story.append(text(d['explanation']))
        if 'difference' in d:
            story.append(text(f"Source A: INR {d['value_a']} | Source B: INR {d['value_b']} | Difference: INR {d['difference']}" ))
        story.append(text('Sources: ' + ', '.join(item['source_document_ids']), 'SmallText'))
    resolved = [i for i in summary['issues'] if i['status'] == 'resolved']
    if resolved:
        heading('User-documented resolutions')
        for item in resolved:
            story.append(text(item['details']['title'] + ': ' + item['resolution_note']))
    heading('Missing information and next steps')
    for step in summary['next_steps'] or ['All implemented checks have been reviewed. Verify final details with your filing professional.']:
        story.append(text('- ' + step))
    heading('Important preparation notice')
    story.append(text(DISCLAIMER, 'SmallText'))
    def footer(canvas, doc):
        canvas.setStrokeColor(colors.HexColor('#dbeafe'))
        canvas.line(20*mm, 18*mm, 190*mm, 18*mm)
        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.HexColor('#64748b'))
        canvas.drawString(20*mm, 13*mm, 'TaxReady AI | Private preparation report | INR amounts')
        canvas.drawRightString(190*mm, 13*mm, str(doc.page))
    SimpleDocTemplate(output, pagesize=(210*mm,297*mm), rightMargin=22*mm,leftMargin=22*mm,topMargin=20*mm,bottomMargin=25*mm, title='TaxReady AI - Filing Preparation Readiness Report', author='TaxReady AI').build(story, onFirstPage=footer, onLaterPages=footer)
    return output.getvalue()

