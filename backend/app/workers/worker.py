from rq import Worker
from .queue import redis  # это экземпляр Redis с твоего REDIS_URL

if __name__ == "__main__":
    Worker(["checks"], connection=redis).work(with_scheduler=True)