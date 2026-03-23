from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    ForeignKeyConstraint,
    Numeric,
    PrimaryKeyConstraint,
    String,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class BusinessPartner(Base):
    __tablename__ = "business_partner"

    business_partner_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    customer_code: Mapped[Optional[str]] = mapped_column(String(20), unique=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    category: Mapped[Optional[str]] = mapped_column(String(4))
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    addresses: Mapped[List["BusinessPartnerAddress"]] = relationship(back_populates="business_partner")
    sales_areas: Mapped[List["CustomerSalesArea"]] = relationship(back_populates="customer")
    company_assignments: Mapped[List["CustomerCompany"]] = relationship(back_populates="customer")
    sales_orders: Mapped[List["SalesOrder"]] = relationship(back_populates="sold_to_party")
    billing_documents: Mapped[List["BillingDocument"]] = relationship(back_populates="sold_to_party")
    journal_entries_ar: Mapped[List["JournalEntryARLine"]] = relationship(back_populates="customer")
    ar_clearing_lines: Mapped[List["ARClearingLine"]] = relationship(back_populates="customer")


class BusinessPartnerAddress(Base):
    __tablename__ = "business_partner_address"

    business_partner_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id"), nullable=False
    )
    address_id: Mapped[str] = mapped_column(String(20), nullable=False)
    address_uuid: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    valid_from: Mapped[Optional[datetime]] = mapped_column(DateTime)
    valid_to: Mapped[Optional[datetime]] = mapped_column(DateTime)
    city: Mapped[Optional[str]] = mapped_column(String(120))
    country: Mapped[Optional[str]] = mapped_column(String(8))
    postal_code: Mapped[Optional[str]] = mapped_column(String(20))
    region: Mapped[Optional[str]] = mapped_column(String(20))
    street: Mapped[Optional[str]] = mapped_column(String(255))

    __table_args__ = (PrimaryKeyConstraint("business_partner_id", "address_id"),)

    business_partner: Mapped["BusinessPartner"] = relationship(back_populates="addresses")


class CustomerSalesArea(Base):
    __tablename__ = "customer_sales_area"

    customer_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id"), nullable=False
    )
    sales_organization: Mapped[str] = mapped_column(String(10), nullable=False)
    distribution_channel: Mapped[str] = mapped_column(String(10), nullable=False)
    division: Mapped[str] = mapped_column(String(10), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(8))
    payment_terms: Mapped[Optional[str]] = mapped_column(String(20))
    incoterms_code: Mapped[Optional[str]] = mapped_column(String(20))
    incoterms_location: Mapped[Optional[str]] = mapped_column(String(120))
    shipping_condition: Mapped[Optional[str]] = mapped_column(String(20))
    delivery_priority: Mapped[Optional[str]] = mapped_column(String(20))

    __table_args__ = (
        PrimaryKeyConstraint(
            "customer_id", "sales_organization", "distribution_channel", "division"
        ),
    )

    customer: Mapped["BusinessPartner"] = relationship(back_populates="sales_areas")


class CustomerCompany(Base):
    __tablename__ = "customer_company"

    customer_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id"), nullable=False
    )
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    reconciliation_account: Mapped[Optional[str]] = mapped_column(String(20))
    customer_account_group: Mapped[Optional[str]] = mapped_column(String(20))
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    __table_args__ = (PrimaryKeyConstraint("customer_id", "company_code"),)

    customer: Mapped["BusinessPartner"] = relationship(back_populates="company_assignments")


class Plant(Base):
    __tablename__ = "plant"

    plant_id: Mapped[str] = mapped_column(String(10), primary_key=True)
    plant_name: Mapped[Optional[str]] = mapped_column(String(255))
    sales_organization: Mapped[Optional[str]] = mapped_column(String(10))
    distribution_channel: Mapped[Optional[str]] = mapped_column(String(10))
    division: Mapped[Optional[str]] = mapped_column(String(10))

    product_plants: Mapped[List["ProductPlant"]] = relationship(back_populates="plant")
    product_storage_locations: Mapped[List["ProductStorageLocation"]] = relationship(back_populates="plant")
    sales_order_items: Mapped[List["SalesOrderItem"]] = relationship(back_populates="production_plant")
    delivery_items: Mapped[List["OutboundDeliveryItem"]] = relationship(back_populates="plant")


