# Contributing

1. Fork, create a branch, make focused changes.
2. Use **synthetic, fictional** documents only (see `backend/tests/synth.py`). Never commit real statements, invoices, account numbers or secrets.
3. Run `cd backend && python -m pytest` and `cd frontend && npm test && npx tsc --noEmit`.
4. Add a test for every parser change (new statement layout = new synthetic fixture).
5. Keep processing logic in `backend/app/services/`; routes stay thin.

By contributing you agree your work is released under the MIT license.
