from app.services.rules import DISCLAIMER


def answer(message, summary):
    question = message.lower()
    references = []
    if any(term in question for term in ['law', 'tax rate', 'regime', 'deductible', 'section ', 'save tax', 'tax advice', 'tax slab']):
        content = 'I can explain your preparation records, but I do not provide unverified tax-law advice. Review official Income Tax Department guidance or speak with a qualified tax professional: https://www.incometax.gov.in/'
    elif any(term in question for term in ['tds', 'match', 'discrep', 'difference']):
        findings = [i for i in summary['issues'] if i['issue_type'] in {'tds_difference','bank_interest_difference','not_comparable'}]
        lines = []
        for issue in findings:
            d = issue['details']
            line = d['title'] + '. ' + d['explanation']
            if 'difference' in d:
                line += f" {d['source_a']}: INR {d['value_a']}; {d['source_b']}: INR {d['value_b']}. Difference: INR {d['difference']}. FY {d['financial_year']}; context: {d['context']}."
                if d.get('provisional'):
                    line += ' These figures still need user verification.'
            line += ' Status: ' + issue['status'].replace('_',' ') + '.'
            lines.append(line)
            references.extend({'document_id': doc_id, 'label': f'Source record {n+1}'} for n,doc_id in enumerate(issue['source_document_ids']))
        content = '\n\n'.join(lines) or 'No differences were found by the implemented checks. ' + str(summary['comparable_checks']) + ' comparable checks could be performed; missing or incompatible records are not evidence of consistency.'
    elif any(term in question for term in ['score', 'readiness', 'percent']):
        content = f"Your preparation score is {summary['readiness_score']}%. " + '\n'.join(f"{k.replace('_',' ').title()}: {v['score']}% × {v['weight']}% weight = {v['contribution']} points." for k,v in summary['components'].items()) + '\n\n' + summary['scoring_notes']
    elif any(term in question for term in ['missing', 'document', 'before filing', 'next', 'review']):
        missing = [i['title'] + ' (' + i['status'].replace('_',' ') + ')' for i in summary['checklist'] if i['status'] not in {'complete','not_applicable'}]
        content = 'Your next document reviews:\n' + '\n'.join('- ' + v for v in missing) if missing else 'Your applicable checklist is complete. Review any remaining validation findings before filing.'
        content += f"\n{summary['total_fields'] - summary['verified_fields']} extracted fields still need verification."
    elif any(term in question for term in ['report', 'download']):
        content = 'Open Report Center and choose Generate report. The PDF captures your current checklist, verified income, score breakdown and unresolved findings. Generate a new report after changing records.'
    elif any(term in question for term in ['income', 'salary', 'interest']):
        content = 'Verified annual records only:\n' + '\n'.join(f"{i['label']}: INR {i['amount']}" for i in summary['income_summary'])
        for i in summary['income_summary']:
            references.extend({'document_id': d, 'label': i['label']} for d in i['source_document_ids'])
        content += '\nUnverified or ambiguous records are excluded. This is not a taxable-income calculation.'
    else:
        content = 'I can explain your readiness score, missing documents, TDS differences, verified income, pending verification, or how to generate a report. Try “Why does my TDS not match?”'
    return {'answer': content, 'references': references, 'mode': 'grounded_template', 'disclaimer': DISCLAIMER}

