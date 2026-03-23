from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from llm_service import LLMService


SCHEMA_TEXT = """
business_partner(business_partner_id, customer_code, full_name, category, is_blocked, is_archived, created_at, updated_at)
business_partner_address(business_partner_id, address_id, address_uuid, valid_from, valid_to, city, country, postal_code, region, street)
customer_sales_area(customer_id, sales_organization, distribution_channel, division, currency, payment_terms, incoterms_code, incoterms_location, shipping_condition, delivery_priority)
customer_company(customer_id, company_code, reconciliation_account, customer_account_group, is_deleted)
plant(plant_id, plant_name, sales_organization, distribution_channel, division)
product(product_id, product_type, product_group, base_unit, division, industry_sector, net_weight, gross_weight, weight_unit, is_marked_for_deletion, created_at, updated_at)
product_description(product_id, language, description)
product_plant(product_id, plant_id, availability_check_type, mrp_type, profit_center)
product_storage_location(product_id, plant_id, storage_location_code, inventory_block_indicator, last_count_posted_date)
sales_order(sales_order_id, sold_to_party_id, sales_order_type, sales_organization, distribution_channel, division, transaction_currency, total_net_amount, created_on, requested_delivery_date)
sales_order_item(sales_order_id, item_no, product_id, production_plant_id, storage_location_code, order_item_category, requested_quantity, quantity_unit, transaction_currency, net_amount)
sales_order_schedule_line(sales_order_id, item_no, schedule_line_no, confirmed_delivery_date, confirmed_quantity, quantity_unit)
outbound_delivery(delivery_document_id, created_on, goods_movement_date, shipping_point, overall_goods_movement_status, overall_picking_status)
outbound_delivery_item(delivery_document_id, item_no, sales_order_id, sales_order_item_no, plant_id, storage_location_code, actual_delivery_quantity, quantity_unit)
accounting_document(company_code, fiscal_year, accounting_document_id, posting_date, document_date)
billing_document(billing_document_id, sold_to_party_id, company_code, fiscal_year, accounting_document_id, billing_document_type, billing_date, transaction_currency, total_net_amount, is_cancelled, cancelled_billing_document_id)
billing_document_item(billing_document_id, item_no, product_id, delivery_document_id, delivery_item_no, billing_quantity, quantity_unit, transaction_currency, net_amount)
journal_entry_ar_line(company_code, fiscal_year, accounting_document_id, accounting_document_item, gl_account, customer_id, reference_billing_document_id, posting_date, document_date, transaction_currency, amount_in_transaction_currency, clearing_date, clearing_accounting_document_id, clearing_doc_fiscal_year)
ar_clearing_line(company_code, fiscal_year, accounting_document_id, accounting_document_item, customer_id, invoice_reference_id, sales_document_id, sales_document_item_no, posting_date, document_date, transaction_currency, amount_in_transaction_currency, clearing_date, clearing_accounting_document_id, clearing_doc_fiscal_year)
""".strip()


DATASET_KEYWORDS = {
    "customer",
    "order",
    "orders",
    "orderitem",
    "order item",
    "product",
    "products",
    "delivery",
    "deliveries",
    "invoice",
    "invoices",
    "payment",
    "payments",
    "sales",
    "billing",
    "ar",
    "receivable",
    "sap",
}


@dataclass
class QueryOutcome:
    success: bool
    status: str
    message: str
    user_query: str
    generated_sql: Optional[str] = None
    row_count: int = 0
    data: Optional[List[Dict[str, Any]]] = None
    answer: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "status": self.status,
            "message": self.message,
            "user_query": self.user_query,
            "generated_sql": self.generated_sql,
            "row_count": self.row_count,
            "data": self.data or [],
            "answer": self.answer,
        }


def is_dataset_related(user_query: str) -> bool:
    normalized = re.sub(r"\s+", " ", user_query.strip().lower())
    return any(keyword in normalized for keyword in DATASET_KEYWORDS)


def _is_safe_select_sql(sql: str) -> bool:
    cleaned = sql.strip().strip(";")
    lowered = cleaned.lower()
    if not lowered.startswith("select"):
        return False
    blocked = ("insert ", "update ", "delete ", "drop ", "alter ", "create ", "truncate ", "attach ", "pragma ")
    if any(token in lowered for token in blocked):
        return False
    if ";" in cleaned:
        return False
    return True


def _get_llm_service() -> LLMService:
    provider = os.getenv("LLM_PROVIDER", "gemini").strip().lower()
    if provider not in {"gemini", "groq"}:
        raise ValueError("LLM_PROVIDER must be either 'gemini' or 'groq'.")
    return LLMService.from_provider(provider=provider)  # type: ignore[arg-type]


def run_nl_query(session: Session, user_query: str) -> QueryOutcome:
    if not user_query or not user_query.strip():
        return QueryOutcome(
            success=False,
            status="invalid_query",
            message="Query is empty.",
            user_query=user_query,
        )

    if not is_dataset_related(user_query):
        return QueryOutcome(
            success=False,
            status="invalid_query",
            message="Query is unrelated to the O2C dataset.",
            user_query=user_query,
        )

    try:
        llm_service = _get_llm_service()
    except Exception as exc:
        return QueryOutcome(
            success=False,
            status="llm_error",
            message=f"Unable to initialize LLM service: {exc}",
            user_query=user_query,
        )

    try:
        generated_sql = llm_service.natural_language_to_sql(schema=SCHEMA_TEXT, user_query=user_query)
    except Exception as exc:
        return QueryOutcome(
            success=False,
            status="llm_error",
            message=f"Failed to generate SQL: {exc}",
            user_query=user_query,
        )

    if generated_sql == "INVALID_QUERY":
        return QueryOutcome(
            success=False,
            status="invalid_query",
            message="The question cannot be mapped to this dataset schema.",
            user_query=user_query,
            generated_sql=generated_sql,
        )

    if not _is_safe_select_sql(generated_sql):
        return QueryOutcome(
            success=False,
            status="invalid_query",
            message="Generated SQL is not a safe SELECT query.",
            user_query=user_query,
            generated_sql=generated_sql,
        )

    try:
        result = session.execute(text(generated_sql))
        rows = [dict(row) for row in result.mappings().all()]
        columns = list(result.keys())
    except SQLAlchemyError as exc:
        return QueryOutcome(
            success=False,
            status="sql_error",
            message=f"SQL execution failed: {exc}",
            user_query=user_query,
            generated_sql=generated_sql,
        )

    if not rows:
        return QueryOutcome(
            success=True,
            status="empty_result",
            message="Query executed successfully but returned no rows.",
            user_query=user_query,
            generated_sql=generated_sql,
            row_count=0,
            data=[],
            answer="No matching records were found.",
        )

    try:
        answer = llm_service.sql_result_to_natural_language(
            user_query=user_query,
            sql=generated_sql,
            columns=columns,
            rows=rows,
        )
    except Exception as exc:
        return QueryOutcome(
            success=False,
            status="llm_error",
            message=f"Failed to summarize SQL result: {exc}",
            user_query=user_query,
            generated_sql=generated_sql,
            row_count=len(rows),
            data=rows,
        )

    return QueryOutcome(
        success=True,
        status="ok",
        message="Query executed successfully.",
        user_query=user_query,
        generated_sql=generated_sql,
        row_count=len(rows),
        data=rows,
        answer=answer,
    )
