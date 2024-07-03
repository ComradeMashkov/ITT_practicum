from bs4 import BeautifulSoup
from dotenv import load_dotenv
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from urllib.parse import quote_plus

import json
import os
import pymongo
import re
import requests

app = FastAPI()

load_dotenv()

url = os.getenv('URL')
accept = os.getenv('ACCEPT')
accept_language = os.getenv('ACCEPT_LANGUAGE')
cache_control = os.getenv('CACHE_CONTROL')
content_type = os.getenv('CONTENT_TYPE')
cookie = os.getenv('COOKIE')
origin = os.getenv('ORIGIN')
priority = os.getenv('PRIORITY')
referer = os.getenv('REFERER')
sec_ch_ua = os.getenv('SEC_CH_UA')
sec_ch_ua_mobile = os.getenv('SEC_CH_UA_MOBILE')
sec_ch_ua_platform = os.getenv('SEC_CH_UA_PLATFORM')
sec_fetch_dest = os.getenv('SEC_FETCH_DEST')
sec_fetch_mode = os.getenv('SEC_FETCH_MODE')
sec_fetch_site = os.getenv('SEC_FETCH_SITE')
sec_fetch_user = os.getenv('SEC_FETCH_USER')
upgrade_insecure_requests = os.getenv('UPGRADE_INSECURE_REQUESTS')
user_agent = os.getenv('USER_AGENT')


async def get_html_document(armclass: str) -> str:
    headers = {
        'accept': accept,
        'accept-language': accept_language,
        'cache-control': cache_control,
        'content-type': content_type,
        'cookie': cookie,
        'origin': origin,
        'priority': priority,
        'referer': referer,
        'sec-ch-ua': sec_ch_ua,
        'sec-ch-ua-mobile': sec_ch_ua_mobile,
        'sec-ch-ua-platform': sec_ch_ua_platform,
        'sec-fetch-dest': sec_fetch_dest,
        'sec-fetch-mode': sec_fetch_mode,
        'sec-fetch-site': sec_fetch_site,
        'sec-fetch-user': sec_fetch_user,
        'upgrade-insecure-requests': upgrade_insecure_requests,
        'user-agent': user_agent,
    }

    data = {
        'id': '',
        'bn': '',
        'armtype': '',
        'familytype': '',
        'armclass': armclass,
        'flag': '',
        'location': '',
        'addupdate': '',
        'date_from': '',
        'date_to': '',
    }

    response = requests.post(url=url, headers=headers, data=data)

    return response.text


@app.post("/load_html_document", response_class=HTMLResponse)
async def load_html_document(response: Response, request: Request) -> str | None:
    try:
        reqv_body = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        print('Invalid JSON request')
        return None

    armclass = reqv_body['armclass']
    save_document = reqv_body['save_document']

    response.status_code = 200
    html = await get_html_document(armclass)

    if save_document:
        filename = 'data/document.html'
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as file:
            file.write(html)
        return f"File saved to: {os.path.abspath(filename)}"

    return html


async def get_data_from_file(path_to_document: str) -> dict:
    soup = BeautifulSoup(open(path_to_document, encoding='utf-8'), 'html.parser')
    a_tags = soup.find_all('a', attrs={'data-caption': True})

    hrefs = [a.get('href') for a in a_tags]

    seen_captions = set()
    unique_captions = list()
    for a in a_tags:
        caption = a['data-caption']
        if caption not in seen_captions:
            seen_captions.add(caption)
            unique_captions.append(caption)

    result = dict()
    for caption in unique_captions:
        armour_id = caption[4:].replace(' - ', ':').split(':')[0]
        armour_name = caption[4:].replace(' - ', ':').split(':')[1]
        armour_url = [href for href in hrefs if 'media' not in href and re.search('new/imagex/id(.*)-', href).group(1) == armour_id]
        result[armour_id] = (armour_name, armour_url)

    return result


async def store_lostarmour_data(path_to_document: str) -> None:
    uri = "mongodb://%s:%s@%s" % (
        quote_plus('user'), quote_plus('pass'), 'localhost:27017')
    client = pymongo.MongoClient(uri)
    db = client["lostarmour_store"]
    collection = db["tanks"]

    document = await get_data_from_file(path_to_document)

    for armour_id, params in document.items():
        mongo_structure = {
            "id": armour_id,
            "name": params[0],
            "url": ';'.join(params[1])
        }

        collection.insert_one(mongo_structure)

    client.close()


@app.post("/cache_lostarmour_data")
async def cache_lostarmour_data(response: Response, request: Request):
    try:
        reqv_body = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        print('Invalid JSON request')
        return None

    path_to_document = reqv_body['path_to_document']

    await store_lostarmour_data(path_to_document)


async def process_cached_data(armour_names: list):
    uri = "mongodb://%s:%s@%s" % (
        quote_plus('user'), quote_plus('pass'), 'localhost:27017')
    client = pymongo.MongoClient(uri)
    db = client['lostarmour_store']
    collection = db['tanks']

    documents = collection.find({"name": {"$in": armour_names}})

    return documents


@app.post("/download_images")
async def download_images(response: Response, request: Request):
    try:
        reqv_body = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        print('Invalid JSON request')
        return None

    armour_name = reqv_body['armour_names']

    train_ratio = reqv_body['train']
    val_ratio = reqv_body['val']
    if train_ratio + val_ratio > 1.0:
        response.status_code = 400
        print('train + val must not exceed 1')
        return

    documents = await process_cached_data(armour_name)

    images_path = 'images/'
    os.makedirs(os.path.dirname(images_path), exist_ok=True)

    urls = list()
    image_names = list()
    for doc in documents:
        urls_list = doc['url'].split(';')
        for cur_url in urls_list:
            urls.append(origin + cur_url)
            image_names.append(cur_url[12:])

    total_number = len(urls)
    train_number = int(total_number * train_ratio)
    val_number = int(total_number * val_ratio)

    train_dir = images_path + 'train/'
    val_dir = images_path + 'val/'
    test_dir = images_path + 'test/'

    os.makedirs(os.path.dirname(train_dir), exist_ok=True)
    os.makedirs(os.path.dirname(val_dir), exist_ok=True)
    os.makedirs(os.path.dirname(test_dir), exist_ok=True)

    for i in range(1, total_number + 1):
        image_data = requests.get(urls[i - 1]).content

        if i < train_number:
            print(urls[i - 1], '->', os.path.abspath(train_dir) + '/' + image_names[i - 1])
            with open(train_dir + image_names[i - 1], 'wb') as handler:
                handler.write(image_data)

        elif i < train_number + val_number:
            print(urls[i - 1], '->', os.path.abspath(val_dir) + '/' + image_names[i - 1])
            with open(val_dir + image_names[i - 1], 'wb') as handler:
                handler.write(image_data)

        else:
            print(urls[i - 1], '->', os.path.abspath(test_dir) + '/' + image_names[i - 1])
            with open(test_dir + image_names[i - 1], 'wb') as handler:
                handler.write(image_data)

    return f"Train = {train_number}, Val = {val_number}, Test = {total_number - train_number - val_number}"
