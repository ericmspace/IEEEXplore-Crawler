import re
import time
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from fake_useragent import UserAgent
from selenium.webdriver.common.by import By

def get_html(url, headers):
    try:
        response = requests.get(url, timeout=40, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        print(f"请求失败: {e}")
        return None

def download_pdf(html_content, headers, index):
    soup = BeautifulSoup(html_content, 'html.parser')
    result = soup.body.find_all('iframe')
    download_url = result[-1].attrs['src'].split('?')[0]
    response = requests.get(download_url, timeout=120, headers=headers)
    cleaned_filename = re.sub('[\\\\/*?:"<>|]', '', download_url[-12:])
    fname = f"{index}_{cleaned_filename}"
    with open(fname, 'wb') as f:
        print(f'开始下载文件 {fname}')
        f.write(response.content)

def setup_browser():
    browser_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\MicrosoftWebDriver.exe'
    service = Service(executable_path=browser_path)
    return webdriver.Edge(service=service)

def read_doi_list():
    with open('data.txt', 'r') as f:
        return f.read().splitlines()

# 主程序
if __name__ == "__main__":
    ua = UserAgent()
    headers = {'user-agent': ua.random}
    base_url = 'https://ieeexplore.ieee.org/search/searchresult.jsp?action=search&newsearch=true&searchField=Search_All&matchBoolean=true&queryText="DOI":'
    doi_list = read_doi_list()
    
    with setup_browser() as browser:
        for index, doi in enumerate(doi_list):
            try:
                url = base_url + doi
                browser.get(url)
                time.sleep(10)
                link_list = browser.find_elements(By.XPATH, "//a[@aria-label='PDF']")
                if not link_list:
                    print(f'第{index + 1}篇论文未找到有效链接')
                    continue
                href = link_list[0].get_attribute('href')
                art_num = href.split('arnumber=')[1].split('&')[0]  # 从链接中解析出arnumber值
                print(f"文章编号：{art_num}")
                pdf_url = f'http://ieeexplore.ieee.org/stamp/stamp.jsp?tp=&arnumber={art_num}'
                html_content = get_html(pdf_url, headers)
                download_pdf(html_content, headers, index)
            except Exception as e:
                print(f"处理DOI {doi}时出错: {e}")
