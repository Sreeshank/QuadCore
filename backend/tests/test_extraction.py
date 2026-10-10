import io
from decimal import Decimal
import pytest
from PIL import Image
from pydantic import ValidationError
import pymupdf
from app.services import extraction
from app.services.demo import sample_pdf
from app.schemas import normalize, ProfileInput, IssueUpdate, LLMExtraction

@pytest.mark.parametrize('name,expected',[('form16.pdf','form16'),('form26as.pdf','form26as'),('bank-interest.pdf','bank_interest'),('salary-slip.pdf','salary_slip'),('ais.pdf','ais')])
def test_pdf_classification_and_evidence(name,expected):
    data=sample_pdf(name)
    assert extraction.validate_file(data,name)=='application/pdf'
    pages=extraction.extract_pages(data,'application/pdf')
    assert extraction.classify(pages[0]['text'])==expected
    fields=extraction.extract_fields(pages)
    assert next(f for f in fields if f['field_name']=='financial_year')['normalized_value']=='2025-26'
    assert all(f['source_page']==1 and f['evidence'] in pages[0]['text'] for f in fields)

def test_supported_financial_extraction():
    result={f['field_name']:f['normalized_value'] for f in extraction.extract_fields(extraction.extract_pages(sample_pdf('form16.pdf'),'application/pdf'))}
    assert result['gross_salary']=='850000.00'
    assert result['tds']=='45000.00'
    assert result['pan']=='ABCDE1234F'

def test_no_fabrication_or_ambiguous_total():
    page={'page':1,'method':'pdf_text','text':'Gross Salary: 100.00\nGross Salary: 200.00\nTDS: banana'}
    assert extraction.extract_fields([page])==[]

def test_image_ocr_fallback(monkeypatch):
    data=io.BytesIO();Image.new('RGB',(800,200),'white').save(data,'PNG')
    monkeypatch.setattr(extraction.pytesseract,'image_to_string',lambda *a,**kw:'BANK INTEREST STATEMENT\nInterest Income: 12,500.00')
    assert extraction.validate_file(data.getvalue(),'scan.png')=='image/png'
    pages=extraction.extract_pages(data.getvalue(),'image/png')
    assert pages[0]['method']=='ocr'
    assert extraction.extract_fields(pages)[0]['normalized_value']=='12500.00'

def test_scanned_pdf_uses_ocr(monkeypatch):
    pdf=pymupdf.open();pdf.new_page()
    monkeypatch.setattr(extraction.pytesseract,'image_to_string',lambda *a,**kw:'FORM 16\nTDS: 100.10')
    assert extraction.extract_pages(pdf.tobytes(),'application/pdf')[0]['method']=='ocr'

def test_missing_tesseract_actionable(monkeypatch):
    def fail(*a,**kw):raise extraction.pytesseract.TesseractNotFoundError()
    monkeypatch.setattr(extraction.pytesseract,'image_to_string',fail)
    with pytest.raises(ValueError,match='Tesseract'):
        extraction.ocr(Image.new('RGB',(10,10)))

@pytest.mark.parametrize('data,name',[(b'not a pdf','fake.pdf'),(sample_pdf('form16.pdf'),'fake.png'),(b'','empty.pdf'),(b'<script>bad</script>','file.jpg'),(b'MZbinary','file.exe')])
def test_content_inspection_rejects_invalid_files(data,name):
    with pytest.raises(ValueError):
        extraction.validate_file(data,name)

def test_upload_size_and_encrypted_pdf(monkeypatch):
    monkeypatch.setattr(extraction.settings,'max_upload_mb',1)
    with pytest.raises(ValueError,match='larger'):
        extraction.validate_file(b'%PDF-'+b'x'*1024*1024,'oversize.pdf')
    pdf=pymupdf.open();pdf.new_page()
    encrypted=pdf.tobytes(encryption=pymupdf.PDF_ENCRYPT_AES_256,owner_pw='owner',user_pw='secret')
    with pytest.raises(ValueError,match='password'):
        extraction.validate_file(encrypted,'locked.pdf')

def test_pdf_page_limit(monkeypatch):
    monkeypatch.setattr(extraction.settings,'max_pdf_pages',1)
    pdf=pymupdf.open();pdf.new_page();pdf.new_page()
    with pytest.raises(ValueError,match='pages'):
        extraction.validate_file(pdf.tobytes(),'big.pdf')

def test_exact_decimal_amounts():
    assert Decimal(normalize('tds','INR 42,000.10'))-Decimal(normalize('tds','Rs. 42,000.09'))==Decimal('0.01')

@pytest.mark.parametrize('value',['NaN','Infinity','-1','1.001','abc','1000000000000000'])
def test_currency_schema_rejects_invalid(value):
    with pytest.raises(ValueError):
        normalize('tds',value)

def test_year_and_resolution_validation():
    assert normalize('financial_year','2025\u20132026')=='2025-26'
    with pytest.raises(ValueError):normalize('financial_year','2025-27')
    with pytest.raises(ValidationError):IssueUpdate(status='resolved',resolution_note='done')
    with pytest.raises(ValidationError):ProfileInput(financial_year='2025-27',answers={})

def test_llm_schema_rejects_unknown_fields():
    with pytest.raises(ValidationError):
        LLMExtraction.model_validate({'document_type':'form16','fields':[{'field_name':'invented_income','value':'100','source_page':1,'evidence':'100'}]})

