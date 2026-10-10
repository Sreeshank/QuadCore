import re
from decimal import Decimal, InvalidOperation
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

MONEY_FIELDS = {'gross_salary', 'taxable_salary', 'tds', 'bank_interest', 'deductions'}
FIELD_NAMES = MONEY_FIELDS | {'financial_year', 'assessment_year', 'employer_name', 'employee_name', 'pan', 'bank_name', 'period_scope', 'document_date'}
DOC_TYPES = Literal['form16', 'form26as', 'ais', 'bank_interest', 'salary_slip', 'other', 'freelance', 'business', 'capital_gains', 'rental', 'deductions', 'other_income']


def normalize(name: str, value: str) -> str:
    value = value.strip()
    if name not in FIELD_NAMES:
        raise ValueError('Unsupported field')
    if name in MONEY_FIELDS:
        cleaned = re.sub(r'(?i)(?:INR|Rs\.?|\u20b9|,|\s)', '', value)
        try:
            amount = Decimal(cleaned)
        except InvalidOperation:
            raise ValueError('Enter a valid monetary amount')
        if not amount.is_finite() or amount < 0 or amount >= Decimal('1000000000000000') or amount.as_tuple().exponent < -2:
            raise ValueError('Amount must be non-negative, below 10^15, and have at most two decimals')
        return str(amount.quantize(Decimal('0.01')))
    if name in {'financial_year', 'assessment_year'}:
        match = re.fullmatch(r'(20\d{2})[-\u2013/](\d{2}|20\d{2})', value)
        if not match or int(match[2][-2:]) != (int(match[1]) + 1) % 100:
            raise ValueError('Use a consecutive year such as 2025-26')
        return f'{match[1]}-{match[2][-2:]}'
    if name == 'pan' and not re.fullmatch('[A-Z]{5}[0-9]{4}[A-Z]', value.upper()):
        raise ValueError('Invalid PAN format')
    if name == 'document_date':
        from datetime import date
        date.fromisoformat(value)
    if name == 'period_scope' and value.lower() not in {'annual', 'monthly', 'quarterly'}:
        raise ValueError('Period must be annual, monthly or quarterly')
    if not value or len(value) > 500:
        raise ValueError('Value must contain 1-500 characters')
    return value.upper() if name == 'pan' else value


class Answers(BaseModel):
    model_config = ConfigDict(extra='forbid')
    name: str = Field(default='Demo taxpayer', min_length=1, max_length=80)
    employment_type: Literal['salaried', 'freelancer', 'business', 'other'] = 'salaried'
    employers: int = Field(default=1, ge=0, le=20)
    salary: bool = True
    freelance: bool = False
    business: bool = False
    bank_interest: bool = True
    capital_gains: bool = False
    rental: bool = False
    other_income: str = Field(default='', max_length=500)
    deductions: bool = False
    form16_issued: bool = True
    completed: bool = True

    @model_validator(mode='after')
    def employer_count(self):
        if self.salary and self.employers < 1:
            raise ValueError('Salary income requires at least one employer')
        return self


class ProfileInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    financial_year: str = '2025-26'
    answers: Answers

    @field_validator('financial_year')
    @classmethod
    def year(cls, v):
        return normalize('financial_year', v)


class DemoInput(BaseModel):
    scenario: Literal['blank', 'sample', 'complete', 'incomplete'] = 'blank'


class VerifyField(BaseModel):
    id: str
    value: str = Field(min_length=1, max_length=500)
    verified: bool = True


class VerifyInput(BaseModel):
    fields: list[VerifyField] = Field(default_factory=list, max_length=100)
    document_type: DOC_TYPES | None = None


class IssueUpdate(BaseModel):
    status: Literal['open', 'under_review', 'resolved']
    resolution_note: str = Field(default='', max_length=1500)

    @model_validator(mode='after')
    def resolution(self):
        if self.status == 'resolved' and len(self.resolution_note.strip()) < 10:
            raise ValueError('Explain the resolution in at least 10 characters')
        return self


class ChatInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    provider: Literal['builtin', 'openai'] = 'builtin'
    model: str = Field(default='gpt-4.1-mini', min_length=1, max_length=80, pattern=r'^[A-Za-z0-9._:-]+$')
    share_context: bool = False
    message: str = Field(min_length=1, max_length=2000)


class LLMField(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field_name: str
    value: str
    source_page: int = Field(ge=1, le=30)
    evidence: str = Field(min_length=1, max_length=600)

    @model_validator(mode='after')
    def valid_value(self):
        normalize(self.field_name, self.value)
        return self


class LLMExtraction(BaseModel):
    model_config = ConfigDict(extra='forbid')
    document_type: DOC_TYPES
    fields: list[LLMField] = Field(max_length=20)


class ManualFieldInput(BaseModel):
    model_config = ConfigDict(extra='forbid')
    field_name: str
    value: str = Field(min_length=1, max_length=500)
    source_page: int = Field(ge=1, le=30)
    evidence: str = Field(min_length=3, max_length=600)

    @model_validator(mode='after')
    def valid(self):
        normalize(self.field_name, self.value)
        if len(self.evidence.strip()) < 3:
            raise ValueError('Quote source evidence from the page')
        return self


class DeleteDataInput(BaseModel):
    confirmation: Literal['DELETE MY DATA']


class BulkDeleteInput(BaseModel):
    document_ids: list[str] = Field(min_length=1, max_length=100)
