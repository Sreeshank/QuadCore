"""Preparation guidance, not a statement of statutory filing requirements."""
import hashlib
import json
import re
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from app.models import Document, ChecklistItem, ValidationIssue

# Easy-to-edit guidance rules: answer key, title, category, accepted document types.
GUIDANCE = [
    ('salary', 'Salary records', 'salary', ['salary_slip'], 'Review supporting salary records for each declared employer.'),
    ('bank_interest', 'Bank interest statement', 'bank_interest', ['bank_interest'], 'Collect interest certificates or annual bank records.'),
    ('freelance', 'Freelance income records', 'freelance', ['freelance'], 'Collect invoices, receipts and a reconciled income summary.'),
    ('business', 'Business income records', 'business', ['business'], 'Prepare your income and expense records for professional review.'),
    ('capital_gains', 'Capital gains records', 'capital_gains', ['capital_gains'], 'Collect broker statements and transaction records.'),
    ('rental', 'Rental income records', 'rental', ['rental'], 'Collect rental receipts and relevant supporting records.'),
    ('other_income', 'Other income records', 'other_income', ['other_income'], 'Collect records for the other sources you declared.'),
    ('deductions', 'Deduction and exemption records', 'deductions', ['deductions'], 'Collect supporting evidence for deductions or exemptions you intend to review.'),
]
CRITICAL = {
    'form16': {'financial_year', 'employer_name', 'period_scope', 'gross_salary', 'tds'},
    'form26as': {'financial_year', 'employer_name', 'period_scope', 'tds'},
    'bank_interest': {'financial_year', 'bank_name', 'period_scope', 'bank_interest'},
    'ais': {'financial_year'},
    'salary_slip': {'financial_year', 'employer_name', 'gross_salary'},
}
DISCLAIMER = 'This is a preparation-progress indicator, not a tax-compliance guarantee or tax advice. TaxReady AI does not file returns. Verify source records and consult a qualified professional where needed.'


def fields(doc):
    return {f.field_name: f.normalized_value for f in doc.fields}


def context(value):
    return re.sub(r'[^a-z0-9]', '', value.lower())


def documents(db, profile):
    return list(db.scalars(select(Document).where(Document.profile_id == profile.id).order_by(Document.created_at.desc())))


def document_verified(doc):
    return bool(doc.fields) and all(f.verification_status == 'verified' for f in doc.fields) and CRITICAL.get(doc.document_type, {'financial_year'}).issubset(fields(doc))


def build_checklist(db, profile, docs):
    answers = profile.answers_json
    requirements = list(GUIDANCE)
    requirements += [
        ('form16', 'Form 16, when issued', 'salary', ['form16'], 'Review Form 16 from each declared employer, when issued.'),
        ('form26as', 'Form 26AS review', 'tax_credits', ['form26as'], 'Review the tax-credit statement for the selected financial year.'),
        ('ais', 'Annual Information Statement', 'tax_credits', ['ais'], 'Review reported information alongside your own records.'),
    ]
    previous = {i.requirement_key: i for i in db.scalars(select(ChecklistItem).where(ChecklistItem.profile_id == profile.id))}
    rows = []
    for key, title, category, types, description in requirements:
        applicable = bool(answers.get(key))
        if key == 'form16':
            applicable = bool(answers.get('salary') and answers.get('form16_issued'))
        if key in {'form26as', 'ais'}:
            applicable = any(bool(answers.get(k)) for k in ('salary', 'freelance', 'business', 'bank_interest', 'capital_gains', 'rental', 'other_income'))
        matches = [d for d in docs if d.document_type in types and fields(d).get('financial_year') == profile.financial_year and d.processing_status != 'extraction_failed']
        # Do not count a duplicate or a second certificate from the same employer as another employer.
        unique = {}
        for doc in matches:
            identity = context(fields(doc).get('employer_name', '')) if key in {'form16', 'salary'} else doc.file_hash
            if identity not in unique or document_verified(doc):
                unique[identity] = doc
        matches = list(unique.values())
        required_count = answers.get('employers', 1) if key in {'form16', 'salary'} else 1
        verified_count = sum(document_verified(d) for d in matches)
        status = 'not_applicable' if not applicable else ('complete' if verified_count >= required_count else 'needs_review' if matches else 'missing')
        if applicable and required_count > 1:
            description += f' {verified_count} of {required_count} employers have verified records.'
        item = previous.get(key) or ChecklistItem(profile_id=profile.id, requirement_key=key)
        item.title, item.description, item.income_category, item.status = title, description, category, status
        item.linked_document_id = matches[0].id if matches else None
        db.add(item)
        rows.append(item)
    db.flush()
    return rows


