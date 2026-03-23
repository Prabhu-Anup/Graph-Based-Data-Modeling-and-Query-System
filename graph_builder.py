from __future__ import annotations

from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from models import (
    ARClearingLine,
    BillingDocument,
    BillingDocumentItem,
    BusinessPartner,
    OutboundDelivery,
    OutboundDeliveryItem,
    Product,
    SalesOrder,
    SalesOrderItem,
)


def _to_number(value: Optional[Decimal]) -> Optional[float]:
    if value is None:
        return None
    return float(value)


def _to_quantity(value: Optional[Decimal]) -> Optional[float | int]:
    if value is None:
        return None
    as_float = float(value)
    if as_float.is_integer():
        return int(as_float)
    return as_float


def _add_node(
    nodes: List[Dict[str, Any]],
    seen: Set[str],
    node_id: str,
    node_type: str,
    metadata: Dict[str, Any],
) -> bool:
    if node_id in seen:
        return False
    seen.add(node_id)
    nodes.append({"id": node_id, "type": node_type, "metadata": metadata})
    return True


def _add_edge(
    edges: List[Dict[str, str]],
    seen: Set[Tuple[str, str, str]],
    node_seen: Set[str],
    source: str,
    target: str,
    edge_type: str,
) -> bool:
    if source not in node_seen or target not in node_seen:
        return False
    edge_key = (source, target, edge_type)
    if edge_key in seen:
        return False
    seen.add(edge_key)
    edges.append({"source": source, "target": target, "type": edge_type})
    return True


