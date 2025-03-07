# Rule Engine API

A powerful rule engine API for defining, managing, and evaluating business rules. This project demonstrates advanced concepts in backend development, including:

- **Rule parsing and execution engine**
- **RESTful API design with FastAPI**
- **Database integration with SQLAlchemy ORM**
- **Containerization with Docker**
- **Automated testing and CI/CD**

## Features

- Define attributes with various data types (integer, float, boolean, string)
- Create complex rules using logical operators (AND, OR, NOT)
- Combine multiple rules to build sophisticated rule sets
- Evaluate data against rules in real-time
- Batch evaluation for multiple candidates
- Persistent storage of attributes and rules

## Technologies Used

- **FastAPI**: High-performance web framework
- **SQLAlchemy**: SQL toolkit and ORM
- **Pydantic**: Data validation and settings management
- **Docker**: Containerization
- **GitHub Actions**: CI/CD pipeline

## API Documentation

When running, access the interactive API documentation at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Getting Started

### Prerequisites

- Python 3.8+
- pip

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/rule-engine-api.git
   cd rule-engine-api
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a .env file based on .env.example:
   ```bash
   cp .env.example .env
   ```

5. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

## Docker Deployment

1. Build the Docker image:
   ```bash
   docker build -t rule-engine-api .
   ```

2. Run the container:
   ```bash
   docker run -p 8000:8000 rule-engine-api
   ```

## Example Usage

### 1. Define Attributes

```bash
curl -X POST "http://localhost:8000/api/attributes/" \
  -H "Content-Type: application/json" \
  -d '{"name":"age","attr_type":"integer","min_value":0,"max_value":120}'
```

### 2. Create Rules

```bash
curl -X POST "http://localhost:8000/api/rules/" \
  -H "Content-Type: application/json" \
  -d '{"name":"is_adult","rule_str":"age >= 18"}'
```

### 3. Evaluate Rules

```bash
curl -X POST "http://localhost:8000/api/evaluation/is_adult" \
  -H "Content-Type: application/json" \
  -d '{"candidate":{"age":25}}'
```

## License

MIT
