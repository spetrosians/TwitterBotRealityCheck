#from celeb_word_list import *
#from aux_func import *
import os
import sys
import time
import json
import twitter
import re
import pymongo
import exceptions
import requests
from datetime import date
from datetime import timedelta
from random import randint

from twitter.api import Twitter, TwitterError
from twitter.oauth import OAuth, write_token_file , read_token_file
from twitter.oauth_dance import oauth_dance
from urllib2 import URLError
from httplib import BadStatusLine

#import any other natual processing libs


# go to http://twitter.com/apps/new to create an app and get values
# for these credentials that you'll need to provide in place of these
# empty string values that are defined as placeholders.
    
def oauth_login():
    CONSUMER_KEY = 'Q7KQHynEeJwEvUrKnHjRUvFBA'
    CONSUMER_SECRET ='WdO5H4NV78bUApxT7tajxr9p7YtQUVWAtkUzIooCq1LdlNurbd'
    OAUTH_TOKEN = '2878685726-7GgrQM3HrFclEu62j6OnoZ3LlgtadoufymOqZ50'
    OAUTH_TOKEN_SECRET =  'rFF2cokPmpg6SuDH9zd7Jy970tTf01UXwTjCrtPCrzpDS'
    auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,
                               CONSUMER_KEY, CONSUMER_SECRET)
    
    twitter_api = Twitter(auth=auth)
    return twitter_api

# nested helper function that handles common HTTPErrors. Return an updated
# value for wait_period if the problem is a 500 level error. Block until the
# rate limit is reset if it's a rate limiting issue (429 error). Returns None
# for 401 and 404 errors, which requires special handling by the caller.
    
    
def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw): 
    
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):
        if wait_period > 3600: # Seconds
            print >> sys.stderr, 'Too many retries. Quitting.'
            raise e
    
        # See https://dev.twitter.com/docs/error-codes-responses for common codes
        if e.e.code == 401:
            print >> sys.stderr, 'Encountered 401 Error (Not Authorized)'
            return None
        elif e.e.code == 404:
            print >> sys.stderr, 'Encountered 404 Error (Not Found)'
            return None
        elif e.e.code == 429: 
            print >> sys.stderr, 'Encountered 429 Error (Rate Limit Exceeded)'
            if sleep_when_rate_limited:
                print >> sys.stderr, "Retrying in 15 minutes...ZzZ..."
                sys.stderr.flush()
                time.sleep(60*15 + 5)
                print >> sys.stderr, '...ZzZ...Awake now and trying again.'
                return 2
            else:
                raise e # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print >> sys.stderr, 'Encountered %i Error. Retrying in %i seconds' % (e.e.code, wait_period)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e
    # End of nested helper function
    
    wait_period = 2 
    error_count = 0 

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError, e:
            error_count = 0 
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError, e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print >> sys.stderr, "URLError encountered. Continuing."
            if error_count > max_errors:
                print >> sys.stderr, "Too many consecutive errors...bailing out."
                raise
        except BadStatusLine, e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print >> sys.stderr, "BadStatusLine encountered. Continuing."
            if error_count > max_errors:
                print >> sys.stderr, "Too many consecutive errors...bailing out."
                raise
                

# all of your project code can be wrapped inside of this function
# right now response just parrots the message back at the sender

def getNPRStories(startDate=date.today()-timedelta(days=7), endDate=date.today()):
    url_line='http://api.npr.org/query'
    params = {'meta':'none',
          'id': '3002',#'1149,1126,1013,1025,1136,1024,1007,1004,1056',
          'fields': 'storyDate,text,listText,pullQuote,teaser,miniTeaser,title', 
          'requiredAssets':'image',
          'startDate':'{0}'.format(startDate),
          'endDate':'{0}'.format(endDate),
          'dateType':'story',
          'sort':'featured',
          'action':'Or',
          'output':'JSON', 
          'numResults':'40',
          'apiKey':'MDE3NDQzNTkzMDE0MTYxOTA0OTQyYjgzYw001'}
    r = requests.get(url_line, params=params)
    r_json=r.json()
    stories=r_json['list']['story']
    return stories
				
				
						
def getResponse(celeb, user, stories):
    good_response = False
    story_num = 0
    while not good_response:
        story = stories[story_num]
        link = story['link'][0]['$text']
    #    if story.has_key('miniTeaser'):
     #       miniTeaser = story['miniTeaser']['$text']
        teaser = story['teaser']['$text']
        title = story['title']['$text']
        response = response_func(celeb, user, '', teaser, title, link)
        if type(response) == type(''):
            good_response = True
        story_num += 1
        if story_num == len(stories):
            response = "@"+user+" Check this out, thought provoking: " + link
            good_response = True
    return response



def response_func(celeb, user, miniTeaser, teaser, title, link):   
    teaser = teaser.split()[0:10]
    teaser = ' '.join(teaser) + '...'
    messages = [teaser, miniTeaser, title]
    for message in messages:
        response = []
        response.append(celeb + "'s latest article: " + message + ' ' + link)
        response.append(celeb + ' is concerned about this: ' + message + ' ' + link)
        response.append(celeb + " has a new guilty pleasure: " + message + ' ' + link)
        response.append("This is more popular than " + celeb + '?\n' + message + ' ' + link)
        response.append("Here's a break from " + celeb + ': ' + message + ' ' + link)
        response.append("@" + user + ' + ' +celeb + ' = '+ message + ' ' + link)
        response.append("What do you and " + celeb + ' have in common? ' + message + ' ' + link)
        i = randint(0,6) #inclusive
        response = response[i]
        if len(response)<=140:
            return response
    return None
        
        
        




