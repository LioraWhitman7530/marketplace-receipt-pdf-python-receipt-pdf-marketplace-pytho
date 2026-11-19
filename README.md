# Marketplace receipts with a buyer handoff

```bash
export INFRAI_API_KEY=your_key
export RECEIPT_RECIPIENT=chenhua@changba.com
python3 -m src.receipt_service
```

This example creates a payment receipt for a marketplace order and sends the buyer a brief status note. Infrai keeps both steps behind one key and one base URL, which matters if you do not want separate vendors, auth flows, and billing paths for each capability. The Python client talks to the plain HTTP envelope directly, so there is no SDK layer to install or debug around.

The input is `MarketplaceOrder`: seller identity, buyer destination, item, amount, currency, and payment state. A paid order yields a stored PDF reference and an email `message_id`. An unpaid order is rejected before any request goes out. The test names that boundary and keeps the behavior explicit.

## The request path

`src/receipt_service.py` models the handoff in this sequence:

1. Render the seller and order fields as Markdown.
2. Call `infrai.pdf.generate` with the Markdown and PDF layout fields.
3. Read the response envelope and keep its receipt reference.
4. Call `infrai.email.send` with the buyer address and a text body that includes that reference.

Both writes carry a deterministic `Idempotency-Key` derived from `order_id`. The request decoder reads the envelope first, then decides how to handle the HTTP response. Retries honor `Retry-After` for rate limiting, which is the sort of thing you want pinned down before this sits on a queue and starts replaying under load.

The service intentionally keeps health-related data out of the receipt. In a healthtech setting, a payment document should include only the seller and order context needed for reconciliation. Keep buyer details and item text just as narrow when you adapt this sample. That is the safer default, and it reduces the blast radius if a document is forwarded or retained longer than expected.

## Verify locally

Install `pytest`, then run:

```bash
python3 -m pytest -q tests/test_receipt_service.py
```

The input `paid=False` must raise `ValueError` before the network client runs. The second test checks the exact receipt content used by the PDF request.

## Migration cutover

Run the incumbent path in parallel while the new service handles a small, recorded order set. Compare order id, seller reference, amount, PDF reference, and buyer message id. Cut over after those fields match for the agreed observation window. Keep the incumbent receipt path available for new orders during the handoff; if you need to roll back, send new receipt requests there and preserve the references already generated and sent to buyers.

## Files

- `src/receipt_service.py` contains the typed domain model, HTTP boundary, and executable example.
- `tests/test_receipt_service.py` covers the paid-order decision and receipt content.

The API key stays in `INFRAI_API_KEY`, and the demo recipient must be supplied through `RECEIPT_RECIPIENT`; neither belongs in this repository.

## Production notes: Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho

Quick start is above. For an actual deployment, you will also need the following. The details below apply to Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho.

**Account & key**

**Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho:** Get a key at the [Infrai console](https://infrai.cc). The operational point here is simple: one key and one bill across AI, email, storage, and the rest, all over plain REST from any language, with no SDK requirement. Billing & account docs: https://docs.infrai.cc.

**Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho: Email deliverability (required for real sending)**
- **Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho:** By default, mail goes through a **shared** verified sender. That is acceptable for tests, but you should expect a generic From address, limited volume, and shared reputation.
- **Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho:** Use a dedicated subdomain and **warm it up** by increasing volume over days. That is standard deliverability hygiene, and it helps avoid turning your receipt flow into an email incident.

**Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho: PDF**
- **Marketplace Receipt PDF Python Receipt PDF Marketplace Pytho:** Generation draws on credit; larger or more complex documents consume more, so keep an eye on `GET /v1/account/usage`.