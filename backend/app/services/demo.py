import hashlib
import io
from reportlab.pdfgen import canvas
from app.models import TaxProfile, Document, uid
from app.schemas import Answers
from app.services import storage
from app.services.extraction import process_document
from app.services.rules import document_verified

SAMPLES = {
    'form16.pdf': ('FORM 16', ['Employer Name: Example Technologies Pvt Ltd', 'Employee Name: Sammer Demo', 'PAN: ABCDE1234F', 'Gross Salary: 8,50,000.00', 'Taxable Salary: 8,00,000.00', 'TDS: 45,000.00', 'Deductions: 50,000.00']),
    'form26as.pdf': ('FORM 26AS', ['Deductor Name: Example Technologies Pvt Ltd', 'Taxpayer Name: Sammer Demo', 'PAN: ABCDE1234F', 'Comparable TDS: 42,000.00']),
    'bank-interest.pdf': ('BANK INTEREST STATEMENT', ['Bank Name: Example Demo Bank', 'Employee Name: Sammer Demo', 'Interest Income: 12,500.00']),
    'salary-slip.pdf': ('SALARY SLIP', ['Employer Name: Example Technologies Pvt Ltd', 'Employee Name: Sammer Demo', 'Gross Salary: 70,833.33']),
    'ais.pdf': ('ANNUAL INFORMATION STATEMENT (AIS)', ['Bank Name: Example Demo Bank', 'Taxpayer Name: Sammer Demo', 'Bank Interest: 12,500.00']),
}


