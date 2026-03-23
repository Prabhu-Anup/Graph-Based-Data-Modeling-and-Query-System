from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional

from database import SessionLocal, init_db
from models import (
    ARClearingLine,
    AccountingDocument,
    BillingDocument,
    BillingDocumentItem,
    BusinessPartner,
    BusinessPartnerAddress,
    CustomerCompany,
    CustomerSalesArea,
    JournalEntryARLine,
    OutboundDelivery,
    OutboundDeliveryItem,
    Plant,
    Product,
    ProductDescription,
    ProductPlant,
    ProductStorageLocation,
    SalesOrder,
    SalesOrderItem,
    SalesOrderScheduleLine,
)


DATASET_DIR = Path(__file__).resolve().parent / "sap-o2c-data"


@dataclass(frozen=True)
class LoadStats:
    table: str
    loaded: int


def _clean(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, str):
        value = value.strip()
        if value in {"", "null", "NULL", "None"}:
            return None
    return value


def _as_str(value: Any) -> Optional[str]:
    value = _clean(value)
    if value is None:
        return None
    return str(value)


def _as_bool(value: Any, default: bool = False) -> bool:
    value = _clean(value)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    return text in {"true", "1", "yes", "y", "t"}


def _as_decimal(value: Any) -> Optional[Decimal]:
    value = _clean(value)
    if value is None:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None


def _as_date(value: Any) -> Optional[date]:
    value = _clean(value)
    if value is None:
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value)
    try:
        if "T" in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
        return date.fromisoformat(text)
    except ValueError:
        return None


def _as_datetime(value: Any) -> Optional[datetime]:
    value = _clean(value)
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return datetime.combine(value, datetime.min.time())
    text = str(value)
    try:
        if "T" in text:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        return datetime.combine(date.fromisoformat(text), datetime.min.time())
    except ValueError:
        return None


