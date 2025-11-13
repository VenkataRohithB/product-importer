# Product Importer

A simple product importer built with FastAPI, Celery, Redis, and PostgreSQL.
Includes a minimal HTML/CSS/JS dashboard and a sample `products.csv` file to test uploads.

---

## Requirements

* Docker
* (Optional) Python 3.10+ for serving the UI locally

---

## Setup

### Clone the repository

```
git clone git@github.com:VenkataRohithB/product-importer.git
cd product-importer
```

---

## Running the Application

### 1. Start all services (API, Worker, Redis, PostgreSQL)

```
docker compose up --build
```

### 2. API URL

```
http://localhost:8000
```

Swagger docs:

```
http://localhost:8000/docs
```

---

## UI Dashboard

The UI is located in the `dashboard/` folder.

### Start the Dashboard-UI

```
cd dashboard
python3 -m http.server 5000
```

Open in browser:

```
http://localhost:5000
```

---

## Features

### CSV Import

* Upload large CSV files
* Background processing using Celery
* Live progress updates
* Uses included `products.csv` for quick testing

### Product Management

* View products
* Pagination
* Search
* Add / Edit / Delete
* Delete all

### Webhooks

* Add / Edit / Delete
* Enable / Disable
* Test webhook (shows status + response time)

---

## Project Structure

```
app/
dashboard/
products.csv
Dockerfile
docker-compose.yml
requirements.txt
.env
```

---

## Ready for Review

All required features are implemented:

* CSV import with progress
* Product CRUD
* Bulk delete
* Webhooks
* UI dashboard
* Full Docker setup