def evaluate(db, profile, docs, checklist):
    old = {i.fingerprint: i for i in db.scalars(select(ValidationIssue).where(ValidationIssue.profile_id == profile.id))}
    active = []
    checks = []

    def issue(kind, severity, ids, title, explanation, **details):
        body = {'title': title, 'explanation': explanation, 'recommended_action': 'Review the source records and document your findings.', **details}
        fingerprint = hashlib.sha256(json.dumps([kind, sorted(ids), body], sort_keys=True).encode()).hexdigest()
        item = old.pop(fingerprint, None) or ValidationIssue(profile_id=profile.id, fingerprint=fingerprint, issue_type=kind, severity=severity, source_document_ids=ids, details_json=body, status='open', resolution_note='')
        db.add(item)
        active.append(item)
        return item

    hashes = {}
    for doc in docs:
        values = fields(doc)
        if doc.file_hash in hashes:
            issue('duplicate', 'medium', [hashes[doc.file_hash], doc.id], 'Potential duplicate document', 'The files have identical contents. Keep one authoritative copy to avoid double-counting.')
        else:
            hashes[doc.file_hash] = doc.id
        year = values.get('financial_year')
        if year and year != profile.financial_year:
            issue('financial_year', 'high', [doc.id], 'Financial year needs attention', f'This document says FY {year}; your profile is FY {profile.financial_year}.')
        missing = sorted(CRITICAL.get(doc.document_type, {'financial_year'}) - values.keys())
        if missing:
            issue('missing_fields', 'medium', [doc.id], 'Critical information needs review', 'Required extraction fields are missing: ' + ', '.join(missing) + '. Upload a supported record or clearer source.', missing_fields=missing)
    for item in checklist:
        if item.status == 'missing':
            issue('missing_records', 'medium', [], item.title + ' is missing', item.description, requirement_key=item.requirement_key)

    def compare(a_type, b_type, field, context_key, title):
        left = [d for d in docs if d.document_type == a_type]
        right = [d for d in docs if d.document_type == b_type]
        seen = set()
        for a in left:
            for b in right:
                pair = tuple(sorted((a.file_hash, b.file_hash)))
                if pair in seen:
                    continue
                seen.add(pair)
                av, bv = fields(a), fields(b)
                if field not in av or field not in bv:
                    continue
                # Annual totals only. A statement with multiple deductors must be reviewed manually.
                comparable = av.get('financial_year') == bv.get('financial_year') == profile.financial_year and av.get('period_scope', '').lower() == bv.get('period_scope', '').lower() == 'annual' and bool(av.get(context_key)) and context(av[context_key]) == context(bv.get(context_key, ''))
                # Multiple different annual records for one source cannot be assumed to
                # represent a single comparable total. Identical content copies are harmless.
                for candidates, values in [(left, av), (right, bv)]:
                    peers = [d for d in candidates if fields(d).get('financial_year') == values.get('financial_year')
                             and context(fields(d).get(context_key, '')) == context(values.get(context_key, ''))
                             and fields(d).get('period_scope', '').lower() == 'annual']
                    if len({fields(d).get(field) for d in peers}) > 1:
                        comparable = False
                if av.get('pan') and bv.get('pan') and av['pan'] != bv['pan']:
                    comparable = False
                if not comparable:
                    issue('not_comparable', 'medium', [a.id, b.id], 'Needs review: comparison context', 'Financial year, annual scope and employer/bank identity must match before comparing these values.', field=field)
                    continue
                difference = abs(Decimal(av[field]) - Decimal(bv[field]))
                record = {'field': field, 'source_document_ids': [a.id, b.id], 'passed': difference == 0}
                if difference:
                    problem = issue(field + '_difference', 'high', [a.id, b.id], title, 'A difference can have legitimate reasons. Please verify the figures in your source records; this is not a confirmed tax error.', field=field, value_a=av[field], value_b=bv[field], difference=str(difference), context=av[context_key], financial_year=profile.financial_year, source_a=a.filename, source_b=b.filename, provisional=not (document_verified(a) and document_verified(b)))
                    record['passed'] = problem.status == 'resolved'
                checks.append(record)

    compare('form16', 'form26as', 'tds', 'employer_name', 'TDS discrepancy detected')
    compare('bank_interest', 'ais', 'bank_interest', 'bank_name', 'Bank interest difference detected')
    for obsolete in old.values():
        db.delete(obsolete)
    db.flush()
    return active, checks