class Product(Base):
    __tablename__ = "product"

    product_id: Mapped[str] = mapped_column(String(40), primary_key=True)
    product_type: Mapped[Optional[str]] = mapped_column(String(20))
    product_group: Mapped[Optional[str]] = mapped_column(String(30))
    base_unit: Mapped[Optional[str]] = mapped_column(String(10))
    division: Mapped[Optional[str]] = mapped_column(String(10))
    industry_sector: Mapped[Optional[str]] = mapped_column(String(10))
    net_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    gross_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    weight_unit: Mapped[Optional[str]] = mapped_column(String(10))
    is_marked_for_deletion: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    descriptions: Mapped[List["ProductDescription"]] = relationship(back_populates="product")
    product_plants: Mapped[List["ProductPlant"]] = relationship(back_populates="product")
    product_storage_locations: Mapped[List["ProductStorageLocation"]] = relationship(back_populates="product")
    sales_order_items: Mapped[List["SalesOrderItem"]] = relationship(back_populates="product")
    billing_document_items: Mapped[List["BillingDocumentItem"]] = relationship(back_populates="product")


class ProductDescription(Base):
    __tablename__ = "product_description"

    product_id: Mapped[str] = mapped_column(String(40), ForeignKey("product.product_id"), nullable=False)
    language: Mapped[str] = mapped_column(String(8), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)

    __table_args__ = (PrimaryKeyConstraint("product_id", "language"),)

    product: Mapped["Product"] = relationship(back_populates="descriptions")


class ProductPlant(Base):
    __tablename__ = "product_plant"

    product_id: Mapped[str] = mapped_column(String(40), ForeignKey("product.product_id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(String(10), ForeignKey("plant.plant_id"), nullable=False)
    availability_check_type: Mapped[Optional[str]] = mapped_column(String(10))
    mrp_type: Mapped[Optional[str]] = mapped_column(String(10))
    profit_center: Mapped[Optional[str]] = mapped_column(String(20))

    __table_args__ = (PrimaryKeyConstraint("product_id", "plant_id"),)

    product: Mapped["Product"] = relationship(back_populates="product_plants")
    plant: Mapped["Plant"] = relationship(back_populates="product_plants")


class ProductStorageLocation(Base):
    __tablename__ = "product_storage_location"

    product_id: Mapped[str] = mapped_column(String(40), ForeignKey("product.product_id"), nullable=False)
    plant_id: Mapped[str] = mapped_column(String(10), ForeignKey("plant.plant_id"), nullable=False)
    storage_location_code: Mapped[str] = mapped_column(String(12), nullable=False)
    inventory_block_indicator: Mapped[Optional[str]] = mapped_column(String(10))
    last_count_posted_date: Mapped[Optional[date]] = mapped_column(Date)

    __table_args__ = (
        PrimaryKeyConstraint("product_id", "plant_id", "storage_location_code"),
    )

    product: Mapped["Product"] = relationship(back_populates="product_storage_locations")
    plant: Mapped["Plant"] = relationship(back_populates="product_storage_locations")


class SalesOrder(Base):
    __tablename__ = "sales_order"

    sales_order_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    sold_to_party_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id"), nullable=False
    )
    sales_order_type: Mapped[Optional[str]] = mapped_column(String(10))
    sales_organization: Mapped[Optional[str]] = mapped_column(String(10))
    distribution_channel: Mapped[Optional[str]] = mapped_column(String(10))
    division: Mapped[Optional[str]] = mapped_column(String(10))
    transaction_currency: Mapped[Optional[str]] = mapped_column(String(8))
    total_net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    created_on: Mapped[Optional[date]] = mapped_column(Date)
    requested_delivery_date: Mapped[Optional[date]] = mapped_column(Date)

    sold_to_party: Mapped["BusinessPartner"] = relationship(back_populates="sales_orders")
    items: Mapped[List["SalesOrderItem"]] = relationship(back_populates="sales_order")


class SalesOrderItem(Base):
    __tablename__ = "sales_order_item"

    sales_order_id: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(10), nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("product.product_id"))
    production_plant_id: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("plant.plant_id"))
    storage_location_code: Mapped[Optional[str]] = mapped_column(String(12))
    order_item_category: Mapped[Optional[str]] = mapped_column(String(10))
    requested_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(10))
    transaction_currency: Mapped[Optional[str]] = mapped_column(String(8))
    net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    __table_args__ = (
        PrimaryKeyConstraint("sales_order_id", "item_no"),
        ForeignKeyConstraint(["sales_order_id"], ["sales_order.sales_order_id"]),
    )

    sales_order: Mapped["SalesOrder"] = relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(back_populates="sales_order_items")
    production_plant: Mapped[Optional["Plant"]] = relationship(back_populates="sales_order_items")
    schedule_lines: Mapped[List["SalesOrderScheduleLine"]] = relationship(back_populates="sales_order_item")
    delivery_items: Mapped[List["OutboundDeliveryItem"]] = relationship(back_populates="sales_order_item")