def _iter_rows(path: Path) -> Iterator[Dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".jsonl":
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        yield row
                except json.JSONDecodeError:
                    continue
        return

    if suffix == ".json":
        with path.open("r", encoding="utf-8") as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError:
                return
        if isinstance(payload, list):
            for row in payload:
                if isinstance(row, dict):
                    yield row
        elif isinstance(payload, dict):
            yield payload
        return

    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if isinstance(row, dict):
                    yield row
        return

    if suffix in {".xlsx", ".xls"}:
        try:
            import pandas as pd  # type: ignore
        except Exception as exc:  # pragma: no cover
            raise RuntimeError(
                "Excel loading requires pandas/openpyxl. Install with: pip install pandas openpyxl"
            ) from exc
        frame = pd.read_excel(path)
        for row in frame.to_dict(orient="records"):
            if isinstance(row, dict):
                yield row
        return


def _entity_files(dataset_root: Path, entity_name: str) -> List[Path]:
    entity_path = dataset_root / entity_name
    if not entity_path.exists():
        return []
    files = [
        p
        for p in entity_path.rglob("*")
        if p.is_file() and p.suffix.lower() in {".jsonl", ".json", ".csv", ".xlsx", ".xls"}
    ]
    files.sort()
    return files


def _ensure_accounting_document(
    session,
    company_code: Optional[str],
    fiscal_year: Optional[str],
    accounting_document_id: Optional[str],
    posting_date: Optional[date] = None,
    document_date: Optional[date] = None,
) -> None:
    if not company_code or not fiscal_year or not accounting_document_id:
        return
    obj = AccountingDocument(
        company_code=company_code,
        fiscal_year=fiscal_year,
        accounting_document_id=accounting_document_id,
        posting_date=posting_date,
        document_date=document_date,
    )
    session.merge(obj)


def _load_business_partners(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "business_partners"):
        for row in _iter_rows(path):
            bp_id = _as_str(row.get("businessPartner")) or _as_str(row.get("customer"))
            if not bp_id:
                continue
            obj = BusinessPartner(
                business_partner_id=bp_id,
                customer_code=_as_str(row.get("customer")),
                full_name=_as_str(row.get("businessPartnerFullName")) or _as_str(row.get("businessPartnerName")),
                category=_as_str(row.get("businessPartnerCategory")),
                is_blocked=_as_bool(row.get("businessPartnerIsBlocked"), False),
                is_archived=_as_bool(row.get("isMarkedForArchiving"), False),
                created_at=_as_datetime(row.get("creationDate")),
                updated_at=_as_datetime(row.get("lastChangeDate")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_business_partner_addresses(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "business_partner_addresses"):
        for row in _iter_rows(path):
            bp_id = _as_str(row.get("businessPartner"))
            address_id = _as_str(row.get("addressId"))
            if not bp_id or not address_id:
                continue
            obj = BusinessPartnerAddress(
                business_partner_id=bp_id,
                address_id=address_id,
                address_uuid=_as_str(row.get("addressUuid")),
                valid_from=_as_datetime(row.get("validityStartDate")),
                valid_to=_as_datetime(row.get("validityEndDate")),
                city=_as_str(row.get("cityName")),
                country=_as_str(row.get("country")),
                postal_code=_as_str(row.get("postalCode")),
                region=_as_str(row.get("region")),
                street=_as_str(row.get("streetName")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_customer_sales_area(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "customer_sales_area_assignments"):
        for row in _iter_rows(path):
            customer_id = _as_str(row.get("customer"))
            sales_org = _as_str(row.get("salesOrganization"))
            dist_channel = _as_str(row.get("distributionChannel"))
            division = _as_str(row.get("division"))
            if not all([customer_id, sales_org, dist_channel, division]):
                continue
            obj = CustomerSalesArea(
                customer_id=customer_id,
                sales_organization=sales_org,
                distribution_channel=dist_channel,
                division=division,
                currency=_as_str(row.get("currency")),
                payment_terms=_as_str(row.get("customerPaymentTerms")),
                incoterms_code=_as_str(row.get("incotermsClassification")),
                incoterms_location=_as_str(row.get("incotermsLocation1")),
                shipping_condition=_as_str(row.get("shippingCondition")),
                delivery_priority=_as_str(row.get("deliveryPriority")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_customer_company(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "customer_company_assignments"):
        for row in _iter_rows(path):
            customer_id = _as_str(row.get("customer"))
            company_code = _as_str(row.get("companyCode"))
            if not customer_id or not company_code:
                continue
            obj = CustomerCompany(
                customer_id=customer_id,
                company_code=company_code,
                reconciliation_account=_as_str(row.get("reconciliationAccount")),
                customer_account_group=_as_str(row.get("customerAccountGroup")),
                is_deleted=_as_bool(row.get("deletionIndicator"), False),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_plants(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "plants"):
        for row in _iter_rows(path):
            plant_id = _as_str(row.get("plant"))
            if not plant_id:
                continue
            obj = Plant(
                plant_id=plant_id,
                plant_name=_as_str(row.get("plantName")),
                sales_organization=_as_str(row.get("salesOrganization")),
                distribution_channel=_as_str(row.get("distributionChannel")),
                division=_as_str(row.get("division")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_products(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "products"):
        for row in _iter_rows(path):
            product_id = _as_str(row.get("product"))
            if not product_id:
                continue
            obj = Product(
                product_id=product_id,
                product_type=_as_str(row.get("productType")),
                product_group=_as_str(row.get("productGroup")),
                base_unit=_as_str(row.get("baseUnit")),
                division=_as_str(row.get("division")),
                industry_sector=_as_str(row.get("industrySector")),
                net_weight=_as_decimal(row.get("netWeight")),
                gross_weight=_as_decimal(row.get("grossWeight")),
                weight_unit=_as_str(row.get("weightUnit")),
                is_marked_for_deletion=_as_bool(row.get("isMarkedForDeletion"), False),
                created_at=_as_datetime(row.get("creationDate")),
                updated_at=_as_datetime(row.get("lastChangeDateTime")) or _as_datetime(row.get("lastChangeDate")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_product_descriptions(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "product_descriptions"):
        for row in _iter_rows(path):
            product_id = _as_str(row.get("product"))
            language = _as_str(row.get("language"))
            description = _as_str(row.get("productDescription"))
            if not product_id or not language or not description:
                continue
            obj = ProductDescription(
                product_id=product_id,
                language=language,
                description=description,
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_product_plants(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "product_plants"):
        for row in _iter_rows(path):
            product_id = _as_str(row.get("product"))
            plant_id = _as_str(row.get("plant"))
            if not product_id or not plant_id:
                continue
            obj = ProductPlant(
                product_id=product_id,
                plant_id=plant_id,
                availability_check_type=_as_str(row.get("availabilityCheckType")),
                mrp_type=_as_str(row.get("mrpType")),
                profit_center=_as_str(row.get("profitCenter")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_product_storage_locations(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "product_storage_locations"):
        for row in _iter_rows(path):
            product_id = _as_str(row.get("product"))
            plant_id = _as_str(row.get("plant"))
            storage_location = _as_str(row.get("storageLocation"))
            if not product_id or not plant_id or not storage_location:
                continue
            obj = ProductStorageLocation(
                product_id=product_id,
                plant_id=plant_id,
                storage_location_code=storage_location,
                inventory_block_indicator=_as_str(row.get("physicalInventoryBlockInd")),
                last_count_posted_date=_as_date(row.get("dateOfLastPostedCntUnRstrcdStk")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_sales_orders(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "sales_order_headers"):
        for row in _iter_rows(path):
            sales_order_id = _as_str(row.get("salesOrder"))
            sold_to_party_id = _as_str(row.get("soldToParty"))
            if not sales_order_id or not sold_to_party_id:
                continue
            obj = SalesOrder(
                sales_order_id=sales_order_id,
                sold_to_party_id=sold_to_party_id,
                sales_order_type=_as_str(row.get("salesOrderType")),
                sales_organization=_as_str(row.get("salesOrganization")),
                distribution_channel=_as_str(row.get("distributionChannel")),
                division=_as_str(row.get("organizationDivision")),
                transaction_currency=_as_str(row.get("transactionCurrency")),
                total_net_amount=_as_decimal(row.get("totalNetAmount")),
                created_on=_as_date(row.get("creationDate")),
                requested_delivery_date=_as_date(row.get("requestedDeliveryDate")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_sales_order_items(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "sales_order_items"):
        for row in _iter_rows(path):
            sales_order_id = _as_str(row.get("salesOrder"))
            item_no = _as_str(row.get("salesOrderItem"))
            if not sales_order_id or not item_no:
                continue
            obj = SalesOrderItem(
                sales_order_id=sales_order_id,
                item_no=item_no.zfill(2),
                product_id=_as_str(row.get("material")),
                production_plant_id=_as_str(row.get("productionPlant")),
                storage_location_code=_as_str(row.get("storageLocation")),
                order_item_category=_as_str(row.get("salesOrderItemCategory")),
                requested_quantity=_as_decimal(row.get("requestedQuantity")),
                quantity_unit=_as_str(row.get("requestedQuantityUnit")),
                transaction_currency=_as_str(row.get("transactionCurrency")),
                net_amount=_as_decimal(row.get("netAmount")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_sales_order_schedule_lines(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "sales_order_schedule_lines"):
        for row in _iter_rows(path):
            sales_order_id = _as_str(row.get("salesOrder"))
            item_no = _as_str(row.get("salesOrderItem"))
            schedule_line_no = _as_str(row.get("scheduleLine"))
            if not sales_order_id or not item_no or not schedule_line_no:
                continue
            obj = SalesOrderScheduleLine(
                sales_order_id=sales_order_id,
                item_no=item_no.zfill(2),
                schedule_line_no=schedule_line_no,
                confirmed_delivery_date=_as_date(row.get("confirmedDeliveryDate")),
                confirmed_quantity=_as_decimal(row.get("confdOrderQtyByMatlAvailCheck")),
                quantity_unit=_as_str(row.get("orderQuantityUnit")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_outbound_deliveries(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "outbound_delivery_headers"):
        for row in _iter_rows(path):
            delivery_document_id = _as_str(row.get("deliveryDocument"))
            if not delivery_document_id:
                continue
            obj = OutboundDelivery(
                delivery_document_id=delivery_document_id,
                created_on=_as_date(row.get("creationDate")),
                goods_movement_date=_as_date(row.get("actualGoodsMovementDate")),
                shipping_point=_as_str(row.get("shippingPoint")),
                overall_goods_movement_status=_as_str(row.get("overallGoodsMovementStatus")),
                overall_picking_status=_as_str(row.get("overallPickingStatus")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_outbound_delivery_items(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "outbound_delivery_items"):
        for row in _iter_rows(path):
            delivery_document_id = _as_str(row.get("deliveryDocument"))
            item_no = _as_str(row.get("deliveryDocumentItem"))
            if not delivery_document_id or not item_no:
                continue
            obj = OutboundDeliveryItem(
                delivery_document_id=delivery_document_id,
                item_no=item_no.lstrip("0") or "0",
                sales_order_id=_as_str(row.get("referenceSdDocument")),
                sales_order_item_no=(_as_str(row.get("referenceSdDocumentItem")) or "").lstrip("0") or None,
                plant_id=_as_str(row.get("plant")),
                storage_location_code=_as_str(row.get("storageLocation")),
                actual_delivery_quantity=_as_decimal(row.get("actualDeliveryQuantity")),
                quantity_unit=_as_str(row.get("deliveryQuantityUnit")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_billing_documents(session, dataset_root: Path, folder_name: str) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, folder_name):
        for row in _iter_rows(path):
            billing_document_id = _as_str(row.get("billingDocument"))
            sold_to_party_id = _as_str(row.get("soldToParty"))
            company_code = _as_str(row.get("companyCode"))
            fiscal_year = _as_str(row.get("fiscalYear"))
            accounting_document_id = _as_str(row.get("accountingDocument"))
            if not billing_document_id or not sold_to_party_id or not company_code or not fiscal_year or not accounting_document_id:
                continue

            _ensure_accounting_document(
                session,
                company_code=company_code,
                fiscal_year=fiscal_year,
                accounting_document_id=accounting_document_id,
                posting_date=_as_date(row.get("billingDocumentDate")),
                document_date=_as_date(row.get("billingDocumentDate")),
            )

            obj = BillingDocument(
                billing_document_id=billing_document_id,
                sold_to_party_id=sold_to_party_id,
                company_code=company_code,
                fiscal_year=fiscal_year,
                accounting_document_id=accounting_document_id,
                billing_document_type=_as_str(row.get("billingDocumentType")),
                billing_date=_as_date(row.get("billingDocumentDate")),
                transaction_currency=_as_str(row.get("transactionCurrency")),
                total_net_amount=_as_decimal(row.get("totalNetAmount")),
                is_cancelled=_as_bool(row.get("billingDocumentIsCancelled"), False) or folder_name == "billing_document_cancellations",
                cancelled_billing_document_id=_as_str(row.get("cancelledBillingDocument")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_billing_document_items(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "billing_document_items"):
        for row in _iter_rows(path):
            billing_document_id = _as_str(row.get("billingDocument"))
            item_no = _as_str(row.get("billingDocumentItem"))
            if not billing_document_id or not item_no:
                continue
            obj = BillingDocumentItem(
                billing_document_id=billing_document_id,
                item_no=item_no.lstrip("0") or "0",
                product_id=_as_str(row.get("material")),
                delivery_document_id=_as_str(row.get("referenceSdDocument")),
                delivery_item_no=(_as_str(row.get("referenceSdDocumentItem")) or "").lstrip("0") or None,
                billing_quantity=_as_decimal(row.get("billingQuantity")),
                quantity_unit=_as_str(row.get("billingQuantityUnit")),
                transaction_currency=_as_str(row.get("transactionCurrency")),
                net_amount=_as_decimal(row.get("netAmount")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_journal_entry_ar_lines(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "journal_entry_items_accounts_receivable"):
        for row in _iter_rows(path):
            company_code = _as_str(row.get("companyCode"))
            fiscal_year = _as_str(row.get("fiscalYear"))
            accounting_document_id = _as_str(row.get("accountingDocument"))
            accounting_document_item = _as_str(row.get("accountingDocumentItem"))
            gl_account = _as_str(row.get("glAccount"))
            if not all([company_code, fiscal_year, accounting_document_id, accounting_document_item, gl_account]):
                continue

            _ensure_accounting_document(
                session,
                company_code=company_code,
                fiscal_year=fiscal_year,
                accounting_document_id=accounting_document_id,
                posting_date=_as_date(row.get("postingDate")),
                document_date=_as_date(row.get("documentDate")),
            )

            obj = JournalEntryARLine(
                company_code=company_code,
                fiscal_year=fiscal_year,
                accounting_document_id=accounting_document_id,
                accounting_document_item=accounting_document_item,
                gl_account=gl_account,
                customer_id=_as_str(row.get("customer")),
                reference_billing_document_id=_as_str(row.get("referenceDocument")),
                posting_date=_as_date(row.get("postingDate")),
                document_date=_as_date(row.get("documentDate")),
                transaction_currency=_as_str(row.get("transactionCurrency")),
                amount_in_transaction_currency=_as_decimal(row.get("amountInTransactionCurrency")),
                clearing_date=_as_date(row.get("clearingDate")),
                clearing_accounting_document_id=_as_str(row.get("clearingAccountingDocument")),
                clearing_doc_fiscal_year=_as_str(row.get("clearingDocFiscalYear")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _load_ar_clearing_lines(session, dataset_root: Path) -> int:
    loaded = 0
    for path in _entity_files(dataset_root, "payments_accounts_receivable"):
        for row in _iter_rows(path):
            company_code = _as_str(row.get("companyCode"))
            fiscal_year = _as_str(row.get("fiscalYear"))
            accounting_document_id = _as_str(row.get("accountingDocument"))
            accounting_document_item = _as_str(row.get("accountingDocumentItem"))
            if not all([company_code, fiscal_year, accounting_document_id, accounting_document_item]):
                continue

            _ensure_accounting_document(
                session,
                company_code=company_code,
                fiscal_year=fiscal_year,
                accounting_document_id=accounting_document_id,
                posting_date=_as_date(row.get("postingDate")),
                document_date=_as_date(row.get("documentDate")),
            )

            obj = ARClearingLine(
                company_code=company_code,
                fiscal_year=fiscal_year,
                accounting_document_id=accounting_document_id,
                accounting_document_item=accounting_document_item,
                customer_id=_as_str(row.get("customer")),
                invoice_reference_id=_as_str(row.get("invoiceReference")),
                sales_document_id=_as_str(row.get("salesDocument")),
                sales_document_item_no=_as_str(row.get("salesDocumentItem")),
                posting_date=_as_date(row.get("postingDate")),
                document_date=_as_date(row.get("documentDate")),
                transaction_currency=_as_str(row.get("transactionCurrency")),
                amount_in_transaction_currency=_as_decimal(row.get("amountInTransactionCurrency")),
                clearing_date=_as_date(row.get("clearingDate")),
                clearing_accounting_document_id=_as_str(row.get("clearingAccountingDocument")),
                clearing_doc_fiscal_year=_as_str(row.get("clearingDocFiscalYear")),
            )
            session.merge(obj)
            loaded += 1
    return loaded


def _commit(session, stats: List[LoadStats], table: str, count: int) -> None:
    session.commit()
    stats.append(LoadStats(table=table, loaded=count))


def load_data(dataset_root: Path | str = DATASET_DIR) -> List[LoadStats]:
    """
    Load O2C data files (JSONL/JSON/CSV/Excel) into the SQLAlchemy schema.

    The loader is idempotent for the same keys because it uses `session.merge`.
    """
    dataset_root = Path(dataset_root).resolve()
    if not dataset_root.exists():
        raise FileNotFoundError(f"Dataset folder not found: {dataset_root}")

    init_db()
    stats: List[LoadStats] = []
    with SessionLocal() as session:
        _commit(session, stats, "business_partner", _load_business_partners(session, dataset_root))
        _commit(session, stats, "business_partner_address", _load_business_partner_addresses(session, dataset_root))
        _commit(session, stats, "customer_sales_area", _load_customer_sales_area(session, dataset_root))
        _commit(session, stats, "customer_company", _load_customer_company(session, dataset_root))

        _commit(session, stats, "plant", _load_plants(session, dataset_root))
        _commit(session, stats, "product", _load_products(session, dataset_root))
        _commit(session, stats, "product_description", _load_product_descriptions(session, dataset_root))
        _commit(session, stats, "product_plant", _load_product_plants(session, dataset_root))
        _commit(session, stats, "product_storage_location", _load_product_storage_locations(session, dataset_root))

        _commit(session, stats, "sales_order", _load_sales_orders(session, dataset_root))
        _commit(session, stats, "sales_order_item", _load_sales_order_items(session, dataset_root))
        _commit(session, stats, "sales_order_schedule_line", _load_sales_order_schedule_lines(session, dataset_root))

        _commit(session, stats, "outbound_delivery", _load_outbound_deliveries(session, dataset_root))
        _commit(session, stats, "outbound_delivery_item", _load_outbound_delivery_items(session, dataset_root))

        _commit(session, stats, "billing_document", _load_billing_documents(session, dataset_root, "billing_document_headers"))
        _commit(session, stats, "billing_document (cancellations)", _load_billing_documents(session, dataset_root, "billing_document_cancellations"))
        _commit(session, stats, "billing_document_item", _load_billing_document_items(session, dataset_root))

        _commit(session, stats, "journal_entry_ar_line", _load_journal_entry_ar_lines(session, dataset_root))
        _commit(session, stats, "ar_clearing_line", _load_ar_clearing_lines(session, dataset_root))

    return stats


if __name__ == "__main__":
    results = load_data()
    total = 0
    for item in results:
        print(f"{item.table}: {item.loaded}")
        total += item.loaded
    print(f"Total rows processed: {total}")
