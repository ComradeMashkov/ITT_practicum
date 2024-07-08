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

    path_to_document = reqv_body['path_to_document'] + '/document.html'
    armclass = reqv_body['armclass']

    html = await get_html_document(armclass)

    os.makedirs(os.path.dirname(path_to_document), exist_ok=True)
    with open(path_to_document, 'w', encoding='utf-8') as file:
        file.write(html)

    response.status_code = 200
    return f"File saved to: {os.path.abspath(path_to_document)}"


async def get_data_from_file(path_to_document: str) -> dict[str, tuple[str, list, list]]:
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
        armour_images_url = [href for href in hrefs if 'media' not in href and re.search('new/imagex/id(.*)-', href).group(1) == armour_id]
        armour_videos_url = [href for href in hrefs if 'media' in href and re.search('media/videos/id(.*)-', href).group(1) == armour_id]
        result[armour_id] = (armour_name, armour_images_url, armour_videos_url)

    return result


async def store_lostarmour_data(path_to_document: str) -> bool:
    try:
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
                "url_images": ';'.join(params[1]),
                "url_videos": ';'.join(params[2])
            }

            collection.insert_one(mongo_structure)

        client.close()

        return True

    except Exception as e:
        print('An error occurred:', e)
        return False

@app.post("/cache_lostarmour_data")
async def cache_lostarmour_data(response: Response, request: Request) -> None:
    try:
        reqv_body = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        print('Invalid JSON request')
        return None

    path_to_document = reqv_body['path_to_document']

    if not await store_lostarmour_data(path_to_document):
        response.status_code = 400
    else:
        response.status_code = 200


async def process_cached_data(armour_names: list):
    uri = "mongodb://%s:%s@%s" % (
        quote_plus('user'), quote_plus('pass'), 'localhost:27017')
    client = pymongo.MongoClient(uri)
    db = client['lostarmour_store']
    collection = db['tanks']

    documents = collection.find({"name": {"$in": armour_names}})

    return documents


@app.post("/download_images")
async def download_images(response: Response, request: Request) -> str | None:
    try:
        reqv_body = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        print('Invalid JSON request')
        return None

    path_to_images = reqv_body['path_to_images']
    armour_name = reqv_body['armour_names']

    documents = await process_cached_data(armour_name)

    os.makedirs(os.path.dirname(path_to_images), exist_ok=True)

    for doc in documents:
        urls_list = doc['url_images'].split(';')
        for cur_url in urls_list:
            image_data = requests.get(origin + cur_url).content
            image_name = cur_url[12:]
            with open(path_to_images + image_name, 'wb') as handler:
                handler.write(image_data)
                print(origin + cur_url, '->', os.path.abspath(path_to_images) + '/' + image_name)

    response.status_code = 200
    return f"Images saved to: {os.path.abspath(path_to_images)}"


@app.post("/download_videos")
async def download_videos(response: Response, request: Request) -> str | None:
    try:
        reqv_body = await request.json()
    except json.decoder.JSONDecodeError:
        response.status_code = 400
        print('Invalid JSON request')
        return None

    path_to_videos = reqv_body['path_to_videos']
    armour_name = reqv_body['armour_names']

    documents = await process_cached_data(armour_name)

    os.makedirs(os.path.dirname(path_to_videos), exist_ok=True)

    for doc in documents:
        urls_list = doc['url_videos'].split(';')
        for cur_url in urls_list:
            if cur_url:
                video_data = requests.get(origin + cur_url).content
                video_name = cur_url[14:]
                with open(path_to_videos + video_name, 'wb') as handler:
                    handler.write(video_data)
                    print(origin + cur_url, '->', os.path.abspath(path_to_videos) + '/' + video_name)

    response.status_code = 200
    return f"Videos saved to: {os.path.abspath(path_to_videos)}"
