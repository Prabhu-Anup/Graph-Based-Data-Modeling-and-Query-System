# Graph-Based Data Modeling and Query System

## Overview

In real-world enterprise systems, business data is distributed across multiple tables such as orders, deliveries, invoices, and payments. These datasets often lack an intuitive way to trace relationships across entities.

This project addresses that challenge by transforming structured relational data into a **graph-based representation**, enabling seamless traversal and relationship analysis across entities.

The system builds a **context graph** where nodes represent business entities and edges represent relationships between them.

---

## Objective

* Convert relational business data into a graph structure

* Model end-to-end business flow:

  Customer → Order → Delivery → Invoice → Payment

* Enable future support for:

  * Natural language querying
  * Graph visualization
  * Flow tracing and anomaly detection

---

## Features Implemented

### 1. Graph Construction

The system ingests structured data and constructs a graph consisting of:

#### Nodes

* Customer
* Product
* Order
* OrderItem
* Delivery
* Invoice
* Payment

Each node contains:

* Unique ID
* Type
* Metadata (business attributes)

---

### 2. Relationships (Edges)

The graph models real business relationships:

* Customer → Order (`PLACED`)
* Order → OrderItem (`CONTAINS`)
* OrderItem → Product (`OF_PRODUCT`)
* Order → Delivery (`ORDER_TO_DELIVERY`)
* Delivery → Invoice (`DELIVERY_TO_INVOICE`)
* Invoice → Payment (`INVOICE_TO_PAYMENT`)

This enables full lifecycle tracing of transactions.

---

### 3. Data Normalization

* Numeric fields converted from strings to numbers

  * `total_net_amount`, `net_amount`, `quantity`
* Free items identified:

  * `is_free_item = true` when `net_amount == 0`

---

### 4. Data Integrity

* Duplicate nodes prevented using sets
* Duplicate edges avoided
* Edges created only if both nodes exist
* Null and invalid references handled safely

---

### 5. API

Built using FastAPI.

#### Endpoint

`GET /graph`

Returns:

```json
{
  "nodes": [...],
  "edges": [...]
}
```

---

## Tech Stack

* **Backend:** Python, FastAPI
* **Database ORM:** SQLAlchemy
* **Data Processing:** Python
* **Architecture:** Graph-based modeling over relational data

---

## Project Structure

```
project-root/
│
├── main.py                # FastAPI app entry point
├── graph_builder.py       # Core graph construction logic
├── models.py              # Database models
├── database.py            # DB connection and session
├── requirements.txt       # Dependencies
├── README.md              # Documentation
└── data/                  # Dataset (CSV or source files)
```

---

## How to Run

### 1. Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate   # Windows
```

---

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

---

### 3. Run Server

```bash
uvicorn main:app --reload
```

---

### 4. Access API

Open:

```
http://127.0.0.1:8000/graph
```

---

## Example Use Cases

* Trace full lifecycle of an order
* Identify relationships between customers and products
* Analyze order composition
* Detect incomplete business flows (future enhancement)

---

## Current Status

✔ Graph construction completed
✔ All entities modeled
✔ Relationships implemented
✔ Clean and validated data

---

## Planned Enhancements

### 1. Conversational Query Interface (LLM Integration)

* Natural language → structured queries
* Data-backed responses

### 2. Graph Visualization UI

* Interactive node exploration
* Relationship highlighting

### 3. Advanced Querying

* Identify incomplete flows
* Revenue analysis
* Product performance insights

### 4. Guardrails

* Restrict queries to dataset domain
* Reject unrelated prompts

---

## Key Design Decisions

* Graph abstraction over relational schema for better traceability
* Separation of node and edge creation for clarity
* Use of sets for deduplication and performance
* Clean ID schema (`type:id`) for consistency

---
## LLM Query System

The system supports natural language queries over the dataset.

### Flow

User Query → LLM → SQL → Database → Result → Natural Language Answer

### Features

* Natural language understanding using Gemini
* Dynamic SQL generation
* Execution on database
* Human-readable responses
* Guardrails for domain restriction

### Example

**Input:**
"Total number of orders"

**Output:**
"There are 100 orders in total."


## Author

Anup Rajesh Prabhu

---

## License

This project is developed for evaluation and educational purposes.
