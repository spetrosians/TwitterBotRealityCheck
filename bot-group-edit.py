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
from datetime import date, datetime, timedelta
from random import randint

from twitter.api import Twitter, TwitterError
from twitter.oauth import OAuth, write_token_file , read_token_file
from twitter.oauth_dance import oauth_dance
from urllib2 import URLError
from httplib import BadStatusLine

#import any other natural processing libs
# go to http://twitter.com/apps/new to create an app and get values
    
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
<<<<<<< HEAD
                	
from random import randint
def response(celeb, link, user, miniTeaser, teaser, title):
    
    if len(miniTeaser)>0:
        message = miniTeaser 
    else:
        message = teaser
    response_good = False
    
    while not response_good:
=======
                

# all of your project code can be wrapped inside of this function
# right now response just parrots the message back at the sender

def getNPRStories(startDate=date.today()-timedelta(days=7), endDate=date.today()):
    url_line='http://api.npr.org/query'
    params = {'meta':'none',
          'id': ','.join(['1149','1126','1013','1025','1136','1024','1007','1004','1056']),
          'fields':','.join(['storyDate,text','listText','pullQuote','teaser','miniTeaser','title']), 
          'requiredAssets':'image',
          'startDate':str(startDate),
          'endDate':str(endDate),
          'dateType':'story',
          'sort':'featured',
          'action':'Or',
          'output':'JSON', 
          'numResults':'40',
          'apiKey':'MDE3NDQzNTkzMDE0MTYxOTA0OTQyYjgzYw001'}
          
          #358046323, #Color Decoded: Stories That Span The Spectrum
          #173814508,#The Race Card Project: Six-Word Essays
          #156490415,#Joe's Big Idea
          #1008,#Arts & Life
          #1060,#Commentary
          #1049,#Digital Life
          #1025,#Environment
          #1052,#Games & Humor
          #1136,#History
          #1129,#Humans
          #1048,#Pop Culture
          #1024,#Research News
          #1007,#Science
          #1004,#World
          #1056, #World Story of the Day
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

>>>>>>> origin/master


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
        
        
def getResponse2(name, user, stories,mention=False):
    name=name.split(' ')
    if len(name)==2:
        name=name[0][0].upper()+name[0][1:]+' '+name[1][0].upper()+name[1][1:]
    elif len(name)==1 and name[0]!='':
        name=name[0][0].upper()+' '+name[0][1:]
    else:
        name=name[0]
        
    templates=[ "@{user} {celeb}'s latest article: {message} {link}",
                "@{user} {celeb} is concerned about this: {message} {link}",
                "@{user} {celeb} has a new guilty pleasure: {message} {link}",
                "@{user} This is more popular than {celeb}?\n{message} {link}",
                "@{user} Here's a break from {celeb}: {message} {link}",
                "@{user} + {celeb} = {message} {link}",
                "@{user} What do you and {celeb} have in common? {message} {link}",
                "@{user} Check this out, thought provoking: {message} {link}"]
    
    lengths=[len(s.format(celeb=name, user=user, message='', link=''))+23 for s in templates]
    i=randint(0,len(stories)-1)
    j=randint(0, len(templates)-1)
    link=stories[i]['link'][0]['$text']
    if stories[i].has_key('teaser'):
        message=stories[i]['teaser']['$text'].split('.')[0][:140-lengths[j]]
    else:
        message=stories[i]['text']['paragraph'][0]['$text'].split('.')[0][:140-lengths[j]]
   # if len(message)>140-lengths[i]:
     #   message=message[:140-lengths[i]]
        
    response=templates[j].format(celeb=name, user=user, message=message, link=link)
    return response
<<<<<<< HEAD
=======
       



<<<<<<< HEAD
>>>>>>> origin/master

