import redis

try:
    client = redis.Redis(host='localhost', port=6379)
    client.ping()
    print('Connected to Redis')
except redis.ConnectionError:
    print('Failed to connect to Redis')
