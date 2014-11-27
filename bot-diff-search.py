from celeb_word_list import *
from aux_func import *
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
import pickle as pkl


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



def getResponse2(name, user, stories_dict,mention=False):
    name=name.split(' ')
    if len(name)==2:
        name=name[0][0].upper()+name[0][1:]+' '+name[1][0].upper()+name[1][1:]
    elif len(name)==1 and name[0]!='':
        name=name[0][0].upper()+name[0][1:]
    else:
        name=name[0]
        
    templates={'358046323':"@{user} {celeb} shares a colorful world with you. {message} {link}",
                '173814508':"@{user} Even {celeb} doesn't have enough money to end racism. {message} {link}",
                '156490415':"@{user} Do you think {celeb} can come up with an idea like this? {message} {link}",
                '1008':"@{user} Here's a different view of life than {celeb}'s: {message} {link}",
                '1060':"@{user} Interesting news! what do you think {celeb} has to say about it? {message} {link}",
                '1049':"@{user} Do you think {celeb} is tech savvy? {message} {link}",
                '1025':"@{user} Does {celeb} care for the environment? {message} {link}",
                '1052':"@{user} vs. {celeb} Who would win? {message} {link}",
                '1136':"@{user} Would {celeb} still be a celebrity back then? {message} {link}",
                '1129':"@{user} If you think {celeb}'s cool, check these people out! {message} {link}", 
                '1024':"@{user} {celeb} should fund this research: {message} {link}",
                '1007':"@{user} what does the future hold? {celeb} or this AWSOME science! {message} {link}",
                '1004':"@{user} There's more to life than {celeb}, check out what's happening around the world! {message} {link}",
                '1056':"@{user} Here's a break from {celeb}, check out what's happening around the world! {message} {link}"}
 
    def trimMessage(message, length):
        message=message.encode("ascii", "ignore")
        message=message.split('.')[0]
        if len(message)>140-length:
            words=message.split(' ')
            message=words[0]
            for w in words[1:]:
                if len(message+' '+w)<=140-length:
                    message=message+' '+w
        return message
    
    def getSentences(story):
        paragraphs=story['text']['paragraph']
        text_list=[p['$text'] for p in paragraphs]
        text='\n'.join(text_list)
        blob=TextBlob(text)
        most_colored=[(s.polarity, s.subjectivity, s.raw) for s in blob.sentences]
        sents=[min(most_colored, key=lambda x: x[0])[2].replace('.',''),
           max(most_colored, key=lambda x: x[0])[2].replace('.',''),
           min(most_colored, key=lambda x: x[1])[2].replace('.',''),
           max(most_colored, key=lambda x: x[1])[2].replace('.','')]
        return sents
    
    lengths={s:(len(templates[s].format(celeb=name, user=user, message='', link=''))+25)
                             for s in templates}
    topic_keys=stories_dict.keys() #get topics returned by the npr query
    i=randint(0, len(topic_keys)-1) #choose random topic
    stories=stories_dict[topic_keys[i]]
    j=randint(0,len(stories)-1) #choose random story within the topic
    link=stories[j]['link'][0]['$text']
    
    k=randint(0,1)
    
    if stories[j].has_key('teaser') and k==0:
        message=stories[j]['teaser']['$text']
        message=trimMessage(message, lengths[topic_keys[i]])
        
    else:
        message=stories[j]['text']['paragraph'][0]['$text']
        message=trimMessage(message, lengths[topic_keys[i]])
        
    response=templates[topic_keys[i]].format(celeb=name, user=user, message=message, link=link)
    
    return response


def getNPRStories(startDate=date.today()-timedelta(days=7), endDate=date.today()):
    url_line='http://api.npr.org/query'
    def getParamDict():
        params = {'meta':'none',
          'id':'{topic}',
          'fields':','.join(['storyDate','text','listText','pullQuote','teaser','title']), 
          'requiredAssets':'image',
          'startDate':str(startDate),
          'endDate':str(endDate),
          'dateType':'story',
          'sort':'featured',
          'output':'JSON', 
          'numResults':'40',
          'apiKey':'MDE3NDQzNTkzMDE0MTYxOTA0OTQyYjgzYw001'}
        return params
          
   
    topic_list=['358046323','173814508','156490415','1008','1060','1049','1025','1052','1136','1129',
                                        '1024','1007','1004','1056']
    
    params_dict={}
    for topic in topic_list:
        params=getParamDict()
        params['id']=params['id'].format(topic=topic)
        params_dict[topic]=params
    
   
        
    story_dict_json={ p: requests.get(url_line, params=params_dict[p]).json()
                                      for p in params_dict}       
    
    story_dict={topic:story_dict_json[topic]['list']['story']
                        for topic in story_dict_json 
                            if story_dict_json[topic]['list'].has_key('story')}
        
    
        
        
        
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
          #1024,#Research News
          #1007,#Science
          #1004,#World
          #1056, #World Story of the Day

    return story_dict



