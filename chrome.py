import asyncio
from bs4 import BeautifulSoup
from pyppeteer import launch

async def crawl_cu_notice_with_pyppeteer(sub_notice_url, search_text):
    browser = await launch(headless=True, 
                           args=[
                                '--disable-dev-shm-usage',
                                '--no-sandbox',
                                '--disable-setuid-sandbox',
                                '--disable-extensions',
                                '--disable-gpu'
                            ], 
                           dumpio=True)
    # browser = await launch(
    #     headless=True,
    #     executablePath='/home/ubuntu/.local/share/pyppeteer/local-chromium/1181205/chrome-linux/chrome',
    #     args=[
    #         '--disable-dev-shm-usage',
    #         '--no-sandbox',
    #         '--disable-setuid-sandbox',
    #         '--disable-extensions',
    #         '--disable-gpu'
    #     ],
    #     dumpio=True
    # )
    page = await browser.newPage()
    await page.goto(sub_notice_url)

    # search_order 인풋 요소에 값 설정
    await page.evaluate(f'document.querySelector("input[name=\'search_order\']").value = "{search_text}"')

    # #searchBtn > fieldset > button 경로의 버튼 클릭
    await page.click('#searchBtn > fieldset > button')

    # 페이지가 완전히 로드될 때까지 대기
    await page.waitForNavigation({'waitUntil': 'networkidle2'})

    # 특정 텍스트를 가진 <a> 태그 찾기
    content = await page.content()
    await browser.close()
    soup = BeautifulSoup(content, 'html.parser')
    cleaned_search_text = search_text.replace(" ", "")
    a_tag = soup.find('a', string=lambda text: text and cleaned_search_text in text.replace(" ", ""))

    if a_tag:
        href_url = a_tag.get('href')
        return href_url
    else:
        return None

sub_notice_url = "https://www.cu.ac.kr/plaza/notice/notice"
title = "2025학년도 1학기 STELLA 안내"

# asyncio.run()을 사용하여 async 함수 실행
next_url = asyncio.run(crawl_cu_notice_with_pyppeteer(sub_notice_url, title))
print(next_url)

# loop = asyncio.get_event_loop()
# try:
#     next_url = loop.run_until_complete(crawl_cu_notice_with_pyppeteer(sub_notice_url, title))
#     print(next_url)
# finally:
#     loop.close()