def sample_pdf(name, complete=False):
    from reportlab.lib.colors import HexColor
    title, lines = SAMPLES[name]
    if complete and name == 'form26as.pdf':
        lines = [line.replace('42,000.00', '45,000.00') for line in lines]
    output = io.BytesIO()
    pdf = canvas.Canvas(output, pagesize=(595, 842))
    pdf.setTitle('SYNTHETIC DEMO - ' + title)
    pdf.setAuthor('TaxReady AI synthetic sample generator')
    navy, accent, muted = HexColor('#172C47'), HexColor('#245C86'), HexColor('#62748A')
    issuer = 'EXAMPLE DEMO BANK' if name == 'bank-interest.pdf' else 'EXAMPLE TECHNOLOGIES PVT LTD' if name in {'form16.pdf','salary-slip.pdf'} else 'TAXREADY DEMO RECORDS'
    pdf.setFillColor(navy); pdf.rect(0, 752, 595, 90, fill=1, stroke=0)
    pdf.setFillColorRGB(1,1,1);pdf.setFont('Helvetica-Bold',12);pdf.drawString(38,808,issuer)
    pdf.setFont('Helvetica',9);pdf.drawString(38,790,'Illustrative financial record | Personal copy')
    pdf.setFont('Helvetica-Bold',8);pdf.drawRightString(557,808,'SYNTHETIC SAMPLE')
    pdf.setFont('Helvetica',8);pdf.drawRightString(557,789,'FY 2025-26')
    pdf.setFillColor(navy);pdf.setFont('Helvetica-Bold',20);pdf.drawString(38,717,title)
    pdf.setFont('Helvetica',9);pdf.setFillColor(muted)
    subtitles = {'form16.pdf':'Salary and tax-deduction summary', 'form26as.pdf':'Consolidated tax-credit statement',
        'bank-interest.pdf':'Annual interest certificate', 'salary-slip.pdf':'Monthly payroll statement', 'ais.pdf':'Annual information summary'}
    pdf.drawString(38,697,subtitles[name])
    pdf.drawRightString(557,697,'Reference: DEMO/2526/' + name.split('.')[0].upper())
    pdf.setStrokeColor(HexColor('#C9D4DF'));pdf.line(38,681,557,681)
    pdf.saveState();pdf.translate(300,400);pdf.rotate(38);pdf.setFillColor(HexColor('#F2F4F7'));pdf.setFont('Helvetica-Bold',64);pdf.drawCentredString(0,0,'SAMPLE');pdf.restoreState()
    def section(label,y):
        pdf.setFillColor(HexColor('#EAF0F6'));pdf.rect(38,y-6,519,23,fill=1,stroke=0)
        pdf.setFillColor(accent);pdf.setFont('Helvetica-Bold',9);pdf.drawString(49,y+2,label)
    section('01  RECORD DETAILS',654)
    context=['Financial Year: 2025-26','Assessment Year: 2026-27','Period Scope: '+('monthly' if name=='salary-slip.pdf' else 'annual'),'Document Date: 2026-05-01']
    y=625
    for line in context:
        pdf.setFillColor(navy);pdf.setFont('Helvetica',10);pdf.drawString(49,y,line);y-=20
    section('02  TAXPAYER AND FINANCIAL SUMMARY',y-8);y-=39
    for n,line in enumerate(lines):
        if n%2==0:
            pdf.setFillColor(HexColor('#F6F8FB'));pdf.rect(38,y-7,519,23,fill=1,stroke=0)
        pdf.setFillColor(navy);pdf.setFont('Helvetica',10);pdf.drawString(49,y,line)
        pdf.setStrokeColor(HexColor('#E5EAF0'));pdf.line(38,y-8,557,y-8);y-=25
    y-=18;section('03  SUPPORTING BREAKDOWN (ILLUSTRATIVE)',y);y-=29
    if name in {'form16.pdf','form26as.pdf'}:
        amount='11,250.00' if name=='form16.pdf' or complete else '10,500.00'
        rows=[('Quarter','Period','Tax credit / deduction (INR)'),
              ('Q1','Apr - Jun 2025',amount),('Q2','Jul - Sep 2025',amount),
              ('Q3','Oct - Dec 2025',amount),('Q4','Jan - Mar 2026',amount)]
    elif name=='bank-interest.pdf':
        rows=[('Account / deposit','Period','Interest (INR)'),('Savings ****4821','Apr 2025 - Mar 2026','2,500.00'),('Term deposit ****7306','Apr 2025 - Mar 2026','10,000.00')]
    elif name=='salary-slip.pdf':
        rows=[('Earnings component','Pay period','Amount (INR)'),('Basic pay','April 2025','45,000.00'),('Allowances','April 2025','25,833.33')]
    else:
        rows=[('Information category','Reporting source','Amount (INR)'),('Savings interest','Example Demo Bank','2,500.00'),('Deposit interest','Example Demo Bank','10,000.00')]
    for n,(a,b,c) in enumerate(rows):
        pdf.setFillColor(accent if n==0 else navy);pdf.setFont('Helvetica-Bold' if n==0 else 'Helvetica',8)
        pdf.drawString(49,y,a);pdf.drawString(206,y,b);pdf.drawRightString(546,y,c)
        pdf.setStrokeColor(HexColor('#E5EAF0'));pdf.line(38,y-7,557,y-7);y-=22
    pdf.setStrokeColor(HexColor('#C9D4DF'));pdf.line(38,112,557,112)
    pdf.setFillColor(muted);pdf.setFont('Helvetica',8);pdf.drawString(38,96,'Computer-generated demonstration record. No signature is required for this sample.')
    pdf.setFont('Helvetica-Bold',8);pdf.drawString(38,78,'NOT AN OFFICIAL TAX DOCUMENT - ALL NAMES AND FIGURES ARE FICTIONAL')
    pdf.setFont('Helvetica',8);pdf.drawString(38,60,'Prepared for TaxReady AI walkthroughs and extraction testing. Amounts shown in INR.')
    pdf.drawRightString(557,38,'Page 1 of 1');pdf.drawString(38,38,'TaxReady AI | Organize. Review. Prepare.')
    pdf.save()
    return output.getvalue()



def seed_demo(db, user, scenario):
    if scenario == 'blank':
        return
    answers = Answers(name='Sammer Demo').model_dump()
    if scenario == 'incomplete':
        answers['capital_gains'] = True
        answers['completed'] = False
    profile = TaxProfile(user_id=user.id, financial_year='2025-26', answers_json=answers)
    db.add(profile)
    db.flush()
    names = list(SAMPLES) if scenario == 'complete' else ['form16.pdf'] if scenario == 'incomplete' else list(SAMPLES)[:3]
    for name in names:
        data = sample_pdf(name, complete=scenario == 'complete')
        identifier = uid()
        key = f'{user.id}/documents/{identifier}.pdf'
        storage.put(key,data,'application/pdf')
        doc = Document(id=identifier,user_id=user.id,profile_id=profile.id,filename=name,storage_path=key,file_hash=hashlib.sha256(data).hexdigest(),mime_type='application/pdf')
        db.add(doc)
        db.commit()
        process_document(db,doc,data)
        if scenario == 'complete':
            # This fixture is explicitly selected as pre-reviewed synthetic demo data.
            for field in doc.fields:
                field.verification_status = 'verified'
                field.review_indicator = 'Pre-reviewed synthetic demo fixture'
            doc.processing_status = 'verified' if document_verified(doc) else 'needs_verification'
    db.commit()