def serialize_issue(item):
    return {'id': item.id, 'issue_type': item.issue_type, 'severity': item.severity, 'source_document_ids': item.source_document_ids, 'details': item.details_json, 'status': item.status, 'resolution_note': item.resolution_note}


def serialize_checklist(item):
    return {key: getattr(item, key) for key in ('id', 'requirement_key', 'title', 'description', 'income_category', 'status', 'linked_document_id')}


def percent(a, b, zero='0'):
    return (Decimal(a) * 100 / Decimal(b)) if b else Decimal(zero)


def summarize(db, profile):
    docs = documents(db, profile)
    checklist = build_checklist(db, profile, docs)
    issues, checks = evaluate(db, profile, docs, checklist)
    applicable = [i for i in checklist if i.status != 'not_applicable']
    relevant = [d for d in docs if fields(d).get('financial_year') == profile.financial_year]
    all_fields = [f for d in relevant for f in d.fields]
    completed = sum(i.status == 'complete' for i in applicable)
    verified_fields = sum(f.verification_status == 'verified' for f in all_fields)
    components = {
        'document_completeness': percent(completed, len(applicable), '100'),
        'field_verification': percent(verified_fields, len(all_fields), '100' if not applicable else '0'),
        'consistency': percent(sum(c['passed'] for c in checks), len(checks), '100' if not applicable else '0'),
        'profile_completion': Decimal('100') if profile.answers_json.get('completed') else Decimal('0'),
    }
    weights = {'document_completeness': Decimal('.40'), 'field_verification': Decimal('.25'), 'consistency': Decimal('.25'), 'profile_completion': Decimal('.10')}
    score = sum(components[key] * weights[key] for key in components).quantize(Decimal('.1'), rounding=ROUND_HALF_UP)
    income = []
    for category, label, name in [('form16', 'Salary', 'gross_salary'), ('bank_interest', 'Bank interest', 'bank_interest')]:
        # A single authoritative verified record per employer/bank; ambiguous duplicates are excluded.
        groups = {}
        for d in relevant:
            if d.document_type != category or not document_verified(d):
                continue
            values = fields(d)
            if name in values and values.get('period_scope', '').lower() == 'annual':
                identity = context(values.get('employer_name' if category == 'form16' else 'bank_name', ''))
                groups.setdefault(identity, []).append(d)
        chosen = []
        for group in groups.values():
            if len({fields(d)[name] for d in group}) == 1:
                chosen.append(group[0])
        amount = sum((Decimal(fields(d)[name]) for d in chosen), Decimal('0'))
        income.append({'label': label, 'amount': str(amount), 'source_document_ids': [d.id for d in chosen]})
    open_issues = [i for i in issues if i.status != 'resolved']
    result = {
        'profile': {'id': profile.id, 'financial_year': profile.financial_year, 'answers': profile.answers_json},
        'readiness_score': str(score),
        'components': {key: {'score': str(value.quantize(Decimal('.1'))), 'weight': str(weights[key] * 100), 'contribution': str((value * weights[key]).quantize(Decimal('.1')))} for key, value in components.items()},
        'scoring_notes': 'Not-applicable checklist items are excluded. With no applicable requirements, empty components are 100. Otherwise no extracted fields or no comparable checks score 0 in those components. User-resolved differences count as reviewed consistency checks; this does not prove the underlying figures correct.',
        'documents_uploaded': len(docs), 'missing_documents': sum(i.status == 'missing' for i in applicable),
        'unresolved_mismatches': sum(i.issue_type in {'tds_difference', 'bank_interest_difference', 'financial_year', 'not_comparable'} for i in open_issues),
        'verified_records': sum(document_verified(d) for d in relevant),
        'verified_fields': verified_fields, 'total_fields': len(all_fields),
        'checklist_complete': completed, 'checklist_total': len(applicable),
        'comparable_checks': len(checks), 'passed_checks': sum(c['passed'] for c in checks),
        'high_severity_issues': sum(i.severity == 'high' for i in open_issues),
        'checklist': [serialize_checklist(i) for i in checklist],
        'issues': [serialize_issue(i) for i in issues],
        'income_summary': income,
        'recent_activity': [{'id': d.id, 'filename': d.filename, 'document_type': d.document_type, 'status': d.processing_status, 'created_at': d.created_at.isoformat()} for d in docs[:5]],
        'next_steps': [i.title for i in applicable if i.status != 'complete'][:5] + (['Review unresolved source-record issues'] if open_issues else []),
        'disclaimer': DISCLAIMER,
    }
    db.commit()
    return result

