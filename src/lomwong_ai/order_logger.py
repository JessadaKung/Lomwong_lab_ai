from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


BANGKOK_TZ = ZoneInfo("Asia/Bangkok")
ORDER_WORKSHEET = "Orders"
ORDER_HEADERS = [
    "order_id",
    "timestamp",
    "date",
    "customer_name",
    "phone",
    "fulfillment",
    "menu",
    "quantity",
    "unit_price",
    "total",
    "item_note",
    "order_note",
    "status",
]
GOOGLE_SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


@dataclass(frozen=True)
class OrderItem:
    menu: str
    quantity: int
    unit_price: float
    note: str = ""

    @property
    def total(self) -> float:
        return self.quantity * self.unit_price


@dataclass(frozen=True)
class CustomerOrder:
    customer_name: str
    phone: str
    fulfillment: str
    items: list[OrderItem]
    note: str = ""
    status: str = "new"

    @property
    def total(self) -> float:
        return sum(item.total for item in self.items)


def google_sheet_configured() -> bool:
    return bool(os.getenv("GOOGLE_SHEET_ID")) and bool(
        os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
        or os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        or os.getenv("SERVICE_ACCOUNT_FILE")
    )


def load_service_account_info() -> dict[str, Any]:
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")
    if raw_json:
        try:
            return json.loads(raw_json)
        except json.JSONDecodeError as exc:
            raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON.") from exc

    credentials_path = (
        os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        or os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        or os.getenv("SERVICE_ACCOUNT_FILE")
    )
    if not credentials_path:
        raise RuntimeError("Set GOOGLE_SERVICE_ACCOUNT_JSON or GOOGLE_APPLICATION_CREDENTIALS.")

    try:
        with open(credentials_path, encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        raise RuntimeError(f"Cannot read service account file: {credentials_path}") from exc
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Service account file is not valid JSON: {credentials_path}") from exc


def get_orders_worksheet():
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ModuleNotFoundError as exc:
        raise RuntimeError("Install dependencies first: pip install -r requirements.txt") from exc

    sheet_id = os.getenv("GOOGLE_SHEET_ID")
    if not sheet_id:
        raise RuntimeError("Missing GOOGLE_SHEET_ID.")

    credentials = Credentials.from_service_account_info(
        load_service_account_info(),
        scopes=GOOGLE_SCOPES,
    )
    client = gspread.authorize(credentials)
    spreadsheet = client.open_by_key(sheet_id)

    try:
        return spreadsheet.worksheet(ORDER_WORKSHEET)
    except gspread.WorksheetNotFound:
        return spreadsheet.add_worksheet(title=ORDER_WORKSHEET, rows=1000, cols=len(ORDER_HEADERS))


def ensure_header(worksheet: Any) -> None:
    first_row = worksheet.row_values(1)
    if first_row != ORDER_HEADERS:
        worksheet.update(range_name=f"A1:M1", values=[ORDER_HEADERS])


def append_order(order: CustomerOrder) -> dict[str, Any]:
    if not order.items:
        raise ValueError("Order must have at least one item.")
    if not order.customer_name.strip():
        raise ValueError("Customer name is required.")
    if not order.phone.strip():
        raise ValueError("Phone number is required.")

    timestamp = datetime.now(BANGKOK_TZ)
    order_id = timestamp.strftime("LW%Y%m%d%H%M%S")
    rows = []
    for item in order.items:
        rows.append(
            [
                order_id,
                timestamp.isoformat(timespec="seconds"),
                timestamp.date().isoformat(),
                order.customer_name.strip(),
                order.phone.strip(),
                order.fulfillment,
                item.menu,
                item.quantity,
                item.unit_price,
                item.total,
                item.note,
                order.note,
                order.status,
            ]
        )

    worksheet = get_orders_worksheet()
    ensure_header(worksheet)
    worksheet.append_rows(rows, value_input_option="USER_ENTERED")
    return {
        "ok": True,
        "order_id": order_id,
        "item_count": len(order.items),
        "total": order.total,
    }


def format_order_message(order: CustomerOrder) -> str:
    lines = [
        "ออเดอร์ Lom Wong Café & Restaurant",
        f"ชื่อ: {order.customer_name}",
        f"เบอร์: {order.phone}",
        f"รูปแบบ: {order.fulfillment}",
        "",
        "รายการ:",
    ]
    for item in order.items:
        note = f" ({item.note})" if item.note else ""
        lines.append(f"- {item.menu} x {item.quantity} = {item.total:.0f} บาท{note}")

    lines.append("")
    lines.append(f"รวมทั้งหมด: {order.total:.0f} บาท")
    if order.note:
        lines.append(f"หมายเหตุ: {order.note}")
    return "\n".join(lines)
