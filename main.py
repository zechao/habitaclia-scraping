import requests
from bs4 import BeautifulSoup
import csv
header = {
    "accept": " text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
    "accept-encoding": " gzip, deflate, br",
    "accept-language": " es",
    "user-agent": " Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
}

variables ={
    'nombre',
    'descripcion',
    'precio',
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


def requests_page(page_idx=None):
    page = requests.get('https://www.habitaclia.com/alquiler-palma_de_mallorca{}.htm'.format(
        '' if page_idx == 0 else '-'+str(page_idx)))
    soup = BeautifulSoup(page.text, features="html.parser")
    section = soup.find('section', {'class': 'list-items'})
    all_articles = section.find_all('article')

    result = []

    for article in all_articles:
        if 'data-href' in article.attrs:
            result.append(article['data-href'])
    return result


def resolve_each_page(url):
    page = requests.get(url)
    soup = BeautifulSoup(page.text, features="html.parser")
    summary = soup.find('div', {'class':'summary-left'})
    price = summary.find('div',{'class':'price'}).find('span',{'class':'font-2'}).string
    name=summary.h1.string
    district=summary.find('a',{'id':'js-ver-mapa-zona'}).string

    feature_container = summary.find('ul',{'class':'feature-container'}).find_all('li')

    area= feature_container[0].strong.string
    roomNum = feature_container[1].strong.string
    bathNum = feature_container[2].strong.string
    
    detail_container = soup.find('section',{'class':'detail'})

    print(url)

    description = detail_container.find('h3',{'id':'js-detail-description-title'}).string +'\n' +detail_container.find('p',{'id':'js-detail-description'}).string
   
    general_feature_detal =detail_container.find('h3',string='Características generales').next_sibling.next_sibling
   
    feature_list = general_feature_detal.find_all('li',attrs={'class': None})

    features = []
    for each in feature_list:
        features.append(each.string)
    features_str = ";".join(features)
    print('price',':',price)
    print('name',':',name)
    print('district',':',district)
    print('area',':',area)
    print('roomNum',':',roomNum)
    print('bathNum',':',bathNum)
    print('description',':',description)
    print('features_str',':',features_str)    
    print('------------------------------------------')

all_results = []

for page_idx in range(1):
    all_results = all_results + requests_page(0)

for page in all_results:
    resolve_each_page(page)