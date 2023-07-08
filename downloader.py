import logging

import requests
from bs4 import BeautifulSoup
import re

BASE_URL = 'https://apksfull.com'
VERSION_URL = f'{BASE_URL}/version/'
SEARCH_URL = f'{BASE_URL}/search/'
DOWNLOAD_URL = f'{BASE_URL}/dl/'
GOOGLE_PLAY_URL = 'https://play.google.com/store/apps/details?id='

headers = {
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_3_1 like Mac OS X) AppleWebKit/603.1.30 (KHTML, like Gecko) Version/10.0 Mobile/14E304 Safari/602.1',
    'Accept': 'application/json, text/javascript, */*; q=0.01',
    'Accept-Language': 'en-US,en;q=0.5',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Connection': 'keep-alive',
}


def download_apk(package_name):
    google_play_response = requests.get(GOOGLE_PLAY_URL + package_name,
                                        headers=headers, allow_redirects=True)
    if google_play_response.status_code != 200:
        return NameError("Invalid package name")

    search_response = requests.get(SEARCH_URL + package_name,
                                   headers=headers, allow_redirects=True)

    soup = BeautifulSoup(search_response.content, 'html.parser')

    sub_dl_links = ""
    for item in soup.findAll('a'):
        link = item.get('href')
        if link.find("/download/") != -1:
            sub_dl_links = BASE_URL + link
            break

    download_response = requests.get(sub_dl_links,
                                     headers=headers, allow_redirects=True)
    script_text = BeautifulSoup(
        download_response.content, 'html.parser').findAll("script")

    token = re.findall("token','([^\']+)", script_text[-2].contents[0])[0]

    download_page_response = requests.post(DOWNLOAD_URL, data={'token': token}, headers=headers)
    download_link = download_page_response.json()['download_link']

    output_file = f"output/{package_name}.apk"

    r = requests.get(download_link, allow_redirects=True, stream=True)
    with open(output_file, 'wb') as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    return package_name
