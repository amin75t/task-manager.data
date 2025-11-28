# Simple FastAPI Application

A simple FastAPI application with basic CRUD endpoints.

## Features

- Welcome endpoint
- Health check endpoint
- Items CRUD operations
- Automatic API documentation

## Installation

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

Once the server is running, you can access:

- Interactive API docs (Swagger UI): `http://localhost:8000/docs`
- Alternative API docs (ReDoc): `http://localhost:8000/redoc`

## Available Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check
- `GET /items` - Get all items
- `POST /items` - Create a new item
- `GET /items/{item_id}` - Get a specific item by ID

## Example Usage

### Get all items
```bash
curl http://localhost:8000/items
```

### Create an item
```bash
curl -X POST http://localhost:8000/items \
  -H "Content-Type: application/json" \
  -d '{"name": "Sample Item", "description": "A test item", "price": 29.99, "quantity": 5}'
```

### Get specific item
```bash
curl http://localhost:8000/items/1
```
