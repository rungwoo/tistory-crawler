import requests
from bs4 import BeautifulSoup
from datetime import datetime
import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials

# 1. 환경변수에서 구글 인증 정보 불러오기
google_json = os.environ['GOOGLE_SERVICE_ACCOUNT_JSON']
google_sheet_id = os.environ['GOOGLE_SHEET_ID']

# 2. JSON 문자열을 파일로 저장 (임시)
with open('service_account.json', 'w') as f:
    f.write(google_json)

# 3. 구글 시트 인증
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
credentials = ServiceAccountCredentials.from_json_keyfile_name('service_account.json', scope)
gc = gspread.authorize(credentials)
sheet = gc.open_by_key(google_sheet_id).sheet1  # 시트 이름이 'sheet1'이면 그대로 사용 가능

# 4. 티스토리 블로그 설정
BASE_URL = 'https://bomiiii.tistory.com'
MAX_PAGES = 5  # 최대 몇 페이지까지 긁을지 설정

# 5. 크롤링 함수
def crawl_posts():
    results = []
    for page in range(1, MAX_PAGES + 1):
        url = f'{BASE_URL}/?page={page}'
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'html.parser')
        posts = soup.select('a.link_title')  # 북클럽 스킨에 맞는 클래스

        if not posts:
            print(f"{page}페이지에서 포스트를 찾을 수 없습니다.")
            break

        for post in posts:
            title_tag = post.select_one('strong.title_post')
            title = title_tag.text.strip() if title_tag else post.text.strip()
            href = post['href']
            full_url = href if href.startswith('http') else BASE_URL + href

            # 카테고리 추출 (상세페이지 접근)
            post_res = requests.get(full_url)
            post_soup = BeautifulSoup(post_res.text, 'html.parser')
            category_tag = post_soup.find('meta', attrs={'property': 'article:section'})
            category = category_tag['content'] if category_tag else '없음'

            results.append([datetime.now().strftime('%Y-%m-%d'), title, full_url, category])

    return results

# 6. 결과 시트에 쓰기
data = crawl_posts()
if data:
    sheet.clear()
    sheet.append_row(['날짜', '제목', 'URL', '카테고리'])
    sheet.append_rows(data)
    print(f"{len(data)}개의 포스팅을 시트에 저장했습니다.")
else:
    print("포스팅이 없습니다.")