def build_graph(session: Session) -> Dict[str, List[Dict[str, Any]]]:
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, str]] = []
    node_seen: Set[str] = set()
    edge_seen: Set[Tuple[str, str, str]] = set()

    customers = session.scalars(select(BusinessPartner)).all()
    orders = session.scalars(select(SalesOrder)).all()
    order_items = session.scalars(select(SalesOrderItem)).all()
    products = session.scalars(select(Product)).all()
    deliveries = session.scalars(select(OutboundDelivery)).all()
    delivery_items = session.scalars(select(OutboundDeliveryItem)).all()
    invoices = session.scalars(select(BillingDocument)).all()
    invoice_items = session.scalars(select(BillingDocumentItem)).all()
    payments = session.scalars(select(ARClearingLine)).all()

    print("[graph_builder] source customers:", len(customers))
    print("[graph_builder] source orders:", len(orders))
    print("[graph_builder] source order_items:", len(order_items))
    print("[graph_builder] source products:", len(products))
    print("[graph_builder] source deliveries:", len(deliveries))
    print("[graph_builder] source invoices:", len(invoices))
    print("[graph_builder] source payments:", len(payments))

    node_counts = {
        "Customer": 0,
        "Order": 0,
        "OrderItem": 0,
        "Product": 0,
        "Delivery": 0,
        "Invoice": 0,
        "Payment": 0,
    }
    edge_counts = {
        "Customer→Order": 0,
        "Order→Item": 0,
        "Item→Product": 0,
        "Order→Delivery": 0,
        "Delivery→Invoice": 0,
        "Invoice→Payment": 0,
    }

    for c in customers:
        customer_node_id = f"customer:{c.business_partner_id}"
        added = _add_node(
            nodes,
            node_seen,
            customer_node_id,
            "Customer",
            {
                "business_partner_id": c.business_partner_id,
                "name": c.full_name,
                "customer_code": c.customer_code,
                "is_blocked": c.is_blocked,
            },
        )
        if added:
            node_counts["Customer"] += 1

    for p in products:
        added = _add_node(
            nodes,
            node_seen,
            f"product:{p.product_id}",
            "Product",
            {
                "product_id": p.product_id,
                "product_type": p.product_type,
                "product_group": p.product_group,
                "base_unit": p.base_unit,
            },
        )
        if added:
            node_counts["Product"] += 1

    for o in orders:
        order_node_id = f"order:{o.sales_order_id}"
        added = _add_node(
            nodes,
            node_seen,
            order_node_id,
            "Order",
            {
                "sales_order_id": o.sales_order_id,
                "currency": o.transaction_currency,
                "total_net_amount": _to_number(o.total_net_amount),
            },
        )
        if added:
            node_counts["Order"] += 1

    for oi in order_items:
        order_item_node_id = f"order_item:{oi.sales_order_id}:{oi.item_no}"
        net_amount_value = _to_number(oi.net_amount)
        added = _add_node(
            nodes,
            node_seen,
            order_item_node_id,
            "OrderItem",
            {
                "sales_order_id": oi.sales_order_id,
                "item_no": oi.item_no,
                "quantity": _to_quantity(oi.requested_quantity),
                "net_amount": net_amount_value,
                "is_free_item": bool(net_amount_value == 0.0),
            },
        )
        if added:
            node_counts["OrderItem"] += 1

    for d in deliveries:
        added = _add_node(
            nodes,
            node_seen,
            f"delivery:{d.delivery_document_id}",
            "Delivery",
            {
                "delivery_document_id": d.delivery_document_id,
                "created_on": d.created_on.isoformat() if d.created_on else None,
                "shipping_point": d.shipping_point,
            },
        )
        if added:
            node_counts["Delivery"] += 1

    for inv in invoices:
        added = _add_node(
            nodes,
            node_seen,
            f"invoice:{inv.billing_document_id}",
            "Invoice",
            {
                "billing_document_id": inv.billing_document_id,
                "billing_date": inv.billing_date.isoformat() if inv.billing_date else None,
                "total_net_amount": _to_number(inv.total_net_amount),
                "currency": inv.transaction_currency,
            },
        )
        if added:
            node_counts["Invoice"] += 1

    for pay in payments:
        payment_node_id = (
            f"payment:{pay.company_code}:{pay.fiscal_year}:{pay.accounting_document_id}:{pay.accounting_document_item}"
        )
        added = _add_node(
            nodes,
            node_seen,
            payment_node_id,
            "Payment",
            {
                "company_code": pay.company_code,
                "fiscal_year": pay.fiscal_year,
                "accounting_document_id": pay.accounting_document_id,
                "accounting_document_item": pay.accounting_document_item,
                "amount": _to_number(pay.amount_in_transaction_currency),
                "currency": pay.transaction_currency,
                "clearing_document_id": pay.clearing_accounting_document_id,
            },
        )
        if added:
            node_counts["Payment"] += 1

    # Relationship edges (only when both source and target nodes exist).
    for o in orders:
        if o.sold_to_party_id:
            added = _add_edge(
                edges,
                edge_seen,
                node_seen,
                f"customer:{o.sold_to_party_id}",
                f"order:{o.sales_order_id}",
                "PLACED",
            )
            if added:
                edge_counts["Customer→Order"] += 1

    for oi in order_items:
        order_item_node_id = f"order_item:{oi.sales_order_id}:{oi.item_no}"
        added = _add_edge(
            edges,
            edge_seen,
            node_seen,
            f"order:{oi.sales_order_id}",
            order_item_node_id,
            "CONTAINS",
        )
        if added:
            edge_counts["Order→Item"] += 1
        if oi.product_id:
            added = _add_edge(
                edges,
                edge_seen,
                node_seen,
                order_item_node_id,
                f"product:{oi.product_id}",
                "OF_PRODUCT",
            )
            if added:
                edge_counts["Item→Product"] += 1

    for di in delivery_items:
        if di.sales_order_id and di.delivery_document_id:
            added = _add_edge(
                edges,
                edge_seen,
                node_seen,
                f"order:{di.sales_order_id}",
                f"delivery:{di.delivery_document_id}",
                "ORDER_TO_DELIVERY",
            )
            if added:
                edge_counts["Order→Delivery"] += 1

    for inv_item in invoice_items:
        if inv_item.delivery_document_id and inv_item.billing_document_id:
            added = _add_edge(
                edges,
                edge_seen,
                node_seen,
                f"delivery:{inv_item.delivery_document_id}",
                f"invoice:{inv_item.billing_document_id}",
                "DELIVERY_TO_INVOICE",
            )
            if added:
                edge_counts["Delivery→Invoice"] += 1

    for pay in payments:
        if pay.invoice_reference_id:
            payment_node_id = f"payment:{pay.company_code}:{pay.fiscal_year}:{pay.accounting_document_id}:{pay.accounting_document_item}"
            added = _add_edge(
                edges,
                edge_seen,
                node_seen,
                f"invoice:{pay.invoice_reference_id}",
                payment_node_id,
                "INVOICE_TO_PAYMENT",
            )
            if added:
                edge_counts["Invoice→Payment"] += 1

    for entity_name, count in node_counts.items():
        print(f"[graph_builder] nodes {entity_name}: {count}")
    print("Customer→Order edges:", edge_counts["Customer→Order"])
    print("Order→Item edges:", edge_counts["Order→Item"])
    print("Item→Product edges:", edge_counts["Item→Product"])
    print("Order→Delivery edges:", edge_counts["Order→Delivery"])
    print("Delivery→Invoice edges:", edge_counts["Delivery→Invoice"])
    print("Invoice→Payment edges:", edge_counts["Invoice→Payment"])
    print("Nodes:", len(nodes))
    print("Edges:", len(edges))

    return {
        "nodes": nodes,
        "edges": edges
    }
