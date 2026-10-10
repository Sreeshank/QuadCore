# Synthetic samples

All names, identifiers, employers, banks and amounts are fictional. These are labelled extraction templates, not official tax documents.

- form16.pdf: FY 2025-26, annual Example Technologies salary INR 850,000; taxable salary INR 800,000; TDS INR 45,000.
- form26as.pdf: same employer and year, annual comparable TDS INR 42,000. The intentionally introduced difference is INR 3,000.
- bank-interest.pdf: annual Example Demo Bank interest INR 12,500.
- salary-slip.pdf: a monthly supporting salary record. Its amount is not added to the annual income summary.
- ais.pdf: annual interest INR 12,500 at Example Demo Bank.

Regenerate with `.venv\Scripts\python.exe scripts\generate_samples.py`.

Only the explicitly selected completed demo fixture replaces Form 26AS TDS with INR 45,000 and pre-verifies synthetic fields. Ordinary uploads and the discrepancy scenario always require manual confirmation.

Manual categorization can link other labelled records to freelancer, business, rental, capital-gains and deduction guidance items. The MVP does not calculate these incomes or tax liabilities.