def get_id_str_list_old(name_list, celeb_word_list, conn, limit=10):
    to_respond={name:[tweet['id_str'] for tweet in searchMongo(name,celeb_word_list[name], conn, limit)] for name in name_list}
    return to_respond

# Connection to Mongo DB
def connectMongo():
    try:
        conn=pymongo.MongoClient()
        print "Connected successfully!!!"
    except pymongo.errors.ConnectionFailure, e:
       print "Could not connect to MongoDB: %s" % e 
    return conn

def searchMongo(name,word_list,conn, limit=10):



    query={'text':{'$in':yes_list, '$nin':no_list}}
    print 'got tweets for '+ str(name)
    
    return list(conn.find(query).limit(limit))
    
    
    
def get_id_str_list(name_list, celeb_word_list, conn, limit=10):
    print limit
    
    re_names=[re.compile(r'{0}\s?{1}'.format(splitName(name)[0], splitName(name)[1]), re.I) 
                                            for name in name_list]
    
    results=list(conn.find(getQuery(name_list, celeb_word_list)).limit(limit))
    print 'results',results
    print 're_names', re_names
    
    to_respond={tweet['id_str']:name for tweet in results 
                                        for r,name in zip(re_names,name_list) if re.search(r, tweet['text'])}
     
    print to_respond                                   
                                        
    return to_respond    

def getQuery(name_list, word_list):
    query={'text':{'$in': [] , '$nin':[]}}
    for name in name_list:
        regex_list=getRegex(name, word_list[name])
        query['text']['$in'].extend(regex_list[0])
        query['text']['$nin'].extend(regex_list[1])
    
    return query
  

def splitName(name):
    name=name.split(' ')
    if(len(name)>1):
        first=name[0]
        last=name[1]
    else:
        first=name[0]
        last='' 
    return first, last
              
def getRegex(name, word_list):
    
    first,last=splitName(name)         
    format_line=r'({word}.*{first}\s?{last})|({first}\s?{last}.*{word})'
    line1=r'({word}.*{first}\s?{last})'
    line2=r'({first}\s?{last}.*{word})'
    lines=[line1, line2]
    
    
    yes_list=[ re.compile(format_line.format(first=first, last=last, word=word), re.I)
                        for word in word_list['yes']] 
    if len(word_list['yes'])==0:
        yes_list=[re.compile(r'{first}\s?{last}'.format(first=first, last=last,word=''),re.I)]
    
    word_list['no'].append('http') 
    word_list['no'].append(r'\n\n\n\n')   
    
    no_list=[re.compile(line.format(first=first,last=last, word=word), re.I) 
                         for word in word_list['no'] if len(word)!=0
                                         for line in lines] 

    return yes_list, no_list
    

def isAscii(mystring):
    try:
        mystring.decode('ascii')
    except UnicodeDecodeError:
        print "it was not a ascii-encoded unicode string"
        return False
    else:
        print "It may have been an ascii-encoded unicode string"
        return True
    

