from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

from order_logger import BANGKOK_TZ, CustomerOrder, format_order_message, get_orders_worksheet


@dataclass(frozen=True)
class OrderReport:
    report_date: date
    order_count: int
    item_count: int
    total_sales: float
    top_menu: str


def telegram_configured() -> bool:
    return bool(os.getenv("TELEGRAM_BOT_TOKEN")) and bool(os.getenv("TELEGRAM_CHAT_ID"))


def send_telegram_message(message: str) -> dict[str, Any]:
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = os.getenv("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        raise RuntimeError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID.")

    payload = json.dumps({"chat_id": chat_id, "text": message}).encode("utf-8")
    request = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8")
        raise RuntimeError(f"Telegram API error: {detail}") from exc


def send_order_notification(order: CustomerOrder, order_id: str | None = None) -> dict[str, Any]:
    title = "มีออเดอร์ใหม่"
    if order_id:
        title += f" #{order_id}"
    return send_telegram_message(f"{title}\n\n{format_order_message(order)}")


def fetch_order_rows() -> list[dict[str, Any]]:
    worksheet = get_orders_worksheet()
    rows = worksheet.get_all_records()
    return [dict(row) for row in rows if row]


def summarize_orders(report_date: date | None = None) -> OrderReport:
    selected_date = report_date or datetime.now(BANGKOK_TZ).date()
    rows = [row for row in fetch_order_rows() if str(row.get("date")) == selected_date.isoformat()]

    order_ids = {str(row.get("order_id")) for row in rows if row.get("order_id")}
    item_count = 0
    total_sales = 0.0
    menu_counter: Counter[str] = Counter()

    for row in rows:
        try:
            quantity = int(row.get("quantity") or 0)
        except (TypeError, ValueError):
            quantity = 0
        try:
            total = float(row.get("total") or 0)
        except (TypeError, ValueError):
            total = 0.0

        menu = str(row.get("menu") or "").strip()
        item_count += quantity
        total_sales += total
        if menu:
            menu_counter[menu] += quantity

    top_menu = "-"
    if menu_counter:
        name, quantity = menu_counter.most_common(1)[0]
        top_menu = f"{name} x {quantity}"

    return OrderReport(
        report_date=selected_date,
        order_count=len(order_ids),
        item_count=item_count,
        total_sales=total_sales,
        top_menu=top_menu,
    )


def format_report(report: OrderReport) -> str:
    return "\n".join(
        [
            f"รายงานยอดขาย Lom Wong Café & Restaurant ({report.report_date.isoformat()})",
            f"- จำนวนออเดอร์: {report.order_count}",
            f"- จำนวนเมนูที่ขาย: {report.item_count}",
            f"- ยอดขายรวม: {report.total_sales:.0f} บาท",
            f"- เมนูขายดี: {report.top_menu}",
        ]
    )


def send_today_report() -> dict[str, Any]:
    report = summarize_orders()
    return send_telegram_message(format_report(report))
