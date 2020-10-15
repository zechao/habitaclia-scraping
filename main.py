import requests
from bs4 import BeautifulSoup
import csv
import sys
import os
import re
from multiprocessing import Lock
import concurrent.futures
import time
from bounded_pool_executor import BoundedProcessPoolExecutor

headers = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "es",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
}

# field names of our csv file.
variables = ['price',  # Mandatory
             'district',  # Mandatory
             'area',  # Mandatory
             'room_num',  # Mandatory
             'bath_num',  # Mandatory
             'furnished',  # Important info that affect the price
             'has_parking',  # Important info that affect the price
             'has_elevator',  # Important info that affect the price
             'has_air',  # Important info that affect the price
             'features_detail',  # detail info contains featureas of the floor which affect the price
             'name',  # contains useful information
             'description'  # contains a description written by the owner that contains useful information
             ]


# some url are invalid because the data are not belong to the original web, they belong to the partner web.
def valid_url(url):
    if re.match(r"^https:.*?.com/fa\d+$", url):
        return False
    return True


def request_page_number(city_name):
    url = 'https://www.habitaclia.com/alquiler-{}.htm'.format(city_name)
    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, features="html.parser")
    aside = soup.find(id='js-nav')
    li_next = aside.find('li', {'class': 'next'})
    if li_next == None:
        return 1
    else:
        max_page_text = li_next.previous_element.find_previous_sibling(
            'li').text.strip('\n')
        if max_page_text.isdigit():
            return int(max_page_text)
        else:
            print('Unknow error while getting max page number:', str(e))
            sys.exit(0)


def build_page_url(city_name, page_idx):
    url = 'https://www.habitaclia.com/alquiler-{}{}.htm'.format(city_name,
                                                                '' if page_idx == 0 else '-'+str(page_idx))
    return url


def requests_pages(city_name, page_idx=None):
    try:
        # first page without index, the rest we need concat the page index
        page = requests.get(build_page_url(
            city_name, page_idx), headers=headers)
        soup = BeautifulSoup(page.text, features="html.parser")
        section = soup.find('section', {'class': 'list-items'})
        all_articles = section.find_all('article')

        result = []
        # only articles with data-href
        for article in all_articles:
            if 'data-href' in article.attrs and valid_url(article['data-href']):
                result.append(article['data-href'])

        return result
    except Exception as e:
        print('Unknow error while requesting pages:', str(e))
        sys.exit(0)


def contain_text(text_to_search, *texts):
    for text in texts:
        if text_to_search in text.lower():
            return True
    return False


def true_false_none(true_str, false_str, *search_texts):
    result = None
    for text in search_texts:
        if true_str in text.lower():
            result = True
        if false_str in text.lower():
            result = False
    return result


def get_features(detail_container):
    features = []
    general_feature_detail = detail_container.find(
        'h3', string='Características generales')

    if general_feature_detail != None:
        general_feature_detail = general_feature_detail.find_next('ul')

        feature_list = general_feature_detail.find_all(
            'li', attrs={'class': None})

        for each in feature_list:
            text = each.string.strip()
            features.append(text)

    community_equipment = detail_container.find(
        'h3', string='Equipamiento comunitario')

    if community_equipment != None:
        community_equipment = community_equipment.find_next('ul')
        equipment_list = community_equipment.find_all('li')
        for each in equipment_list:
            text = each.string.strip()
            features.append(text)

    return features


def resolve_each_page(url):
    result = None

    page = requests.get(url, headers=headers)
    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find('div', {'class': 'summary-left'})
    price = summary.find('div', {'class': 'price'}).find(
        'span', {'class': 'font-2'}).string
    name = summary.h1.string

    if summary.find(id='js-ver-mapa-zona') == None:
        return None

    district = summary.find(id='js-ver-mapa-zona').string.strip()

    feature_container = summary.find(
        'ul', {'class': 'feature-container'}).find_all('li')

    area = None
    roomNum = None
    bathNum = None

    for feature in feature_container:
        if 'm2' in feature.text and '€/m2' not in feature.text:
            area = re.findall('[0-9]+', feature.text)[0]
        if 'hab.' in feature.text:
            roomNum = re.findall('[0-9]+', feature.text)[0]
        if 'baño' in feature.text:
            bathNum = re.findall('[0-9]+', feature.text)[0]

    detail_container = soup.find('section', {'class': 'detail'})

    description = '{}.{}'.format(detail_container.find(id='js-detail-description-title').text,
                                 detail_container.find(id='js-detail-description').text.replace('\r', '.').replace('\n', '.'))

    features = get_features(detail_container)

    # The following variables can be TRUE,FALSE or None
    furnished = None
    has_parking = None
    has_air = None
    has_elevator = None

    for text in features:
        text_lower = text.lower()
        if 'plaza parking' in text_lower:
            has_parking = true_false_none(
                'plaza parking', 'sin plaza parking', text)
        if 'amueblado' in text_lower or 'sin amueblar' in text_lower:
            furnished = true_false_none('amueblado', 'sin amueblar', text)
        if 'aire acondicionado' in text_lower:
            has_air = true_false_none(
                'aire acondicionado', 'sin aire acondicionado', text)
        if 'ascensor' in text_lower:
            has_elevator = true_false_none('ascensor', 'sin ascensor', text)

    features_detail = "%;%".join(features)
    result = {
        'price': price,
        'district': district,
        'area': area,
        'room_num': roomNum,
        'bath_num': bathNum,
        'furnished': furnished,
        'has_parking': has_parking,
        'has_elevator': has_elevator,
        'has_air': has_air,
        'features_detail': features_detail,
        'name': name,
        'description': description
    }
    return result


def get_pages(page_idx, city_name):
    pages = requests_pages(city_name, page_idx)
    results = []
    count = 0
    for page_url in pages:
        count = count+1
        try:
            print('Resolving Page:{},Count{},URL:{}'.format(
                page_idx, count, page_url))
            result = resolve_each_page(page_url)
            if result == None:
                print('ERROR!!!!NOT ENOUGH DATA!!!:{},\n'.format(page_url))
            else:
                results.append(result)
        except Exception as e:

            print('UNEXPECTED EROOR:[{}]!!:{}\n'.format(str(e), page_url))

    return results


if __name__ == "__main__":
    city_name = 'barcelona'
    # Get max page to resolve
    max_page_number = request_page_number(city_name)
    print('Max page number is:[{}], estimate url to resolve:[{}]'.format(
        max_page_number, max_page_number*15))

    # define number of worker to run,defeault None
    worker_num = None

    with open('dataset.csv', 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=variables)
        writer.writeheader()

        with concurrent.futures.ThreadPoolExecutor(worker_num) as executor:
            future_work = {executor.submit(get_pages, page_idx, city_name): page_idx for page_idx in (
                x for x in range(max_page_number))}
            for future in concurrent.futures.as_completed(future_work):
                page_idx = future_work[future]
                try:
                    results = future.result()
                    for result in results:
                        writer.writerow(result)
                except Exception as exc:
                    print('%r generated an exception: %s' % (results, exc))