if __name__ == "__main__":

    user_ids={'date':datetime.utcnow(), 'id_list':[]}
    nrp_query_time=datetime.utcnow()
    last_tweet='0'
    first_tweet='0'
    last_status='0'
    tweet_list=[]
    search_more=False
    SEARCH_LIM=10
    search_lim=SEARCH_LIM
    conn=connectMongo()['twitter']['lines']
    sleep_int=60
    

    bot = oauth_login()
    bot_name ='@'+bot.account.verify_credentials()['screen_name'] #put your actual bot's name here
    print bot_name
    bot_id=bot.account.verify_credentials()['id']
    print bot_id

    

    if os.path.exists("responded_list.txt") and os.path.getsize('responded_list.txt') > 0:
		f = open("responded_list.txt", "r")
		last_tweet=f.readline().split(' ')[1].strip()
		first_tweet=f.readline().split(' ')[1].strip()
		last_status=f.readline().split(' ')[1].strip()
		user_ids['date'] = datetime.strptime(f.readline(), '%x %X\n')
		nrp_query_time = datetime.strptime(f.readline(), '%x %X\n')
		user_ids['id_list']=[line.strip() for line in f.readlines()]
		f.close()
    
    
    if os.path.exists("responded_pkl") and os.path.getsize('responded_pkl') > 0:
		f = file("responded_pkl", "r")
                tweet_list=pkl.load(f)
		f.close()    
    
    print 'tweet_list', tweet_list
    
    stories=getNPRStories()
    
    
    print user_ids['date'], user_ids['id_list']
    #main loop. Just keep searching anyone talking to us
	#a specific user will only get one response per day 
    to_respond=[]
    
    while True:
 
        try:     
          
            if (user_ids['date']-datetime.utcnow()).days>=7:
                user_ids['date']=datetime.utcnow()
                user_ids['id_list']=[]
           
            if (nrp_query_time-datetime.utcnow())>1:
                stories=getNPRStories()
            
            if stories==None:
                stories=getNPRStories()
        
            #name_list=['katy perry','justin bieber', 'britney spears', 'kim kardashian', 'miley cyrus', 'taylor swift']
            
            if len(to_respond)==0:
                print 'searching for tweets'
                id_list_str=get_id_str_list(name_list,celeb_word_list, conn, limit=search_lim)
                print id_list_str
                print 'getting rid of the tweets we already responded to', time.ctime()
                id_list_str={tweet_id:id_list_str[tweet_id] for tweet_id in id_list_str if tweet_id not in tweet_list}
                                    
                if len(id_list_str)==0:  #everything was a repeat
                        search_lim+=SEARCH_LIM                  
                 
                else:                               #otherwise, get a respond lis
                    to_respond=id_list_str.keys()
                    if len(tweet_list)>0:           # and see if mongoDB has new entries
                        max_last_tweet=str(max([int(t) for t in tweet_list]))
                        if int(to_respond[0])>int(max_last_tweet): #if it does, roll back to searching 10 tweets per search
                            search_lim=SEARCH_LIM
                        else:
                            search_lim+=SEARCH_LIM   #if it doesn't, increment the search by 10
            

        

            if len(to_respond)!=0:
                            last_tweet=to_respond.pop()
                            
                            status = make_twitter_request(bot.statuses.user_timeline)
                            if len(status) > 0:
                                last_status = status[0]['id_str']
                                print 'last_id', last_status    
                            
                            
                            # reply to one of the users pulled out from DB
                        #======================================================== 
                            mention=make_twitter_request(bot.statuses.show,_id=int(last_tweet))

                            if mention!=None:
                                if mention['user']['id_str'] in user_ids['id_list']: #check if the user has been responded to in the past 7 days
                                            #tweet_list.append(last_tweet)
                                            sleep_int=15
                                            print time.ctime()
                                
                                elif  not isAscii(mention['text']):
                                          tweet_list.append(last_tweet)                      
                                else:
                                    sleep_int=2*60            
                                    user_ids['id_list'].append(mention['user']['id_str'])
                                    message = mention['text']
                                    speaker = mention['user']['screen_name']
                                    _id=mention['id']
                                    print "[+] " + speaker + " is saying " + message
                                    reply=getResponse2(id_list_str[last_tweet], speaker , stories)
                                    print "[+] Replying " , reply
                                    #_id=532812179049676800 #would need to comment out once we have a real message
                                    make_twitter_request(bot.statuses.update, status=reply,in_reply_to_status_id=_id)
                                    tweet_list.append(last_tweet)
                                    print time.ctime(), 'appending the tweet', mention['text'], last_tweet, tweet_list
                            #===================================                 
                            #then respond to all the mentions (based on the last reply)
                            #===========================================
                            if last_status!='0':
                                mentions = make_twitter_request(bot.statuses.mentions_timeline, since_id=int(last_status))
                            else:
                                mentions = make_twitter_request(bot.statuses.mentions_timeline)
        
                            if not mentions:
                                print "No one talking to us now...", time.ctime()
                                
                            else:
                                
                                mentions.reverse()
                                theonion=make_twitter_request(bot.users.lookup, user_id=14075928)
                            
                                for mention in mentions: 
                                  #  print mention['id'], last_status, time.ctime(), 'mentions1'
                                    if mention['id'] > int(last_status) and mention['user']['id']!=bot_id: #does not respond to itself
                                        print 'current mention_id ',mention['id']
                                        message = mention['text'].replace(bot_name, '')
                                        speaker = mention['user']['screen_name']
                                        _id = mention['id']
                                        #speaker_id = str(mention['id'])
                                        print "[+] " + speaker + " is saying " + message
                                        #reply=getResponse2('', 'color_blind_if' , stories) 
                                        reply='@'+speaker+'  @TheOnion '+theonion[0]['status']['text']
                                        onion_image=''
                                        if theonion[0]['status'].has_key('media_url'):
                                                onion_image=theonion[0]['status']['media_url']
                                        if len(reply)>140:
                                                reply=getResponse2('world', speaker , stories)
                                        print "[+] Replying " , reply
                                        make_twitter_request(bot.statuses.update, status=reply,in_reply_to_status_id=_id, media_url=onion_image)
                                
                               
                                                                 
                            #sleep_int = 60*2#downtime interval in seconds 
                            "Sleeping...\n"
                            time.sleep(sleep_int)
    
                        
            else:
                status = make_twitter_request(bot.statuses.user_timeline)
                if len(status) > 0:
                        last_status = status[0]['id_str']
                        print 'last_id', last_status  
                        
                            #===================================                 
                            #then respond to all the mentions (based on the last reply)
                            #===========================================
                if last_status!='0':
                        mentions = make_twitter_request(bot.statuses.mentions_timeline, since_id=int(last_status))
                else:
                        mentions = make_twitter_request(bot.statuses.mentions_timeline)
        
                if not mentions:
                        print "No one talking to us now...", time.ctime()
                        
                #mentions=[mentions[(len(mentions)-i-1)] for i in xrange(len(mentions))] #reverse the list
                else:
                    mentions.reverse()
                            
                    theonion=make_twitter_request(bot.users.lookup, user_id=14075928)
                            
                    for mention in mentions: 
                            print mention['id'], last_status, time.ctime(), 'mentions2'
                            if mention['id'] > int(last_status) and mention['user']['id']!=bot_id: #does not respond to itself
                                    print 'current mention_id ',mention['id']
                                    message = mention['text'].replace(bot_name, '')
                                    speaker = mention['user']['screen_name']
                                    _id = mention['id']
                                    #speaker_id = str(mention['id'])
                                    print "[+] " + speaker + " is saying " + message
                                    #reply=getResponse2('', 'color_blind_if' , stories) 
                                    reply='@'+speaker+'  @TheOnion '+theonion[0]['status']['text']
                                    onion_image=''
                                    if theonion[0]['status'].has_key('media_url'):
                                            onion_image=theonion[0]['status']['media_url']
                                    if len(reply)>140:
                                            reply=getResponse2('world', speaker , stories)
                                    print "[+] Replying " , reply
                                    make_twitter_request(bot.statuses.update, status=reply,in_reply_to_status_id=_id, media_url=onion_image)
                                
                               
                                                                 
                sleep_int = 60#downtime interval in seconds
                print "Sleeping...\n"
                time.sleep(sleep_int)
                        
                        
                        
                        
                        
                        
            
        except KeyboardInterrupt:
                print"[!] Cleaning up. last_id was ", last_tweet
               
                if len(tweet_list)>0:  #alternative
                #if last_tweet!=0
                    with open('responded_list.txt','w') as f:
                        f.write('last '+last_tweet.strip()+'\n')
                        f.write('first '+first_tweet.strip()+'\n')
                        f.write('status '+last_status.strip()+'\n')
                        f.write(user_ids['date'].strftime('%x %X\n'))
                        f.write(nrp_query_time.strftime('%x %X\n')) 
                        for line in user_ids['id_list']:
                            f.write(line+'\n') 
                        
                    print tweet_list        
                    with open('responded_pkl','w') as f:
                        pkl.dump(tweet_list, f)
                    with open('tweet_list.txt','w') as f:
                        for line in tweet_list:
                            f.write(line+'\n') 
                        
                sys.exit()
                
        except exceptions.BaseException, e: #in case of some error/exception - just skipping that post
                print e
                sleep_int = 60 #downtime interval in seconds
                print "Sleeping...error\n"
                time.sleep(sleep_int)
