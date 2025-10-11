# Debug Steps for Missing Document

## Document Details:
- Title: CHR_SOW#1_MarTech Enablement_Kick Off_11.21.24
- Expected: Should be in the system (first doc in spreadsheet)
- Issue: Not showing on page 5

## Quick Checks:

### 1. Search for the document:
In the Inventory tab, use the Search box and type: "CHR_SOW" or "MarTech"
This will tell us if the document exists anywhere in the system.

### 2. Check all pages:
The document might be on pages 1-4 depending on sorting.
- Default sort: by "created_at" descending (newest first)
- If this was the FIRST imported, it might be LAST in created_at order

### 3. Check the sort order:
- Current sort: created_at DESC (newest documents first)
- First imported document = oldest created_at = appears LAST
- So first spreadsheet doc should be on page 5 (documents 81-98)

## Likely Issue:
Documents are sorted by created_at DESCENDING, so:
- Newest documents → Page 1
- Oldest documents → Page 5

If the spreadsheet was processed top-to-bottom:
- First row (CHR_SOW#1...) = oldest created_at
- Should appear on page 5

## Solution:
If the document is missing from page 5, check:
1. Was it imported? (Search for it)
2. What's its created_at timestamp?
3. Are there exactly 98 documents or fewer?
