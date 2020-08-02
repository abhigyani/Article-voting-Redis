from flask import Flask
from redis import Redis

app = Flask(__name__)
cache = Redis(host='redis', port=6379)

@app.route('/')
def home():
    hit_count = cache.get('hitcount')
    if hit_count is None:
        hit_count = 1
    else :
        hit_count = int(hit_count) + 1
    cache.set('hitcount', hit_count)
    return str(hit_count)