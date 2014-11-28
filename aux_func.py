import exceptions
import pymongo
import re


def textFileForCeleb(name, limit):

    name=name.split(' ')
    if(len(name)>1):
        first=name[0]
        last=name[1]
    else:
        first=name[0]
        last=''
    
    conn=pymongo.MongoClient()['twitter']['lines']
    result=conn.find({'text':{'$regex':first+r'.?'+last, '$options':'is'}})
    text_r=[line['text'].strip() for line in list(result.limit(limit))]
    with open(first+'_'+last+'.txt', 'w') as f:
        for line in text_r:
               f.write(line+'\n')
               
               
               
def deletePosts(bot): #mass delete the posts
    
    statuses=bot.statuses.user_timeline()
    print len(statuses)
    for status in statuses:
        try:
            print 'deleting ', status['id']
            bot.statuses.destroy(id=status['id'])
        except exceptions.BaseException, e: #in case of some error/exception - just skipping that post
                        print e