def get_id_str_list(name_list, celeb_word_list, collection, limit=10):
    to_respond={name:[tweet['id_str'] for tweet in searchMongo(name,celeb_word_list[name], collection, limit)]
=======
def get_id_str_list(name_list, celeb_word_list, conn, limit=10):
    to_respond={name:[tweet['id_str'] for tweet in searchMongo(name,celeb_word_list[name], conn, limit)]
>>>>>>> fe52db4fbd17bdf60c8ebeaa9d6283ef5f1d66e3
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

<<<<<<< HEAD
def searchMongo(name,word_list,collection, limit=10):
=======



def searchMongo(name,word_list,conn, limit=10):
>>>>>>> fe52db4fbd17bdf60c8ebeaa9d6283ef5f1d66e3
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
    
    return list(conn.find(query).limit(limit))

if __name__ == "__main__":

    user_ids={'date':datetime.utcnow(), 'id_list':[]}
    conn=pymongo.MongoClient()['twitter']['lines']
    last_id=None

    bot = oauth_login()
    bot_name ='@'+bot.account.verify_credentials()['screen_name'] #put your actual bot's name here
    print bot_name
    bot_id_GRC=2880116101 #gina's bot
    bot_id= 2878685726 #GetRealCeleb bot
    #bot_id=bot.account.verify_credentials()['id']
    print bot_id
    
    user_ids={ 'date': datetime.utcnow(), 'id_list':[]}
    if os.path.exists("responded_list.txt") and os.path.getsize('responded_list.txt') > 0:
		f = file("responded_list.txt", "r")
		user_ids['date'] = datetime.strptime(f.readline(), '%x %X\n')
		user_ids['id_list']=[line.strip() for line in f.readlines()]
		f.close()
    
    
    print user_ids['date'], user_ids['id_list']
    #main loop. Just keep searching anyone talking to us
	#a specific user will only get one response per day 
    while True:
<<<<<<< HEAD
        if (user_ids['date']-datetime.utcnow()).days>=1:  
=======
        stories=getNPRStories()
        if (user_ids['date']-datetime.utcnow()).days>=1:
>>>>>>> origin/master
            user_ids['date']=datetime.utcnow()
            user_ids['id_list']=[]
        
        try:
            name_list=['britney spears', 'justin bieber', 'katy perry', 'taylor swift']
            id_list_str=get_id_str_list(name_list,celeb_word_list, conn, limit=1)
            
            id_list_str={tweet_id:name 
                                for name in id_list_str 
                                    for tweet_id in id_list_str[name]}


            for id_str in id_list_str:
                        try:
                            status = make_twitter_request(bot.statuses.user_timeline)
                            if len(status) > 0:
                                last_id = status[0]['id']
                                print 'last_id', last_id    
                            
                            
                            # reply to one of the users pulled out from DB
                        #======================================================== 
                            mention=make_twitter_request(bot.statuses.show,_id=int(id_str))

                            if mention!=None and mention['user']['id_str'] not in user_ids['id_list']: #check if the user has been responded to in the past 24 hours
                                user_ids['id_list'].append(mention['user']['id_str'])
                            
                                message = mention['text']
                                speaker = mention['user']['screen_name']
                                _id=mention['id']
                                print "[+] " + speaker + " is saying " + message
                                reply=getResponse2(id_list_str[id_str], 'color_blind_if' , stories)
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
                                print mention['id'], last_id
                                if mention['id'] > last_id and mention['user']['id']!=bot_id: #does not respond to itself
                                    print 'current mention_id ',mention['id']
                                    message = mention['text'].replace(bot_name, '')
                                    speaker = mention['user']['screen_name']
                                    _id = mention['id']
                                    speaker_id = str(mention['id'])
                                    print "[+] " + speaker + " is saying " + message
                                    reply=getResponse2('', 'color_blind_if' , stories) 
                                    print "[+] Replying " , reply
                                    make_twitter_request(bot.statuses.update, status=reply,in_reply_to_status_id=_id)
                                
                                                
                            sleep_int = 60 #downtime interval in seconds
                            print "Sleeping...\n"
                            time.sleep(sleep_int)
        
                        except exceptions.BaseException, e: #in case of some error/exception - just skipping that post
                        #except KeyboardInterrupt:    
                                print e
                                sleep_int = 60 #downtime interval in seconds
                                print "Sleeping...error\n"
                                time.sleep(sleep_int)
            
        except KeyboardInterrupt:
                print"[!] Cleaning up. last_id was ", last_id
                with open('responded_list.txt','w') as f:
                    f.write(user_ids['date'].strftime('%x %X\n'))
                    for line in user_ids['id_list']:
                        f.write(line+'\n')     
                sys.exit()
