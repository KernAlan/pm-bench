# Feature Request: Billing Export API

## Request (from Sales, March 5)
- Enterprise customers need to export billing data
- Requested formats: CSV, PDF, Excel (.xlsx)
- Sales estimate: 3 enterprise deals ($120K combined ARR) waiting on this
- Engineering estimate: 3 weeks (1 week CSV, 1 week PDF, 1 week Excel)

## Customer research (from Josh, March 6)
- Talked to all 3 enterprise prospects:
  - Acme Corp: 'We just need a CSV we can import into QuickBooks'
  - Pinnacle Inc: 'CSV is fine, we use it for our monthly reconciliation'
  - Waverly Labs: 'We'd love Excel but honestly CSV works, we just paste it into Google Sheets'
- No customer specifically needs PDF
- Excel request came from the sales rep, not the customer
- All 3 confirmed: CSV with the right columns is sufficient

## Engineering breakdown
- CSV endpoint: 2 days (query + stream + format)
- PDF generation: 5 days (template engine, layout, styling, edge cases)
- Excel generation: 5 days (library integration, formatting, formulas)
- Testing + docs: 3 days
