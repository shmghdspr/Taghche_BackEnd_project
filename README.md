# Book Cache Service

A FastAPI-based service to retrieve book details from an external API (`Taaghche`) with a two-layer caching mechanism. It first checks a memory cache, then a Redis cache, and finally fetches the data from the external API if not cached.

## Features
- Two-layer caching with **Memory Cache** and **Redis Cache**.
- **TTL (Time-to-Live)** for both caches.
- Supports dynamic switching of cache layers.
- Implements a clean, testable code structure with unit tests.
- Configurable TTL values for both memory and Redis caches.
- Error handling for API timeouts, connection issues, and HTTP errors.

## How It Works

1. When a request is made to `/api/book/{id}`, the service first checks if the book data is available in **Memory Cache**.
2. If not found in memory, it checks the **Redis Cache**.
3. If the data is not found in either cache, the service makes an HTTP request to the external API (`https://get.taaghche.com/v2/book/{id}`) to retrieve the book details and stores them in both caches.
4. The cached data will expire after the configured TTL times for memory and Redis.

## Installation

### Requirements
- Python 3.8+
- Redis server

### Install dependencies
```bash
pip install -r requirements.txt
```

## Running the Application

1. **Run the FastAPI application** using `uvicorn`:

   ```bash
   uvicorn main:app --reload
   ```

This will start the FastAPI server at `http://127.0.0.1:8000`.

### Access the API:

You can now make API requests by navigating to `http://127.0.0.1:8000`. For example:

- **Swagger UI** (API documentation):
  
  http://127.0.0.1:8000/docs

## Configuration

You can configure the TTL (Time-to-Live) for both **Memory Cache** and **Redis Cache** by modifying the respective variables in the code.

- **Memory Cache TTL**: `MEMORY_CACHE_TTL` (default: 300 seconds)
- **Redis Cache TTL**: `REDIS_CACHE_TTL` (default: 86400 seconds)

For example, to change the TTL for the memory cache to 600 seconds and for Redis to 3600 seconds, modify these values in your code:

```python
MEMORY_CACHE_TTL = 600  # New TTL for memory cache
REDIS_CACHE_TTL = 3600  # New TTL for Redis cache
```

You can also change the Redis connection settings (host, port, db) in the RedisCache class. By default, it connects to localhost on port 6379 with database 0. If you want to change these values, update the following:

```python
REDIS_CACHE = RedisCache(host='your_redis_host', port=your_redis_port, db=your_redis_db, ttl=REDIS_CACHE_TTL)
```
## Testing

To run the unit tests, ensure that your virtual environment is activated, then run the following command:
```python
pytest -vv test_cache.py
```
This will run all the tests in your project and output the results to the terminal.
### Example Output:
                                                                                                                                 
```python
- test_cache.py::test_memory_cache <span style="color: green;">PASSED</span>

- test_cache.py::test_redis_cache <span style="color: green;">PASSED</span>           
- test_cache.py::test_cache_miss_and_api_call <span style="color: red;">FAILED</span>
- test_cache.py::test_cache_storage <span style="color: red;">FAILED</span>     
- test_cache.py::test_book_not_found <span style="color: green;">PASSED</span>    
- test_cache.py::test_api_timeout <span style="color: red;">FAILED</span>
```  
