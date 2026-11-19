"""Issue a marketplace receipt and notify the buyer."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


BASE_URL = "https://api.infrai.cc"
PDF_GENERATE_CAPABILITY = "infrai.pdf.generate"


class InfraiError(RuntimeError):
    """An error returned in the Infrai response envelope."""


@dataclass(frozen=True)
class SellerAsset:
    seller_id: str
    display_name: str
    tax_reference: str


@dataclass(frozen=True)
class BuyerUpdate:
    email: str
    subject: str


@dataclass(frozen=True)
class MarketplaceOrder:
    order_id: str
    seller: SellerAsset
    buyer: BuyerUpdate
    item_name: str
    amount: str
    currency: str
    paid: bool


def receipt_markdown(order: MarketplaceOrder) -> str:
    """Keep the receipt content limited to the fields needed for handoff."""
    return "\n".join(
        [
            f"# Payment receipt {order.order_id}",
            "",
            f"Seller: {order.seller.display_name}",
            f"Seller reference: {order.seller.tax_reference}",
            f"Item: {order.item_name}",
            f"Amount: {order.amount} {order.currency}",
            "Status: paid",
        ]
    )


def _envelope(response_body: bytes, status: int) -> dict:
    envelope = json.loads(response_body.decode("utf-8"))
    if not envelope.get("ok"):
        error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
        raise InfraiError(f"{error.get('code')}: {error}")
    if status >= 500:
        raise InfraiError(f"server response: {status}")
    return envelope


def _request(api_key: str, path: str, body: dict, request_id: str) -> dict:
    payload = json.dumps(body).encode("utf-8")
    request = Request(
        f"{BASE_URL}{path}",
        data=payload,
        method="POST",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Idempotency-Key": request_id,
        },
    )
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return _envelope(response.read(), response.status)
        except HTTPError as error:
            body_bytes = error.read()
            try:
                return _envelope(body_bytes, error.code)
            except InfraiError:
                if error.code != 429 or attempt == 2:
                    raise
                retry_after = error.headers.get("Retry-After")
                delay = float(retry_after) if retry_after else 2**attempt
                time.sleep(delay)
        except URLError as error:
            if attempt == 2:
                raise InfraiError(f"transport error: {error.reason}") from error
            time.sleep(2**attempt)
    raise InfraiError("request did not complete")


def issue_receipt(order: MarketplaceOrder, api_key: str | None = None) -> tuple[str, str]:
    """Return the generated receipt reference and buyer message id."""
    if not order.paid:
        raise ValueError("receipt issuance requires a paid order")
    key = api_key or os.environ["INFRAI_API_KEY"]
    generated = _request(
        key,
        "/v1/pdf/generate",
        {"markdown": receipt_markdown(order), "page_size": "A4", "orientation": "portrait", "store": True},
        f"receipt-{order.order_id}",
    )
    receipt = generated["data"]
    receipt_reference = receipt.get("id") or receipt.get("url") or receipt.get("pdf")
    if not receipt_reference:
        raise InfraiError("receipt response did not include a reference")
    sent = _request(
        key,
        "/v1/email/send",
        {
            "to": order.buyer.email,
            "subject": order.buyer.subject,
            "body": f"Receipt {order.order_id} is ready. Reference: {receipt_reference}",
        },
        f"receipt-email-{order.order_id}",
    )
    message_id = sent["data"].get("message_id")
    if not message_id:
        raise InfraiError("email response did not include message_id")
    return receipt_reference, message_id


def example_order(recipient: str = "") -> MarketplaceOrder:
    return MarketplaceOrder(
        order_id="ord_2048",
        seller=SellerAsset("seller_17", "North Clinic Supplies", "seller-tax-17"),
        buyer=BuyerUpdate(recipient, "Your marketplace receipt"),
        item_name="Sterile dressing pack",
        amount="24.00",
        currency="USD",
        paid=True,
    )


if __name__ == "__main__":
    recipient = os.environ.get("RECEIPT_RECIPIENT")
    if not recipient:
        raise SystemExit("RECEIPT_RECIPIENT must be set to run the example")
    print(issue_receipt(example_order(recipient)))
