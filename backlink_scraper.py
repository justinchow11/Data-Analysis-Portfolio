
import datetime as dt
import json
import re
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from random import randrange
from time import sleep
from mysql import connector
from mysql.connector import errorcode


ua = UserAgent()

with open('params.json') as file:
    params = json.load(file)

def get_page(query, start, filter_val):
    payload = {'q': query, 'start': start, 'filter':filter_val}
    r = requests.get('http://www.google.com/search', params=payload, headers={'User-agent': ua.random})
    
    with open("test.txt", "a") as myfile:
        myfile.write('[' + str(dt.datetime.now()) + '] ' + query + ' start:' + str(start) + 
                     ' filter:' + str(start) + str(filter_val) + ' ' + str(r) + '\n')
    print(r)
    return BeautifulSoup(r.text, 'lxml')

def get_sites(soup, query):
    tags = soup.find_all('h3', class_='r')
    return [re.sub('^https?://(www.)?', '', x.a['href']) for x in tags]

def get_all_sites(query, filter_val, cnx, cursor):
    all_sites = []
    initial_pg = get_page(query, 0, filter_val)
    sleep(10)
    
    search_count_area = initial_pg.find("div", {"id":"resultStats"})
    result_count = re.findall('\d+.*results', search_count_area.text)[0]
    result_count = int(''.join(re.findall('\d+', result_count)))
    
    page_nums = range(0, result_count, 10)
    for n in page_nums:
        page = get_page(query, n, filter_val)
        sites = get_sites(page, query)
        if sites != []:
            tuple_list = []
            for item in sites:
                tuple_list.append((query[5:],) + (item,) + (n*10 + filter_val,))
            add_data(tuple_list, cnx, cursor)
        sleep(540)
    return 0

def get_data(cnx, cursor):
    count = 0
    data = []

    for filter_val in range(0,2):
        for query in params['queries']:
            q = query.replace(' ', '+')
            q = "link:" + q
            sites = get_all_sites(q, filter_val, cnx, cursor)
            count += 1
            print(count)
    print('DONE!', dt.datetime.now())

def get_db():
    config = {
      'user': 'username',
      'password': 'password',
      'host': 'yourdbinstance.cqzic8hp8eqe.us-east-1.rds.amazonaws.com',
      'database': 'db',
      'raise_on_warnings': True,
    }

    cnx = connector.connect(**config)
    cursor = cnx.cursor(buffered=True)
    return cnx, cursor

def add_data(data, cnx, cursor):
    add_linkdata = ("INSERT INTO link_data "
                   "(competitor, backlink, filter) "
                    "VALUES (%s, %s, %s)")

    cursor.executemany(add_linkdata, data)

    # Make sure data is committed to the database
    cnx.commit()

def main():
    cnx, cursor = get_db()
    get_data(cnx, cursor)
    cursor.close()
    cnx.close()

if __name__ == "__main__":
    main()
