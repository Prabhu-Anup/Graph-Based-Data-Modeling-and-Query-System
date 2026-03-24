# Graph-Based Data Modeling and Query System

## Overview

In real-world enterprise systems, business data is distributed across multiple tables such as orders, deliveries, invoices, and payments. These datasets often lack an intuitive way to trace relationships across entities.

This project transforms structured relational data into a **graph-based representation**, enabling seamless traversal, traceability, and analysis of business processes.

A **context graph** is constructed where:

* Nodes represent business entities
* Edges represent relationships between them

Additionally, the system integrates an **LLM-powered query interface**, allowing users to interact with the data using natural language.

---

## Objective

* Convert relational data into a graph structure

* Model complete business flow:

  **Customer → Order → Delivery → Invoice → Payment**

* Enable:

  * Natural language querying
  * Graph visualization
  * Flow tracing
  * Data-driven insights

---

## System Architecture

```text
User (Frontend UI)
        ↓
Chat Interface (React)
        ↓
FastAPI Backend (/query)
        ↓
LLM (Gemini)
        ↓
SQL Generation
        ↓
Database Execution
        ↓
Result Processing
        ↓
Natural Language Answer
```

---

## Features Implemented

### 1. Graph Construction

The system constructs a graph from structured data.

#### Nodes

* Customer
* Product
* Order
* OrderItem
* Delivery
* Invoice
* Payment

Each node contains:

* Unique ID (`type:id`)
* Type
* Metadata (business attributes)

---

### 2. Relationships (Edges)

The graph models real-world business flows:

* Customer → Order (`PLACED`)
* Order → OrderItem (`CONTAINS`)
* OrderItem → Product (`OF_PRODUCT`)
* Order → Delivery (`ORDER_TO_DELIVERY`)
* Delivery → Invoice (`DELIVERY_TO_INVOICE`)
* Invoice → Payment (`INVOICE_TO_PAYMENT`)

This enables **end-to-end traceability**.

---

### 3. Data Normalization

* Converted numeric fields from strings:

  * `total_net_amount`, `net_amount`, `quantity`
* Identified free items:

  * `is_free_item = true` when `net_amount == 0`

---

### 4. Data Integrity

* Duplicate nodes prevented using sets
* Duplicate edges avoided
* Edges created only when both nodes exist
* Null values handled safely

---

### 5. Backend API (FastAPI)

#### Endpoints

**GET /graph**

```json
{
  "nodes": [...],
  "edges": [...]
}
```

**POST /query**

```json
{
  "user_query": "total number of orders"
}
```

Returns:

```json
{
  "answer": "There are 100 orders in total.",
  "generated_sql": "...",
  "result": [...]
}
```

---

## LLM Query System

The system enables **natural language interaction with data**.

### Flow

User Query → LLM → SQL → Database → Result → Natural Language Answer

### Features

* Natural language understanding using **Google Gemini**
* Dynamic SQL generation
* Execution on database
* Human-readable responses
* Domain-specific guardrails

---

## Frontend UI

A React-based interactive interface is implemented.

### Features

* Graph visualization using **React Flow**
* Interactive node exploration (click to view metadata)
* Chat interface for querying data
* Real-time responses from backend

### Layout

* Left: Graph visualization
* Right: Chat assistant panel

---

## Tech Stack

### Backend

* Python
* FastAPI
* SQLAlchemy
* SQLite

### Frontend

* React (Vite)
* React Flow
* Axios

### AI / LLM

* Google Gemini API

---

## Project Structure

```
project-root/
│
├── main.py
├── graph_builder.py
├── query_engine.py
├── models.py
├── database.py
│── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── components/
│   └── package.json
│
├── data/
└── README.md
```

---

## How to Run

### Backend

```bash
python -m venv venv
venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

---

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on:

```
http://localhost:5173
```

---

## Example Queries

* "Total number of orders"
* "Total revenue"
* "Top products by billing"
* "Trace a full order flow"

---

## Guardrails

* Restricts queries to dataset domain
* Rejects unrelated queries (e.g., jokes, general knowledge)
* Ensures responses are data-backed

---

## Key Design Decisions

* Graph abstraction over relational schema for traceability
* Separation of node and edge creation
* Use of sets for deduplication
* Clean ID schema (`type:id`)
* LLM-driven dynamic query generation

---

## Current Status

✔ Graph construction completed
✔ Full relationship modeling
✔ LLM-powered query system
✔ SQL execution + natural answers
✔ Interactive frontend UI

---

## Future Enhancements

* Highlight nodes based on query results
* Advanced graph analytics (clustering, anomaly detection)
* Conversation memory
* Streaming LLM responses
* Deployment (Docker + cloud hosting)

---

## Demo Flow

1. Open frontend UI
2. Enter query (e.g., "total orders")
3. System generates SQL
4. Executes query
5. Returns natural language answer
6. Explore graph relationships interactively

---

## Author

**Anup Rajesh Prabhu**

---

## License

This project is developed for evaluation and educational purposes.
