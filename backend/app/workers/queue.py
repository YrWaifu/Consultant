from rq import Queue
from redis import Redis
from ..settings import settings


redis = Redis.from_url(settings.REDIS_URL)
queue = Queue("checks", connection=redis)