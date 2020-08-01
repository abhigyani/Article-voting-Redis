from flask import Flask
from redis import Redis

app = Flask(__name__)
cache = Redis(host='redis', port=6379)

@app.route('/')
def home():
    key = 'welcome'
    value = 'Hello World! I am the value of key "welcome" in the redis'
    cache.set(key, value)
    return cache.get(key)