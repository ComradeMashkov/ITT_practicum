from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
import requests

app = FastAPI()


async def get_html_document(armclass: str):
    cookies = {
        '__ddg1_': 'VbDL1Ddm2Y1ttLnRDUtU',
        '_ga': 'GA1.1.1391103055.1719859094',
        '_ym_uid': '1719859095216662605',
        '_ym_d': '1719859095',
        '_ym_isad': '1',
        '__ddgid_': '0ykITtgQkXlFPFoo',
        '__ddgmark_': 'fvTDtRgdO84RQ3eP',
        '__ddg5_': 'oCX8w2MUNxXc3BGY',
        '_ga_S1J39HETHJ': 'GS1.1.1719942694.3.1.1719943725.0.0.0',
    }

    headers = {
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'cache-control': 'max-age=0',
        'content-type': 'application/x-www-form-urlencoded',
        # 'cookie': '__ddg1_=VbDL1Ddm2Y1ttLnRDUtU; _ga=GA1.1.1391103055.1719859094; _ym_uid=1719859095216662605; _ym_d=1719859095; _ym_isad=1; __ddgid_=0ykITtgQkXlFPFoo; __ddgmark_=fvTDtRgdO84RQ3eP; __ddg5_=oCX8w2MUNxXc3BGY; _ga_S1J39HETHJ=GS1.1.1719942694.3.1.1719943725.0.0.0',
        'origin': 'https://lostarmour.info',
        'priority': 'u=0, i',
        'referer': 'https://lostarmour.info/armour',
        'sec-ch-ua': '"Not/A)Brand";v="8", "Chromium";v="126", "Google Chrome";v="126"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36',
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

    response = requests.post('https://lostarmour.info/armour', cookies=cookies, headers=headers, data=data)

    return response.text


@app.post("/load_html_document", response_class=HTMLResponse)
async def load_html_document(response: Response, request: Request):
    reqv_body = await request.json()
    html = await get_html_document(reqv_body['armclass'])
    return html
