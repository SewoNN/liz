# MongoDB with Docker

This guide explains how to use MongoDB with Docker in this project.

## Prerequisites

- Docker installed on your system
- Docker Compose installed on your system

## Getting Started

1. Start MongoDB and Mongo Express using Docker Compose:

```bash
docker-compose up -d
```

This command starts both MongoDB and Mongo Express in detached mode.

## Connection Details

- **MongoDB Server**:
  - Host: `localhost`
  - Port: `27017`
  - Username: `root`
  - Password: `example`
  - Connection string: `mongodb://root:example@localhost:27017/`

- **Mongo Express** (Web-based MongoDB admin interface):
  - URL: `http://localhost:8081`
  - Username: `root`
  - Password: `example`

## Using MongoDB in Your Application

### Python Example (with pymongo):

```python
from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://root:example@localhost:27017/')

# Access a database
db = client['your_database_name']

# Access a collection
collection = db['your_collection_name']

# Insert a document
collection.insert_one({"name": "Example", "value": 42})

# Find documents
results = collection.find({"name": "Example"})
for result in results:
    print(result)
```

## Stopping the Containers

To stop the MongoDB and Mongo Express containers:

```bash
docker-compose down
```

To stop the containers and remove the volumes (this will delete all data):

```bash
docker-compose down -v
```

## Security Note

The current configuration uses default credentials for demonstration purposes. For production use:

1. Change the default username and password
2. Consider using Docker secrets or environment variables
3. Implement proper network security measures

## Troubleshooting

If you encounter connection issues:

1. Ensure Docker is running
2. Check if the containers are running with `docker ps`
3. View container logs with `docker logs mongodb` or `docker logs mongo-express` 