def get_id_str_list(name_list, celeb_word_list, collection, limit=10):
    to_respond={name:[tweet['id_str'] for tweet in searchMongo(name,celeb_word_list[name], collection, limit)]
                                for name in name_list}
    return to_respond

# Connection to Mongo DB
def connectMongo():
    try:
        conn=pymongo.MongoClient()
        print "Connected successfully!!!"
    except pymongo.errors.ConnectionFailure, e:
       print "Could not connect to MongoDB: %s" % e 
    return conn




def searchMongo(name,word_list,collection, limit=10):
    name=name.split(' ')
    if(len(name)>1):
        first=name[0]
        last=name[1]
    else:
        first=name[0]
        last=''
        
    yes_line=r'({word}.*{first}\s?{last})|({first}\s?{last}.*{word})'
    yes_list=[ re.compile(yes_line.format(first=first, last=last, word=word), re.I)
                        for word in word_list['yes']] 
                        
    no_list=[ re.compile(word, re.I)
                        for word in word_list['no']] 
    no_list.append(re.compile(r'http', re.I))

    query={'text':{'$in':yes_list, '$nin':no_list}}
    
    return list(collection.find(query).limit(limit))



if __name__ == "__main__":
    from datetime import datetime
    user_ids={'date':datetime.utcnow(), 'id_list':[]}
    conn=connectMongo()
    db=conn.twitter
    collection=db.lines

    last_id=None

    bot = oauth_login()
    bot_name ='@'+bot.account.verify_credentials()['screen_name'] #put your actual bot's name here
    print bot_name
    bot_id_GRC=2880116101 #gina's bot
    bot_id= 2878685726 #GetRealCeleb bot
    #bot_id=bot.account.verify_credentials()['id']
    print bot_id
    
    #main loop. Just keep searching anyone talking to us
    while True:
        stories=getNPRStories()
        if (user_ids['date']-datetime.utcnow()).days>=1:
            user_ids['date']=datetime.utcnow()
            user_ids['id_list']=[]
        
        try:
            name_list=['britney spears', 'justin bieber', 'katy perry']
            id_list_str=get_id_str_list(name_list,celeb_word_list, collection, limit=2)
            id_list_str={tweet_id:name 
                                for name in id_list_str 
                                    for tweet_id in id_list_str[name]}

            #make a call to npr.org
            for id_str in id_list_str:
                        try:
                            status = make_twitter_request(bot.statuses.user_timeline)
                            if len(status) > 0:
                                last_id = status[0]['id']
                                print 'last_id', last_id    
                            
                            
                            # reply to one of the users pulled out from DB
                        #======================================================== 
                            mention=make_twitter_request(bot.statuses.show,_id=int(id_str))
                            if mention['user']['id'] not in user_ids['id_list']: #check if the user has been responded to in the past 24 hours
                                user_ids['id_list'].append(mention['user']['id'])
                            else:
                                continue
                            message = mention['text']
                            speaker = mention['user']['screen_name']
                            _id=mention['id']
                            print "[+] " + speaker + " is saying " + message
                           # reply = '@color_blind_if  get on earth(c) ' +speaker
                            reply=getResponse(id_list_str[id_str], 'color_blind_if' , stories)
                            #reply = 'get on earth(c) ' +speaker+' forget '+ message
                            if len(reply)>140: #in case message is more than 140 characters
                                reply=reply[:140]
                            print "[+] Replying " , reply 
                            _id=532812179049676800 #would need to comment out once we have a real message
                            make_twitter_request(bot.statuses.update, status=reply,in_reply_to_status_id=_id)
                        
                        #===================================                 
                        #then respond to all the mentions (based on the last reply)
                        #===========================================
                            if last_id!=None:
                                mentions = make_twitter_request(bot.statuses.mentions_timeline, since_id=last_id)
                            else:
                                mentions = make_twitter_request(bot.statuses.mentions_timeline)
        
                            if not mentions:
                                print "No one talking to us now...", time.ctime()
                        
                            mentions=[mentions[(len(mentions)-i-1)] for i in xrange(len(mentions))] #reverse the list
                    
                            for mention in mentions: 
                                if mention['id'] > last_id and mention['user']['id']!=bot_id: #does not respond to itself
                                    print 'current mention_id ',mention['id']
                                    message = mention['text'].replace(bot_name, '')
                                    speaker = mention['user']['screen_name']
                                    _id = mention['id']
                                    speaker_id = str(mention['id'])
        
                                    print "[+] " + speaker + " is saying " + message
                                    reply = '@%s %s' % (speaker, 'here should be a link to a pop culture article') 
                                    print "[+] Replying " , reply
                                    make_twitter_request(bot.statuses.update, status=reply,in_reply_to_status_id=_id)
                                
                                                
                            sleep_int = 60 #downtime interval in seconds
                            print "Sleeping...\n"
                            time.sleep(sleep_int)
        
                        #except exceptions.BaseException, e: #in case of some error/exception - just skipping that post
                        except KeyboardInterrupt:    
                                #print e
                                sleep_int = 60 #downtime interval in seconds
                                print "Sleeping...\n"
                                time.sleep(sleep_int)

        

            
        except KeyboardInterrupt:
                print"[!] Cleaning up. last_id was ", last_id
                with open('responded_list.txt','w') as f:
                    f.write(user_ids['date'].strftime('%x %X'))
                    f.writelines(user_ids['id_list'])
                sys.exit()









            
