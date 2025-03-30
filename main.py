from fastapi import FastAPI, HTTPException
import requests
import redis
import json
from cachetools import TTLCache
from abc import ABC, abstractmethod

app = FastAPI()

BASE_URL = "https://get.taaghche.com/v2/book/"

# مقدار TTL برای کش‌ها
MEMORY_CACHE_TTL = 300  # مدت زمان کش در حافظه (ثانیه)
REDIS_CACHE_TTL = 86400  # مدت زمان کش در Redis (ثانیه)


# 🔹 کلاس انتزاعی برای کش
class CacheBase(ABC):
    """کلاس پایه برای پیاده‌سازی انواع کش"""

    @abstractmethod
    def get(self, key: str):
        pass

    @abstractmethod
    def set(self, key: str, value: dict):
        pass

    @abstractmethod
    def delete(self, key: str):
        pass


# 🔹 پیاده‌سازی کش حافظه (MemoryCache)
class MemoryCache(CacheBase):
    def __init__(self, ttl: int, max_size: int = 100):
        self.cache = TTLCache(maxsize=max_size, ttl=ttl)

    def get(self, key: str):
        return self.cache.get(key)

    def set(self, key: str, value: dict):
        self.cache[key] = value

    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]


# 🔹 پیاده‌سازی کش Redis (RedisCache)
class RedisCache(CacheBase):
    def __init__(self, host: str, port: int, db: int, ttl: int):
        self.redis_client = redis.StrictRedis(host=host, port=port, db=db, decode_responses=True)
        self.ttl = ttl

    def get(self, key: str):
        data = self.redis_client.get(key)
        if not data:
            return None
        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def set(self, key: str, value: dict):
        json_value = json.dumps(value, ensure_ascii=False)
        self.redis_client.set(key, json_value)  # ذخیره بدون انقضا
        self.redis_client.expire(key, self.ttl)


    def delete(self, key: str):
        self.redis_client.delete(key)


# 🔹 مدیریت کش برای امکان تغییر لایه‌های کش در آینده
class CacheManager:
    def __init__(self, memory_cache: CacheBase, redis_cache: CacheBase):
        self.memory_cache = memory_cache
        self.redis_cache = redis_cache

    def get(self, key: str):
        data = self.memory_cache.get(key)
        if data:
            return data

        data = self.redis_cache.get(key)
        if data:
            self.memory_cache.set(key, data)  # داده Redis را در حافظه ذخیره کنیم
            return data

        return None

    def set(self, key: str, value: dict):
        self.memory_cache.set(key, value)
        self.redis_cache.set(key, value)

    def delete(self, key: str):
        self.memory_cache.delete(key)
        self.redis_cache.delete(key)


# پیاده‌سازی کش‌ها
MEMORY_CACHE = MemoryCache(ttl=MEMORY_CACHE_TTL)
REDIS_CACHE = RedisCache(host='localhost', port=6379, db=0, ttl=REDIS_CACHE_TTL)
CACHE_MANAGER = CacheManager(MEMORY_CACHE, REDIS_CACHE)


@app.get("/api/book/{book_id}")
def get_book(book_id: int):
    """دریافت اطلاعات کتاب و بازگرداندن آن"""
    cached_data = CACHE_MANAGER.get(str(book_id))
    if cached_data:
        return cached_data

    url = f"{BASE_URL}{book_id}"
    try:
        response = requests.get(url, timeout=5)

        if response.status_code == 200:
            data = response.json()

            if not data or "book" not in data:
                raise HTTPException(status_code=404, detail="کتاب یافت نشد!")

            book = data["book"]

            result = {
                "id": book.get("id"),
                "title": book.get("title"),
                "description": book.get("description"),
                "price": book.get("price"),
                "numberOfPages": book.get("numberOfPages"),
                "authors": [f"{a}" for a in book.get("authors", [])] if isinstance(book.get("authors"), list) else [],
                "cover": book.get("cover") or book.get("coverUri"),
                "isbn": book.get("isbn") or book.get("ISBN"),
            }

            CACHE_MANAGER.set(str(book_id), result)
            return result

        elif response.status_code == 404:
            raise HTTPException(status_code=404, detail="کتاب یافت نشد!")

        else:
            raise HTTPException(status_code=response.status_code, detail="خطای سرور!")

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="مدت زمان انتظار برای دریافت پاسخ به پایان رسید!")

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"خطای اتصال به سرور طاقچه! ({str(e)})")
