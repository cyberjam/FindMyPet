from flask import Flask
import googlemaps
import folium
import requests
from lxml import etree
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.request import urlopen

app = Flask(__name__)

def crawl_find():
    result_2 = {}
    flag = 1
    page = 1
    while flag:
        url =  f"http://www.angel.or.kr/index.php?code=dog&page={page}&ski=&sci=%EB%8C%80%EC%A0%84%EA%B4%91%EC%97%AD%EC%8B%9C&sco=&sgu=&q=&style=webzine&listType=&sgu=L"
        response = urlopen(url)
        htmlparser = etree.HTMLParser()
        tree = etree.parse(response , htmlparser)

        find_img_list = tree.xpath('/html/body/div[4]/div/div/div[1]/div/div[1]/div/div[1]/a/img/@src')
        find_list = tree.xpath('/html/body/div[4]/div/div/div[1]/div/div[1]/div/p/text()[1]')
        find_day_list = tree.xpath('/html/body/div[4]/div/div/div[1]/div/div[1]/div/p/text()[3]')

        if not find_list:
            flag = 0
        else:
            page+=1
            for idx, elem in enumerate(zip(find_img_list,find_list,find_day_list)):
                result_2[f'{page}_{idx}'] = {}
                result_2[f'{page}_{idx}']['img_url'] = elem[0]
            
                address = elem[1]
                if '대전' not in address:
                    address = '대전광역시 '+ address
                result_2[f'{page}_{idx}']['address'] = address

                day= elem[2].split('(')[-1][:-1] # 실종날짜 (2020-7-5)
                day=list(map(int,day.split("-")))
                result_2[f'{page}_{idx}']['day'] = day
    return result_2

def view_find(view,result_2,gmaps):
    
    for key, elem in result_2.items():
        address = elem['address']
        url = elem['img_url']
        day = elem['day']
        
        try:
            geocode_result = gmaps.geocode(address)
            location = list(geocode_result[0]['geometry']['location'].values())
            
            image_tag = f'''<img src="{url}", height="150" width=auto>
            <p style="font-size:70%;">실종 날짜 : {day[0]}년 {day[1]}월 {day[2]}일</p>
            <p style="font-size:70%;">실종 장소 : {address.replace("대전광역시","").strip()}</p>'''
            iframe = folium.IFrame(image_tag, width=180, height=250)
            popup = folium.Popup(iframe, max_width=650)
            
            folium.Marker(location, popup=popup, tooltip=address , icon=folium.Icon(icon='cloud', color = 'red')).add_to(view)
            folium.Circle(location, radius=1000, color='#FCAE60', fill_color='#FCAE60').add_to(view)
        except:
            print(address, geocode_result)

def crawl_detect():
    result = {}
    flag = 1
    page = 1

    while flag:
        url = f"https://www.daejeon.go.kr/ani/AniStrayAnimalList.do?pageIndex={page}&menuSeq=3108&searchCondition=1&searchCondition2=&searchCondition3=1&searchCondition4=0&searchKeyword=&flag=1&gubun="
        res = requests.post(url)
        html = res.text
        soup = BeautifulSoup(html, 'html.parser')
        address_raw_bulk = soup.select(
            '#contents > div.contents > div.board_top > ul > li > ul > li:nth-child(5)'
            )
        img_raw_bulk = soup.select(
            '#contents > div.contents > div.board_top > ul > li > a > img'
            )
        day_url_bulk = soup.select(
            '#contents > div.contents > div.board_top > ul > li > a'
        )
        
        if not address_raw_bulk:
            flag = 0
        else:
            img_bulk = ['https://www.daejeon.go.kr/'+img.get('src') for img in img_raw_bulk]
            address_bulk = [address.text.split(':')[-1] for address in address_raw_bulk]
            day_url_bulk = ['https://www.daejeon.go.kr/'+url.get('href') for url in day_url_bulk]
        
            for idx, elem in enumerate(zip(img_bulk,address_bulk)):
                result[f'{page}_{idx}']={}
                result[f'{page}_{idx}']['img_url'] = elem[0]
                address = elem[1]
                
                if '대전' not in address:
                    address = '대전광역시 '+ address
                result[f'{page}_{idx}']['address'] = address

            for idx, url in enumerate(day_url_bulk):
                res_2 = requests.get(url)
                html_2 = res_2.text
                soup_2 = BeautifulSoup(html_2, 'html.parser')
                day = soup_2.select(
                    '#contents > div.contents > div > div:nth-child(1) > table > tbody > tr:nth-child(9) > td'
                )
                result[f'{page}_{idx}']['day'] = list(map(int,day[0].text.split('-')))
            page+=1
    return result

def view_detect(view,result,gmaps):
    for key, elem in result.items():
        address = elem['address']
        url = elem['img_url']
        day = elem['day']
        
        try:
            geocode_result = gmaps.geocode(address)
            location = list(geocode_result[0]['geometry']['location'].values())
            
            image_tag = f'''<img src="{url}", height="150" width=auto>
                <p style="font-size:70%;">발견 날짜 : {day[0]}년 {day[1]}월 {day[2]}일
                <p style="font-size:70%;">발견 장소 : {address.replace("대전광역시","").strip()}</p>'''
            iframe = folium.IFrame(image_tag, width=180, height=250)
            popup = folium.Popup(iframe, max_width=650)
            
            folium.Marker(location, popup=popup, tooltip=address , icon=folium.Icon(icon='cloud')).add_to(view)
            folium.Circle(location, radius=1000, color='#3186cc', fill_color='#3186cc').add_to(view)
        except:
            print(address, geocode_result)
 
@app.route('/')
def index():
    gmaps_key = "PUT UR KEY"
    gmaps = googlemaps.Client(key=gmaps_key)
    geocode_result = gmaps.geocode('대전시')
    center = list(geocode_result[0]['geometry']['location'].values())
    view = folium.Map(location=center, zoom_start=12, tiles='Stamen Terrain')

    print(" 1. map init complete")

    result_find = crawl_find()
    print(" 2-1. find data complete")
    view_find(view,result_find,gmaps)
    print(" 2-2. find map complete")

    result_detect = crawl_detect()
    print(" 3-1. detect data complete")
    view_detect(view,result_detect,gmaps)
    print(" 3-2. detect data complete ")
    print(" FINISH ")

#     start_coords = (46.9540700, 142.7360300)
#     folium_map = folium.Map(location=start_coords, zoom_start=14)
    return view._repr_html_()


if __name__ == '__main__':
    app.run(debug=True)