class SalesOrderScheduleLine(Base):
    __tablename__ = "sales_order_schedule_line"

    sales_order_id: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(10), nullable=False)
    schedule_line_no: Mapped[str] = mapped_column(String(10), nullable=False)
    confirmed_delivery_date: Mapped[Optional[date]] = mapped_column(Date)
    confirmed_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(10))

    __table_args__ = (
        PrimaryKeyConstraint("sales_order_id", "item_no", "schedule_line_no"),
        ForeignKeyConstraint(
            ["sales_order_id", "item_no"],
            ["sales_order_item.sales_order_id", "sales_order_item.item_no"],
        ),
    )

    sales_order_item: Mapped["SalesOrderItem"] = relationship(back_populates="schedule_lines")


class OutboundDelivery(Base):
    __tablename__ = "outbound_delivery"

    delivery_document_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    created_on: Mapped[Optional[date]] = mapped_column(Date)
    goods_movement_date: Mapped[Optional[date]] = mapped_column(Date)
    shipping_point: Mapped[Optional[str]] = mapped_column(String(20))
    overall_goods_movement_status: Mapped[Optional[str]] = mapped_column(String(10))
    overall_picking_status: Mapped[Optional[str]] = mapped_column(String(10))

    items: Mapped[List["OutboundDeliveryItem"]] = relationship(back_populates="delivery")


class OutboundDeliveryItem(Base):
    __tablename__ = "outbound_delivery_item"

    delivery_document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(10), nullable=False)
    sales_order_id: Mapped[Optional[str]] = mapped_column(String(20))
    sales_order_item_no: Mapped[Optional[str]] = mapped_column(String(10))
    plant_id: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("plant.plant_id"))
    storage_location_code: Mapped[Optional[str]] = mapped_column(String(12))
    actual_delivery_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(10))

    __table_args__ = (
        PrimaryKeyConstraint("delivery_document_id", "item_no"),
        ForeignKeyConstraint(["delivery_document_id"], ["outbound_delivery.delivery_document_id"]),
        ForeignKeyConstraint(
            ["sales_order_id", "sales_order_item_no"],
            ["sales_order_item.sales_order_id", "sales_order_item.item_no"],
        ),
    )

    delivery: Mapped["OutboundDelivery"] = relationship(back_populates="items")
    sales_order_item: Mapped[Optional["SalesOrderItem"]] = relationship(back_populates="delivery_items")
    plant: Mapped[Optional["Plant"]] = relationship(back_populates="delivery_items")
    billing_items: Mapped[List["BillingDocumentItem"]] = relationship(back_populates="delivery_item")


class AccountingDocument(Base):
    __tablename__ = "accounting_document"

    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(4), nullable=False)
    accounting_document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    posting_date: Mapped[Optional[date]] = mapped_column(Date)
    document_date: Mapped[Optional[date]] = mapped_column(Date)

    __table_args__ = (
        PrimaryKeyConstraint("company_code", "fiscal_year", "accounting_document_id"),
    )

    billing_documents: Mapped[List["BillingDocument"]] = relationship(back_populates="accounting_document")
    journal_entries_ar: Mapped[List["JournalEntryARLine"]] = relationship(back_populates="accounting_document")
    ar_clearing_lines: Mapped[List["ARClearingLine"]] = relationship(back_populates="accounting_document")


class BillingDocument(Base):
    __tablename__ = "billing_document"

    billing_document_id: Mapped[str] = mapped_column(String(20), primary_key=True)
    sold_to_party_id: Mapped[str] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id"), nullable=False
    )
    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(4), nullable=False)
    accounting_document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    billing_document_type: Mapped[Optional[str]] = mapped_column(String(10))
    billing_date: Mapped[Optional[date]] = mapped_column(Date)
    transaction_currency: Mapped[Optional[str]] = mapped_column(String(8))
    total_net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    is_cancelled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    cancelled_billing_document_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("billing_document.billing_document_id")
    )

    __table_args__ = (
        ForeignKeyConstraint(
            ["company_code", "fiscal_year", "accounting_document_id"],
            [
                "accounting_document.company_code",
                "accounting_document.fiscal_year",
                "accounting_document.accounting_document_id",
            ],
        ),
    )

    sold_to_party: Mapped["BusinessPartner"] = relationship(back_populates="billing_documents")
    accounting_document: Mapped["AccountingDocument"] = relationship(back_populates="billing_documents")
    cancelled_billing_document: Mapped[Optional["BillingDocument"]] = relationship(
        remote_side=[billing_document_id]
    )
    items: Mapped[List["BillingDocumentItem"]] = relationship(back_populates="billing_document")
    journal_entries_ar: Mapped[List["JournalEntryARLine"]] = relationship(back_populates="billing_document")


