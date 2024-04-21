import time
from selenium import webdriver
from selenium.webdriver.edge.service import Service
from selenium.webdriver.common.by import By
import pandas as pd
import json
import random
from selenium.common.exceptions import NoSuchElementException, JavascriptException, TimeoutException

def setup_browser():
    browser_path = r'C:\Program Files (x86)\Microsoft\Edge\Application\MicrosoftWebDriver.exe'
    service = Service(executable_path=browser_path)
    options = webdriver.EdgeOptions()
    # options.add_argument('--headless')  # 如果不需要浏览器界面，可以启用无头模式
    return webdriver.Edge(service=service, options=options)

def scrape_conference_links(driver):
    """ 抓取所有会议链接 """
    driver.get("https://ieeexplore.ieee.org/recentlypublished/conferences")
    time.sleep(random.uniform(5, 15))  # 等待页面加载
    conferences = driver.find_elements(By.CSS_SELECTOR, "div.recently-published-item a.title")
    links = [conf.get_attribute('href') for conf in conferences]
    return links

def scrape_paper_links(driver, conference_url):
    """ 抓取一个会议中的所有论文链接，并去除重复项 """
    driver.get(conference_url)
    time.sleep(5)
    paper_links = set()  # 使用集合来存储链接，自动去除重复项

    while True:
        # 获取当前页面的所有论文链接
        current_papers = driver.find_elements(By.CSS_SELECTOR, "a[xplmathjax]")
        # 将新链接添加到集合中
        for paper in current_papers:
            paper_links.add(paper.get_attribute('href'))

        try:
            # 尝试点击下一页
            next_page = driver.find_element(By.CSS_SELECTOR, "li.next-btn button")
            time.sleep(random.uniform(1, 3))
            driver.execute_script("arguments[0].click();", next_page)
            time.sleep(random.uniform(2, 5))  # 等待新页面加载
        except NoSuchElementException:
            break  # 如果没有下一页了，退出循环

    # 返回一个列表，因为集合不保持顺序，如果需要可以在这里排序
    return list(paper_links)


def extract_metadata(driver):
    """ 使用JavaScript从网页中提取元数据，确保xplGlobal已经加载 """
    end_time = time.time() + 30  # 设置10秒超时
    while True:
        try:
            # 检查xplGlobal是否已定义并获取metadata
            result = driver.execute_script(
                "return typeof xplGlobal !== 'undefined' && xplGlobal.document && JSON.stringify(xplGlobal.document.metadata);"
            )
            if result:
                return json.loads(result)
        except JavascriptException:
            pass  # 如果JavaScript执行出错，忽略错误继续循环

        if time.time() > end_time:
            raise TimeoutException("Timed out waiting for xplGlobal to be available")

        time.sleep(random.uniform(1, 3))  # 暂停一下再次尝试

def scrape_paper_data(driver, paper_url):
    """ 访问论文页面并提取数据 """
    driver.get(paper_url)
    time.sleep(random.uniform(3, 8))  # 等待JavaScript加载
    metadata = extract_metadata(driver)

    data = {
        "Title": metadata.get("displayDocTitle", ""),
        "Abstract": metadata.get("abstract", ""),
        "Conference Location": metadata.get("confLoc", ""),
        "DOI": metadata.get("doi", "")
    }
    return data

import pandas as pd

def main():
    driver = setup_browser()
    conference_links = scrape_conference_links(driver)
    print(conference_links)
    all_paper_links = set()
    results = []  # Initialize an empty list to store the results
    
    for conference_link in conference_links:
        # Fetch all paper links for the current conference, already as a set
        paper_links = scrape_paper_links(driver, conference_link)
        # Add the current conference's paper links to the global set, removing duplicates
        all_paper_links.update(paper_links)
    print(all_paper_links)
    # Process each unique paper link
    for paper_link in all_paper_links:
        paper_data = scrape_paper_data(driver, paper_link)
        # Print the paper data (optional, for debugging or monitoring)
        print(paper_data)
        # Append the paper data to the results list
        results.append(paper_data)

    # Save the data to a CSV file
    df = pd.DataFrame(results)
    df.to_csv('papers.csv', index=False)
    driver.quit()

if __name__ == '__main__':
    main()
