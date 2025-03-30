from fastapi.testclient import TestClient
from main import app, MEMORY_CACHE, REDIS_CACHE  # فایل اصلی پروژه شما
from unittest.mock import patch
import json

client = TestClient(app)

def test_memory_cache():
    book_id = 123
    cached_data = {"id": book_id, "title": "Test Book"}
    
    # ابتدا داده‌ها رو به کش حافظه می‌ریزیم
    MEMORY_CACHE.set(str(book_id), cached_data)
    
    # درخواست به API
    response = client.get(f"/api/book/{book_id}")
    
    # بررسی وضعیت پاسخ و داده‌ها
    assert response.status_code == 200
    assert response.json() == cached_data

def test_redis_cache(mocker):
    book_id = 456
    cached_data_redis = {"id": book_id, "title": "Redis Test Book"}

    # Mock کردن رفتار RedisCache
    mock_redis_get = mocker.patch.object(REDIS_CACHE, 'get', return_value=cached_data_redis)

    # درخواست به API
    response = client.get(f"/api/book/{book_id}")

    # بررسی وضعیت پاسخ و داده‌ها
    assert response.status_code == 200
    assert response.json() == cached_data_redis
    mock_redis_get.assert_called_once_with(str(book_id))  # بررسی اینکه متد get روی Redis صدا زده شده

def test_cache_miss_and_api_call(mocker):
    book_id = 789
    book_data_from_api = {
        "book": {
            "id": book_id,
            "title": "API Fetched Book",
            "description": "A book fetched from API",
            "price": 100,
            "numberOfPages": 250,
            "authors": ["Author Name"],  
            "cover": "https://someurl.com",  
            "isbn": "123-456-789"  
        }
    }

    # Mock کردن درخواست به API
    mock_requests_get = mocker.patch('requests.get')
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = book_data_from_api

    # درخواست به API
    response = client.get(f"/api/book/{book_id}")

    # بررسی وضعیت پاسخ و داده‌ها
    assert response.status_code == 200
    assert response.json() == book_data_from_api["book"]

def test_cache_storage(mocker):
    book_id = 101
    book_data = {"id": book_id, "title": "Test Book After API"}

    # Mock کردن درخواست به API
    mock_requests_get = mocker.patch('requests.get')
    mock_requests_get.return_value.status_code = 200
    mock_requests_get.return_value.json.return_value = {"book": book_data}

    # درخواست به API
    response = client.get(f"/api/book/{book_id}")

    # بررسی ذخیره شدن داده‌ها در کش حافظه
    assert MEMORY_CACHE.get(str(book_id)) == book_data
    # بررسی ذخیره شدن داده‌ها در کش Redis
    assert json.loads(REDIS_CACHE.get(str(book_id))) == book_data

def test_book_not_found(mocker):
    book_id = 999
    mock_requests_get = mocker.patch('requests.get')
    mock_requests_get.return_value.status_code = 404
    
    response = client.get(f"/api/book/{book_id}")

    assert response.status_code == 404

def test_api_timeout(mocker):
    book_id = 202
    mock_requests_get = mocker.patch('requests.get', side_effect=TimeoutError)

    response = client.get(f"/api/book/{book_id}")

    assert response.status_code == 504
