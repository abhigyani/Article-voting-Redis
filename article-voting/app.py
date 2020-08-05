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


ONE_WEEK_IN_SECOND = 7 * 86400
VOTE_SCORE = 432
def article_vote():

    """
    Method to add vote up functionality.
    If the article is posted for more than a week, then no voting is allowed.
    If article is posted within a week and if the current user has not voted for it yet:
    -   Update the article hash's votes attribute by 1
    -   Update the article's score in score z-set y 432
    -   Adds the user's id to voters:<id> set
    """

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


def add_article(conn, user, title, link):

    """
    Method to add a new article.
    1.  Generate an unique article id.
    2.  Prepare the name for article hash and voter set
    3.  Create and add the hash for article details to be stored as a new article:<article id>
    4.  Create a new set for voted:article for the new article.
    5.  Add expiry after one week for the newly added article's voted set.
    6.  Add a new entry with the article id in the time: z-set.
    7.  Add a new entry with the article score in the score: z-set.
    """

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


ARTICLES_PER_PAGE = 25
def fetch_articles(conn, page, order='score:'):

    """
    Method to fetch articles for each page.
    -   Pagination is present with articles quantified to 25
    -   Pick the 25 highest scored articles for that page.
    -   Pick the article body from the article: HASH for each of the id's picked in previous step.
    -   Add an attribute id to the the picked article.
    """

    articles = []

    # "Logic to load the first article of n-th page.
    # NOTE: data fetched in z-set is 0 indexed"
    start = (page-1) * ARTICLES_PER_PAGE
    end = start + (ARTICLES_PER_PAGE - 1)

    # "Logic to fetch the last 25 articles of the given range.
    # NOTE: In Z-SET data is scored in member:score format in ascending order by value.
    # ZREVRANGE() returns a list of data in reverse order."
    ids = redisConn.zrevrange(order, start, end)

    # Logic to fetch the article body from the article HASH based upon the article ids picked in previous steps.
    for id in ids:
        article = redisConn.hgetall(id)
        article['id'] = id
        articles.append(article)

    return articles


def add_to_remove_from_groups(conn, article_id, to_add=[], to_remove=[]):

    """
    Method to add any article to different groups.
    @params conn: Redis connection oject.
    @params article_id: id of the article which has to be added or removed from different groups.
    @params to_add[]:list of group ids to which the article has to be added.
    @params to_remove[]: list of group ids from which the article has to be removed.

    NOTE: Every different group is a SET with key as 'group:<group_id>' and 'article:<id>' as members."
    """

    article = 'article:'+id

    for group_id in to_add:
        group = 'group:'+group_id
        redisConn.sadd(group, article)
    
    for group_id in to_remove:
        group = 'group:'+group_id
        redisConn.srem(group, article)


def get_group_articles(conn, group_id, page, order='score:'):

    """
    Method to fetch all the articles in a group.
    @params conn: Redis connection object.
    @params group_id: Id of the group for whose all the articles are to be fetched.
    @params page: Articles on N-th page of that groups to fetched.
    @params order: The SET/Z-SET with which intersection has to be done.
    
    STEPS:
      -   Format the name of group SET which has to be intersected with 'scores:' Z-SET.
      -   Prepare the name of the temporary Z-SET which would be formed on intersection on all the SETS/Z-SETS.
      -   If that Z-SET does not exist already then prepare it using 'ZINTERSTORE' function.
      -   Call the fetch articles method sending the newly created Z-SET by intersection as parameter.

     NOTE: ZINTERSTORE, perform an intersection with all the MEMBERS of primary SET/Z-SET with all the MEMBERS of passes SETS/Z-SETS based on the parameter passed as aggregate/weights.
            By default score of all MEMBERS of SET are 1."
    """

    group = 'group:'+group_id
    interstore_name = order + group

    if not redisConn.exists(interstore_name):
        intersection = redisConn.zinterstore(interstore_name, [group, order], aggregate='max')
        redisConn.expire(intersection, 60)
        redisConn.z
    return fetch_articles(conn, page, intersection)

def down_vote_article(conn, article_id):
    article = 'article:'+article_id
    time_posted = redisConn.zscore('score:', article)

    if time_posted < ONE_WEEK_IN_SECOND:
        redisConn.zincrby('score:', -VOTE_SCORE, article)


if __name__ == '__main__':
    app.run(debug=True)
