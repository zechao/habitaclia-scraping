import requests
from bs4 import BeautifulSoup
import csv
import sys
import re
header = {
    "accept": " text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": " gzip, deflate, br",
    "accept-language": " es",
    "user-agent": " Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
}

variables = {
    'name',
    'description',
    'price',
    'barrio',
    'nHabitacion',
    'nBanyo',
    'area',
    'nPlanta',
    'hayParking',
    'hayMueble',
    'hayAscensor',
    'aireAcondicionado',
    'calefaccion'
}


def check_robots_file():
    pass


def requests_pages(page_idx=None):
    try:
        # first page without index, the rest we need concat the page index
        page = requests.get('https://www.habitaclia.com/alquiler-palma_de_mallorca{}.htm'.format(
            '' if page_idx == 0 else '-'+str(page_idx)))
        soup = BeautifulSoup(page.text, features="html.parser")
        section = soup.find('section', {'class': 'list-items'})
        all_articles = section.find_all('article')

        result = []
        # only articles with data-href
        for article in all_articles:
            if 'data-href' in article.attrs:
                result.append(article['data-href'])

        return result
    except Exception as e:
        print('Unknow error:', str(e))
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


def resolve_each_page(url):
    result = None

    page = requests.get(url)
    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find('div', {'class': 'summary-left'})
    price = summary.find('div', {'class': 'price'}).find(
        'span', {'class': 'font-2'}).string
    name = summary.h1.string
    district = summary.find('a', {'id': 'js-ver-mapa-zona'}).string.strip()

    feature_container = summary.find(
        'ul', {'class': 'feature-container'}).find_all('li')

    area = None
    roomNum =None
    bathNum=None

    for feature in feature_container:
        if 'm2' in feature.text:
            area=re.findall('[0-9]+', feature.text)[0]
        if 'hab.' in feature.text:
            roomNum=re.findall('[0-9]+', feature.text)[0]
        if 'baño' in feature.text:
            bathNum= re.findall('[0-9]+', feature.text)[0]



    detail_container = soup.find('section', {'class': 'detail'})

    description = detail_container.find('h3', {'id': 'js-detail-description-title'}).text + \
        '.' + \
        detail_container.find(
            'p', {'id': 'js-detail-description'}).text.replace('\n\r', '.')

    general_feature_detal = detail_container.find(
        'h3', string='Características generales').next_sibling.next_sibling

    feature_list = general_feature_detal.find_all(
        'li', attrs={'class': None})

    features = []
    furnished = None  # check if the floor is furnished, it can be TRUE,FALSE or None
    has_parking = None  # check if has parking,it can be TRUE,FALSE or None
    has_air = None
    for each in feature_list:
        text = each.string.strip()
        features.append(text)
        has_parking = true_false_none(
            'plaza parking', 'sin plaza parking', text)
        furnished = true_false_none('amueblado', 'sin amueblar', text)
        has_air = true_false_none(
            'aire acondicionado', 'sin aire acondicionado', text)

        
    

    has_elevator =None
    community_equipment = detail_container.find('h3', string='Equipamiento comunitario')
    if community_equipment != None:
        community_equipment =detail_container.find('h3', string='Equipamiento comunitario').next_sibling.next_sibling
        equipment_list = community_equipment.find_all('li')
        has_elevator = None
        for each in equipment_list:
            text = each.string.strip()
            
            features.append(text)
            if 'ascensor' in text.lower():
                has_elevator = True

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


if __name__ == "__main__":
    all_pages = []
    for page_idx in range(4,5):
        all_pages = all_pages + requests_pages(page_idx)

    with open('dataset.csv', 'w', newline='', encoding='utf-8') as csvfile, open('err.log', 'w', encoding='utf-8') as errlog:
        writer = csv.DictWriter(csvfile, fieldnames=['price', 'district', 'area', 'room_num', 'bath_num',
                                                     'furnished', 'has_parking', 'has_elevator', 'has_air', 'features_detail', 'name', 'description'])
        writer.writeheader()
        for page in all_pages:
            try:
                result = resolve_each_page(page)

                if result == None:
                    errlog.write('{},ERROR!!!!NOT ENOUGH DATA!!!\n'.format(page))
                    continue

                writer.writerow(result)
            except IOError:
                print("Unknow io error:")
            except Exception as e:
                # catch all unchecked exepcetion
                errlog.write('{},{}\n'.format(page, str(e)))
