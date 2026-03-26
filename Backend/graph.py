import sqlite3
from database import get_connection

def build_graph():
    conn = get_connection()
    nodes = []
    edges = []
    node_ids = set()

    def add_node(node_id, label, entity_type, properties={}):
        if node_id not in node_ids:
            node_ids.add(node_id)
            nodes.append({
                "id": str(node_id),
                "label": str(label),
                "type": entity_type,
                "properties": properties
            })

    def add_edge(source, target, relationship):
        if str(source) in node_ids and str(target) in node_ids:
            edges.append({
                "source": str(source),
                "target": str(target),
                "relationship": relationship
            })

    # 1. SALES ORDER HEADERS
    rows = conn.execute("""
        SELECT salesOrder, soldToParty, salesOrderType,
               creationDate, totalNetAmount, transactionCurrency,
               overallDeliveryStatus, overallOrdReltdBillgStatus
        FROM sales_order_headers
    """).fetchall()

    for r in rows:
        add_node(
            f"SO_{r['salesOrder']}",
            f"SO: {r['salesOrder']}",
            "SalesOrder",
            {
                "salesOrder": r["salesOrder"],
                "soldToParty": r["soldToParty"],
                "type": r["salesOrderType"],
                "amount": r["totalNetAmount"],
                "currency": r["transactionCurrency"],
                "creationDate": r["creationDate"],
                "deliveryStatus": r["overallDeliveryStatus"],
                "billingStatus": r["overallOrdReltdBillgStatus"]
            }
        )

    # 2. SALES ORDER ITEMS
    rows = conn.execute("""
        SELECT salesOrder, salesOrderItem, material,
               requestedQuantity, netAmount, transactionCurrency
        FROM sales_order_items
    """).fetchall()

    for r in rows:
        item_id = f"SOI_{r['salesOrder']}_{r['salesOrderItem']}"
        add_node(
            item_id,
            f"SOItem: {r['salesOrderItem']}",
            "SalesOrderItem",
            {
                "salesOrder": r["salesOrder"],
                "item": r["salesOrderItem"],
                "material": r["material"],
                "quantity": r["requestedQuantity"],
                "amount": r["netAmount"]
            }
        )
        add_edge(f"SO_{r['salesOrder']}", item_id, "HAS_ITEM")

    # 3. DELIVERY HEADERS
    rows = conn.execute("""
        SELECT deliveryDocument, creationDate,
               overallGoodsMovementStatus, actualGoodsMovementDate
        FROM delivery_headers
    """).fetchall()

    for r in rows:
        add_node(
            f"DEL_{r['deliveryDocument']}",
            f"DEL: {r['deliveryDocument']}",
            "Delivery",
            {
                "deliveryDocument": r["deliveryDocument"],
                "creationDate": r["creationDate"],
                "goodsMovementStatus": r["overallGoodsMovementStatus"],
                "actualGoodsMovementDate": r["actualGoodsMovementDate"]
            }
        )

    # 4. DELIVERY ITEMS
    rows = conn.execute("""
        SELECT deliveryDocument, deliveryDocumentItem,
               referenceSdDocument, referenceSdDocumentItem,
               actualDeliveryQuantity, plant
        FROM delivery_items
    """).fetchall()

    for r in rows:
        item_id = f"DELI_{r['deliveryDocument']}_{r['deliveryDocumentItem']}"
        add_node(
            item_id,
            f"DItem: {r['deliveryDocumentItem']}",
            "DeliveryItem",
            {
                "deliveryDocument": r["deliveryDocument"],
                "item": r["deliveryDocumentItem"],
                "referenceSdDocument": r["referenceSdDocument"],
                "quantity": r["actualDeliveryQuantity"],
                "plant": r["plant"]
            }
        )
        # DeliveryItem → Delivery
        add_edge(
            f"DEL_{r['deliveryDocument']}",
            item_id,
            "HAS_ITEM"
        )
        # SalesOrder → Delivery (via referenceSdDocument)
        if r["referenceSdDocument"]:
            add_edge(
                f"SO_{r['referenceSdDocument']}",
                f"DEL_{r['deliveryDocument']}",
                "HAS_DELIVERY"
            )

    # 5. BILLING HEADERS
    rows = conn.execute("""
        SELECT billingDocument, soldToParty, accountingDocument,
               billingDocumentDate, totalNetAmount,
               transactionCurrency, billingDocumentType,
               billingDocumentIsCancelled
        FROM billing_headers
    """).fetchall()

    for r in rows:
        add_node(
            f"BILL_{r['billingDocument']}",
            f"BILL: {r['billingDocument']}",
            "Billing",
            {
                "billingDocument": r["billingDocument"],
                "soldToParty": r["soldToParty"],
                "accountingDocument": r["accountingDocument"],
                "date": r["billingDocumentDate"],
                "amount": r["totalNetAmount"],
                "currency": r["transactionCurrency"],
                "type": r["billingDocumentType"],
                "isCancelled": r["billingDocumentIsCancelled"]
            }
        )

    # 6. BILLING ITEMS
    rows = conn.execute("""
        SELECT billingDocument, billingDocumentItem,
               referenceSdDocument, material,
               billingQuantity, netAmount
        FROM billing_items
    """).fetchall()

    for r in rows:
        item_id = f"BILLI_{r['billingDocument']}_{r['billingDocumentItem']}"
        add_node(
            item_id,
            f"BItem: {r['billingDocumentItem']}",
            "BillingItem",
            {
                "billingDocument": r["billingDocument"],
                "item": r["billingDocumentItem"],
                "referenceSdDocument": r["referenceSdDocument"],
                "material": r["material"],
                "quantity": r["billingQuantity"],
                "amount": r["netAmount"]
            }
        )
        add_edge(
            f"BILL_{r['billingDocument']}",
            item_id,
            "HAS_ITEM"
        )
        # SalesOrder → Billing via referenceSdDocument
        if r["referenceSdDocument"]:
            add_edge(
                f"SO_{r['referenceSdDocument']}",
                f"BILL_{r['billingDocument']}",
                "HAS_BILLING"
            )

    # 7. PAYMENTS
    rows = conn.execute("""
        SELECT accountingDocument, invoiceReference,
               salesDocument, amountInTransactionCurrency,
               transactionCurrency, postingDate, customer
        FROM payments
    """).fetchall()

    for r in rows:
        add_node(
            f"PAY_{r['accountingDocument']}",
            f"PAY: {r['accountingDocument']}",
            "Payment",
            {
                "accountingDocument": r["accountingDocument"],
                "invoiceReference": r["invoiceReference"],
                "salesDocument": r["salesDocument"],
                "amount": r["amountInTransactionCurrency"],
                "currency": r["transactionCurrency"],
                "postingDate": r["postingDate"],
                "customer": r["customer"]
            }
        )
        # Billing → Payment
        if r["invoiceReference"]:
            add_edge(
                f"BILL_{r['invoiceReference']}",
                f"PAY_{r['accountingDocument']}",
                "HAS_PAYMENT"
            )

    # 8. JOURNAL ENTRIES
    rows = conn.execute("""
        SELECT accountingDocument, referenceDocument,
               postingDate, amountInTransactionCurrency,
               transactionCurrency, companyCode
        FROM journal_entries
    """).fetchall()

    for r in rows:
        node_id = f"JE_{r['accountingDocument']}"
        add_node(
            node_id,
            f"JE: {r['accountingDocument']}",
            "JournalEntry",
            {
                "accountingDocument": r["accountingDocument"],
                "referenceDocument": r["referenceDocument"],
                "postingDate": r["postingDate"],
                "amount": r["amountInTransactionCurrency"],
                "currency": r["transactionCurrency"],
                "companyCode": r["companyCode"]
            }
        )
        # Billing → JournalEntry
        if r["referenceDocument"]:
            add_edge(
                f"BILL_{r['referenceDocument']}",
                node_id,
                "HAS_JOURNAL"
            )

    # 9. BUSINESS PARTNERS
    rows = conn.execute("""
        SELECT businessPartner, businessPartnerFullName,
               businessPartnerCategory
        FROM business_partners
    """).fetchall()

    for r in rows:
        add_node(
            f"BP_{r['businessPartner']}",
            f"BP: {r['businessPartnerFullName'] or r['businessPartner']}",
            "BusinessPartner",
            {
                "businessPartner": r["businessPartner"],
                "name": r["businessPartnerFullName"],
                "type": r["businessPartnerCategory"]
            }
        )
        # BusinessPartner → SalesOrder
        so_rows = conn.execute(
            "SELECT salesOrder FROM sales_order_headers WHERE soldToParty=?",
            (r["businessPartner"],)
        ).fetchall()
        for so in so_rows:
            add_edge(
                f"BP_{r['businessPartner']}",
                f"SO_{so['salesOrder']}",
                "PLACED_ORDER"
            )

    # 10. PRODUCTS
    rows = conn.execute("""
        SELECT product, productType, baseUnit
        FROM products
    """).fetchall()

    for r in rows:
        add_node(
            f"PROD_{r['product']}",
            f"PROD: {r['product']}",
            "Product",
            {
                "product": r["product"],
                "type": r["productType"],
                "baseUnit": r["baseUnit"]
            }
        )
        # Product → SalesOrderItem
        item_rows = conn.execute(
            "SELECT salesOrder, salesOrderItem FROM sales_order_items WHERE material=?",
            (r["product"],)
        ).fetchall()
        for item in item_rows:
            add_edge(
                f"PROD_{r['product']}",
                f"SOI_{item['salesOrder']}_{item['salesOrderItem']}",
                "IN_ORDER"
            )

    conn.close()

    return {
        "nodes": nodes,
        "edges": edges,
        "stats": {
            "total_nodes": len(nodes),
            "total_edges": len(edges)
        }
    }


if __name__ == "__main__":
    result = build_graph()
    print(f"Nodes: {result['stats']['total_nodes']}")
    print(f"Edges: {result['stats']['total_edges']}")

    from collections import Counter
    types = Counter(n["type"] for n in result["nodes"])
    for t, count in types.items():
        print(f"  {t}: {count}")