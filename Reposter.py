# -*- coding: utf-8 -*-
import praw
import json
import requests
import tweepy
import time
import os
import imghdr
import urllib.parse
from glob import glob

# Twitter security codes
#Enter your security codes here
access_token = ' '
access_token_secret = ' '
consumer_key = ' '
consumer_secret = ' '

#Enter subreddit name and hashtags to be used in tweets
#Enter time delay between each tweet
subreddit_name = " "
tag_string = "#twitterbot"
num_tweets_before_stopping = 20
tweet_delay = 5  # in minutes

#name of the folder to download images
IMAGE_DIR = 'img'

#main functions

#cut off excess text
def strip_title(title, tag_len):
    char_remaining = 240-tag_len-26
    if len(title) <= char_remaining:
        return title
    elif char_remaining >= 3:
        return title[:char_remaining-3] + "..."
    else:
        return ""

#fetch image
def get_image(img_url):
    if 'redd.it' in img_url:
        file_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
        img_path = IMAGE_DIR + '/' + file_name
        print('[bot] Downloading image at URL ' + img_url + ' to ' + img_path)
        resp = requests.get(img_url, stream=True)
        if resp.status_code == 200:
            with open(img_path, 'wb') as image_file:
                for chunk in resp:
                    image_file.write(chunk)
            return img_path
        else:
            print('[bot] Image failed to download. Status code: ' +
                  str(resp.status_code))


def tweet_creator(subreddit_info):
    post_titles = []
    post_links = []
    post_ids = []
    post_authors = []
    post_imgs = []
    print("[bot] Getting posts from Reddit")
    ''' Usage
    -> .hot() - sorts by hot
    -> .top() - sorts by top
        ->.top("day") - sorts by top of the day
        ->.top("all") - sorts by top posts of all time
    -> .new() - sorts by new
    '''
    for submission in subreddit_info.hot(limit=100):
        post_id = submission.id
        post_link = submission.url
        post_title = strip_title(submission.title, len(tag_string))
        post_author = submission.author
        post_img = submission.url
        post_link = submission.permalink

        post_titles.append(post_title)
        post_links.append(post_link)
        post_ids.append(post_id)
        post_authors.append(post_author)
        post_imgs.append(post_img)

        del post_title, post_link, post_id, post_author, post_img
    return post_titles, post_links, post_ids, post_authors, post_imgs


def setup_connection_reddit(subreddit):
    print("[bot] setting up connection with Reddit")
    #enter your reddit keys here
    r = praw.Reddit(user_agent='Reposter ', client_id=' ',
                    client_secret=' ')
    return r.subreddit('subreddit_name_here')

#check for duplicate posts
def duplicate_check(id):
    found = 0
    with open('posted_posts.txt', 'r') as file:
        for line in file.read().splitlines():
            if id == line:
                found = 1
    file.close()
    return found

#add id for posted posts
def add_id_to_file(id):
    with open('posted_posts.txt', 'a') as file:
        file.write(str(id) + "\n")


def main():
    for filename in glob(IMAGE_DIR + '/*'):
        os.remove(filename)
    count = 0
    if len(tag_string) > 114:
        print("[bot] Trailing string of tags is too long, please limit to <= 114 char")
        return
    while count <= num_tweets_before_stopping:
        try:
            subreddit = setup_connection_reddit(subreddit_name)
            post_titles, post_links, post_ids, post_authors, post_imgs = tweet_creator(
                subreddit)
            tweeter(post_titles, post_links, post_ids, post_authors, post_imgs)
            print("[bot] waiting until next tweet")
            time.sleep(tweet_delay*60)
            count += 1
        except Exception as e:
            continue

    for filename in glob(IMAGE_DIR + '/*'):
        os.remove(filename)


def tweeter(post_titles, post_links, post_ids, post_authors, post_imgs):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)
    api = tweepy.API(auth)
    index = 0
    for post_title, post_link, post_id, post_author, post_img in zip(post_titles, post_links, post_ids, post_authors, post_imgs):
        found = duplicate_check(post_id)
        if found == 0:
            file_img =get_image(post_img)
            tweet_content = post_title+"\nBy u/" + \
                str(post_author)+"\nhttp://redd.it/"+post_id+"\n"+tag_string

            print("[bot] Posting this link on twitter")
            print(tweet_content.encode("utf-8"))
            try:
                print('[bot] With image ' + file_img)
                api.update_with_media(filename=file_img, status=tweet_content)
            except Exception as e:
                print("[bot] Error triggered when sending tweet content to twitter:")
                try:
                    print("[Twitter] " + e.args[0][0]['message'])
                except:
                    continue
                return
            add_id_to_file(post_id)
            return
        else:
            print("[bot] ID for post #%d already collected" % (index))
            index += 1


if __name__ == '__main__':
    main()
