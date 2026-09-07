import requests
import csv
from datetime import datetime
from urllib.parse import urljoin,urlparse
from urllib.robotparser import RobotFileParser
from bs4 import BeautifulSoup
import sqlite3
from collections import deque

START_URL=input("Enter the url of the website or page you want to crawl:")
MAX_PAGES=50
MAX_DEPTH=3

HEADERS={
    "User-agent":"WebCrawler/1.0"
}

conn=sqlite3.connect("crawler.db")
cursor=conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS crawler(
id INTEGER PRIMARY KEY AUTOINCREMENT,
url TEXT UNIQUE,
title TEXT,
status_code INTEGER,
crawled_at TEXT,
depth INTEGER)
)''')

conn.commit()

def setup_robots(url):
    parser=urlparse(url)
    robots=f"{parser.scheme}://{parser.netloc}/robots.txt"
    rp=RobotFileParser()
    rp.set_url(robots)
    try:
        rp.read()
        return rp
    except Exception:
        return None

def page(url,title,status_code,depth):
    cursor.execute('''
INSERT OR IGNORE INTO crawler(
url,title,status_code,crawled_at,depth) VALUES(?,?,?,?,?)
''',(
    url,title,status_code,datetime.now.strftime("%Y-%m-%d %H:%M:%S"),depth
))

conn.commit()

def crawl(START_URL):
    domain=urlparse(START_URL).netloc
    queue=deque([(START_URL,0)])
    visited=set()
    robot=setup_robots(START_URL)
    while queue and len(visited)<MAX_PAGES:
        url,depth=queue.popleft()
        if url in visited:
            continue
        if depth>MAX_DEPTH:
            continue
        if robot and not robot.can_fetch(
            HEADERS["User-Agent"],url
        ):
            print("Blocked by robots.txt",url)
            continue
        try:
            response=requests.get(url,headers=HEADERS,timeout=5)
            visited.add(url)
            print(
                f"Crawling:{url}|"
                f"Depth: {depth}"
                f"Status: {response.status_code}"
            )
            soup=BeautifulSoup(response.text,"html.parser")
            if soup.title:
                title=soup.title.get_text(strip=True)
            else:
                title="NO TITLE"
            page(url,title,response.status_code,depth)

            for link in soup.find_all("a",href=True):
                next_url=urljoin(url,link["href"])
                next_url=next_url.split("#")[0]
                parsed=urlparse(next_url)
                if (next_url not in visited and next_url not in queue):
                    queue.append(next_url,depth+1)
        except requests.RequestException as e:
            print("ERROR",e)
    return visited
visited=crawl(START_URL)
conn.close()
print("Crawling completed ")
print("Total page crawled: ",len(visited))

            

        


    



