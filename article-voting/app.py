from flask import Flask, render_template
from redis import Redis
import time
from datetime import datetime

app = Flask(__name__)
redisConn = Redis(host='redis', port=6379)

articles = [
    {
        'author': 'Abhigyani',
        'postedOn': datetime.utcfromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
        'body': 'This is an article on Flask',
        'didYouVote': True
    },
    {
        'author': 'Aditi',
        'postedOn': datetime.utcfromtimestamp(int(time.time())).strftime('%Y-%m-%d %H:%M:%S'),
        'body': 'This is an article on Redis',
        'didYouVote': False
    }
]

@app.route('/')
def home():
    return 'Welcome you are going to view some articles!'

@app.route('/<user>')
def userpage(user):
    return render_template('index.html', articles=articles, user=user)

#"
# Method to add vote up functionality.
# If the article is posted for more than a week, then no voting is allowed.
# If article is posted within a week and if the current user has not voted for it yet:
#   -   Update the article hash's votes attribute by 1
#   -   Update the article's score in score z-set y 432
#   -   Adds the user's id to voters:<id> set
# "
ONE_WEEK_IN_SECOND = 7 * 86400
VOTE_SCORE = 432
def article_vote():
    # Logic to check if the posted article is more than a week old.
    cut_off = time.time() - ONE_WEEK_IN_SECOND
    if redisConn.zscore('time:', article) < cut_off:
        return
    
    # Logic to extract the article id
    article_id = article.partition(':')[-1]

    # Logic to check if the current user has already voted for the article or not.
    if redisConn.sadd('voted:'+article_id, user):
        # Logic to increase the vote count in article has by one.
        redisConn.hincrby(article, 'votes', 1)

        # Logic to increase the score of article by 432.
        redisConn.zincrby('score:', article, VOTE_SCORE)

#"
# Method to add a new article.
#   1.  Generate an unique article id.
#   2.  Prepare the name for article hash and voter set
#   3.  Create and add the hash for article details to be stored as a new article:<article id>
#   4.  Create a new set for voted:article for the new article.
#   5.  Add expiry after one week for the newly added article's voted set.
#   6.  Add a new entry with the article id in the time: z-set.
#   7.  Add a new entry with the article score in the score: z-set.
# "
def add_article(conn, user, title, link):

    # Logic to create unique article id for the new article.
    article_id = int(conn.incr('article:'))

    # Setting up name for to be created article hash and voted set.
    article = 'article:'+article_id
    voted = 'voted:'+article_id

    # Creation of new hash with the meta data of the new article.
    article_details = {
        'title': title,
        'link': link,
        'poster': user,
        'time': time.time(),
        'votes': 1
    }
    # Adding a new hashmap of the new article.
    redisConn.hmset(article, article_details)

    # Creating a new set to maintain the voted user id on the new article.
    redisConn.sadd(voted, user)
    # Logic to configure expiry after one week of voted set of new article.
    redisConn.expire(voted, ONE_WEEK_IN_SECOND)

    # Adding an entry in the time: z-set with the current time when the article is posted.
    redisConn.zadd('time:', article_id, time.time())

    # "Adding an entry to maintain the score of the new article.
    # Initial score has been set as a function of 432"
    redisConn.zadd('score:', article_id, time.time() + VOTE_SCORE)

    return article_id

if __name__ == '__main__':
    app.run(debug=True)