r"""
                                                             
        _____                                               
  _____/ ____\______ ________________    ____   ___________ 
 /  _ \   __\/  ___// ___\_  __ \__  \  /  _ \_/ __ \_  __ \
(  <_> )  |  \___ \\  \___|  | \// __ \(  <_> )  ___/|  | \/
 \____/|__| /____  >\___  >__|  (____  /\____/ \___  >__|   
                 \/     \/           \/            \/         
"""
import time
import asyncio
import httpx
from tenacity import retry,stop_after_attempt,wait_random
from tqdm.asyncio import tqdm
global sem
sem = asyncio.Semaphore(8)
from ..constants import (
    timelineEP, timelineNextEP,
    timelinePinnedEP,
    archivedEP, archivedNextEP,timelinePinnedNextEP 
)
from ..utils import auth
from ..db.operations import read_timeline_response,read_archive_response\
,read_pinned_response
@retry(stop=stop_after_attempt(5),wait=wait_random(min=5, max=20),reraise=True)   
def scrape_pinned_posts(headers, model_id,timestamp=0) -> list:
    with httpx.Client(http2=True, headers=headers) as c:
        ep = timelinePinnedNextEP if timestamp else timelinePinnedEP
        url = ep.format(model_id, timestamp)
        # url = timelinePinnedEP.format(model_id)

        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = c.get(url, timeout=None)
        if not r.is_error:
            return r.json()['list']
        r.raise_for_status()

def get_pinned_post(headers,model_id,username):
    return scrape_pinned_posts(headers,model_id)
   
@retry(stop=stop_after_attempt(1),wait=wait_random(min=5, max=20),reraise=True)   
async def scrape_timeline_posts(headers, model_id, timestamp=None,recursive=False) -> list:
    
    if timestamp:
        timestamp=str(timestamp)
        ep = timelineNextEP
        url = ep.format(model_id, timestamp)
    else:
        ep=timelineEP
        url=ep.format(model_id)
    async with sem:
        async with httpx.AsyncClient(http2=True, headers=headers) as c:
            auth.add_cookies(c)
            c.headers.update(auth.create_sign(url, headers))
            r = await c.get(url , timeout=None)
            if not r.is_error:
                posts = r.json()['list']
    
                if not posts:
                    return []
                elif len(posts)==0:
                    return []
                elif not recursive:
                    return posts
                # recursive search for posts
                global tasks
                tasks.append(asyncio.create_task( scrape_timeline_posts(headers, model_id,posts[-1]['postedAtPrecise'],recursive=True)))
                return posts
           
            r.raise_for_status()
#max result is 50, try to get 40 in each async task for leeway
# Also need to grab new posts
async def get_timeline_post(headers,model_id,username):
    oldtimeline=read_timeline_response(model_id,username)
    postedAtArray=sorted(list(map(lambda x:float(x["postedAtPrecise"]),oldtimeline)))
    global tasks
    tasks=[]
    if len(postedAtArray)>0:
        split=min(40,len(postedAtArray))
        splitArrays=[postedAtArray[i:i+split] for i in range(0, len(postedAtArray), split)]
        #-100 because we want it to be inclusive
        tasks.extend(list(map(lambda x:asyncio.create_task(scrape_timeline_posts(headers,model_id,tasks,timestamp=x[0]-100)),splitArrays)))
        tasks.append(asyncio.create_task(scrape_timeline_posts(headers,model_id,timestamp=splitArrays[-1][-1],recursive=True)))
    else:
        tasks.append(asyncio.create_task(scrape_timeline_posts(headers,model_id,recursive=True)))

    responseArray=[]
   
   
    page_count=0 
    desc = 'Pages Progress: {page_count}'   

    with tqdm(desc=desc.format(page_count=page_count), colour='cyan',position=2) as main_bar:
        while len(tasks)!=0:
            for coro in asyncio.as_completed(tasks):
                result=await coro
                page_count=page_count+1
                main_bar.set_description(desc.format(page_count=page_count), refresh=False)
                main_bar.update()
                responseArray.extend(result)
            time.sleep(2)
            tasks=list(filter(lambda x:x.done()==False,tasks))
    unduped=[]
    dupeSet=set()
    for post in sorted(responseArray,key=lambda x:x["postedAtPrecise"]):
        if post["id"] in dupeSet:
            continue
        dupeSet.add(post["id"])
        unduped.append(post)
    return unduped                                


def get_archive_post(headers,model_id,username):
    return scrape_archived_posts(headers,model_id)
   

@retry(stop=stop_after_attempt(5),wait=wait_random(min=5, max=20),reraise=True)   
def scrape_archived_posts(headers, model_id, timestamp=0) -> list:
    ep = archivedNextEP if timestamp else archivedEP
    url = ep.format(model_id, timestamp)

    with httpx.Client(http2=True, headers=headers) as c:
        auth.add_cookies(c)
        c.headers.update(auth.create_sign(url, headers))

        r = c.get(url, timeout=None)
        if not r.is_error:
            posts = r.json()['list']
            if not posts:
                return posts
            posts += scrape_archived_posts(
                headers, model_id, posts[-1]['postedAtPrecise'])
            return posts
        r.raise_for_status()


def parse_posts(posts: list):
    data = list(filter( lambda x:x.get('media')!=None,posts))
    # [  'data']
    output=[]
    for ele in data:
        medialist=list(filter(lambda x:x["canView"],ele["media"]))
        for count,media in enumerate(medialist):
            output.append({"responsetype":ele["responseType"],"id":media["id"],"date":media["createdAt"]
            ,"text":ele["text"],"count":count+1,"url":media["source"]["source"],"mediatype":media["type"],"data":ele})
    return output