class BillingDocumentItem(Base):
    __tablename__ = "billing_document_item"

    billing_document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    item_no: Mapped[str] = mapped_column(String(10), nullable=False)
    product_id: Mapped[Optional[str]] = mapped_column(String(40), ForeignKey("product.product_id"))
    delivery_document_id: Mapped[Optional[str]] = mapped_column(String(20))
    delivery_item_no: Mapped[Optional[str]] = mapped_column(String(10))
    billing_quantity: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 3))
    quantity_unit: Mapped[Optional[str]] = mapped_column(String(10))
    transaction_currency: Mapped[Optional[str]] = mapped_column(String(8))
    net_amount: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))

    __table_args__ = (
        PrimaryKeyConstraint("billing_document_id", "item_no"),
        ForeignKeyConstraint(["billing_document_id"], ["billing_document.billing_document_id"]),
        ForeignKeyConstraint(
            ["delivery_document_id", "delivery_item_no"],
            ["outbound_delivery_item.delivery_document_id", "outbound_delivery_item.item_no"],
        ),
    )

    billing_document: Mapped["BillingDocument"] = relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = relationship(back_populates="billing_document_items")
    delivery_item: Mapped[Optional["OutboundDeliveryItem"]] = relationship(back_populates="billing_items")


class JournalEntryARLine(Base):
    __tablename__ = "journal_entry_ar_line"

    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(4), nullable=False)
    accounting_document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    accounting_document_item: Mapped[str] = mapped_column(String(10), nullable=False)
    gl_account: Mapped[str] = mapped_column(String(20), nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id")
    )
    reference_billing_document_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("billing_document.billing_document_id")
    )
    posting_date: Mapped[Optional[date]] = mapped_column(Date)
    document_date: Mapped[Optional[date]] = mapped_column(Date)
    transaction_currency: Mapped[Optional[str]] = mapped_column(String(8))
    amount_in_transaction_currency: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    clearing_date: Mapped[Optional[date]] = mapped_column(Date)
    clearing_accounting_document_id: Mapped[Optional[str]] = mapped_column(String(20))
    clearing_doc_fiscal_year: Mapped[Optional[str]] = mapped_column(String(4))

    __table_args__ = (
        PrimaryKeyConstraint(
            "company_code",
            "fiscal_year",
            "accounting_document_id",
            "accounting_document_item",
            "gl_account",
        ),
        ForeignKeyConstraint(
            ["company_code", "fiscal_year", "accounting_document_id"],
            [
                "accounting_document.company_code",
                "accounting_document.fiscal_year",
                "accounting_document.accounting_document_id",
            ],
        ),
    )

    accounting_document: Mapped["AccountingDocument"] = relationship(back_populates="journal_entries_ar")
    customer: Mapped[Optional["BusinessPartner"]] = relationship(back_populates="journal_entries_ar")
    billing_document: Mapped[Optional["BillingDocument"]] = relationship(back_populates="journal_entries_ar")


class ARClearingLine(Base):
    __tablename__ = "ar_clearing_line"

    company_code: Mapped[str] = mapped_column(String(10), nullable=False)
    fiscal_year: Mapped[str] = mapped_column(String(4), nullable=False)
    accounting_document_id: Mapped[str] = mapped_column(String(20), nullable=False)
    accounting_document_item: Mapped[str] = mapped_column(String(10), nullable=False)
    customer_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("business_partner.business_partner_id")
    )
    invoice_reference_id: Mapped[Optional[str]] = mapped_column(
        String(20), ForeignKey("billing_document.billing_document_id")
    )
    sales_document_id: Mapped[Optional[str]] = mapped_column(String(20))
    sales_document_item_no: Mapped[Optional[str]] = mapped_column(String(10))
    posting_date: Mapped[Optional[date]] = mapped_column(Date)
    document_date: Mapped[Optional[date]] = mapped_column(Date)
    transaction_currency: Mapped[Optional[str]] = mapped_column(String(8))
    amount_in_transaction_currency: Mapped[Optional[Decimal]] = mapped_column(Numeric(18, 2))
    clearing_date: Mapped[Optional[date]] = mapped_column(Date)
    clearing_accounting_document_id: Mapped[Optional[str]] = mapped_column(String(20))
    clearing_doc_fiscal_year: Mapped[Optional[str]] = mapped_column(String(4))

    __table_args__ = (
        PrimaryKeyConstraint(
            "company_code",
            "fiscal_year",
            "accounting_document_id",
            "accounting_document_item",
        ),
        ForeignKeyConstraint(
            ["company_code", "fiscal_year", "accounting_document_id"],
            [
                "accounting_document.company_code",
                "accounting_document.fiscal_year",
                "accounting_document.accounting_document_id",
            ],
        ),
    )

    accounting_document: Mapped["AccountingDocument"] = relationship(back_populates="ar_clearing_lines")
    customer: Mapped[Optional["BusinessPartner"]] = relationship(back_populates="ar_clearing_lines")
