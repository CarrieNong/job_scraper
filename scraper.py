from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from langdetect import detect
from langdetect import detect_langs
from db import save_job
import re
import time
import random

chrome_options = Options()
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.linkedin.com/jobs/search/?currentJobId=3733036815&f_TPR=r86400&geoId=101282230&keywords=frontend%20react%20vue&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true")


def extract_numbers(text):
    """
    从文本中提取数字（支持千分位逗号和小数），返回 int/float 的列表。
    """
    matches = re.findall(r'\d[\d,]*\.?\d*', text)
    numbers = []
    for m in matches:
        cleaned = m.replace(',', '')  # 去掉千分位逗号
        if '.' in cleaned:
            try:
                numbers.append(float(cleaned))
            except ValueError:
                continue
        else:
            try:
                numbers.append(int(cleaned))
            except ValueError:
                continue
    return numbers

def get_status(job):
    try:
        return job.find_element(By.CSS_SELECTOR, ".job-card-container__footer-job-state").text.strip()
    except NoSuchElementException:
        return 'new'
    
def scrape_jobs(driver, max_jobs=15):
    wait = WebDriverWait(driver, 15)
    job_list = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, ".scaffold-layout__list-item"))
    )

    jobs_data = []

    for index in range(min(max_jobs, len(job_list))):
        try:
            # 点击前先取完所有列表数据
            job_list = driver.find_elements(By.CSS_SELECTOR, ".scaffold-layout__list-item")
            job = job_list[index]

            title = job.find_element(By.CSS_SELECTOR, ".job-card-list__title--link span strong").text.strip()
            company = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle span").text.strip()
            location = job.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-wrapper li span").text.strip()
            status = get_status(job)
            href_value = job.find_element(By.CSS_SELECTOR, ".job-card-container__link").get_attribute("href")

            # 点击职位卡
            job.click()

            # 等详情面板出现
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__tertiary-description-container")
            ))

            # 获取申请人数量
            span_elem = driver.find_element(
                By.CSS_SELECTOR, 
                ".job-details-jobs-unified-top-card__tertiary-description-container > span"
            )
            apply_number = span_elem.find_element(By.XPATH, "./*[last()-1]").text.strip()

            # 获取职位描述
            job_desc = driver.find_element(
                By.CSS_SELECTOR, 
                ".jobs-box__html-content"
            ).get_attribute("innerHTML")

            # 语言过滤
            langs = detect_langs(job_desc)
            # langs 是类似 [en:0.85, de:0.10] 这样的列表
            en_prob = 0
            for lang in langs:
                if lang.lang == "en":
                    en_prob = lang.prob
                    break
            if en_prob < 0.85:
                continue  # 不满足阈值，跳过

            # 数字过滤
            nums = extract_numbers(apply_number)
            if nums and isinstance(nums[0], (int, float)) and nums[0] >= 100:
                continue

            job_data = {
                "title": title,
                "company": company,
                "location": location,
                "status": status,
                "link": href_value,
                "applicants": apply_number,
                "description": job_desc
            }
            jobs_data.append(job_data)
            save_job(job_data)  # 保存数据字典，而不是 Selenium 元素

            # print(f"✅ {index+1}. {title} | {company} | {location} | 状态: {status} | 申请数量: {apply_number}")

            time.sleep(random.uniform(2, 4))  # 随机延迟

        except TimeoutException:
            print(f"⚠️ 第 {index+1} 个职位详情加载超时")
        except Exception as e:
            print(f"✅ {index+1}. {title} | {company} | {location} | 状态: {status}")
            print(f"申请数量（nums）: {nums}")
            print(f"详情长度: {len(job_desc) if job_desc else '无'}")
            print(f"链接长度: {len(href_value) if href_value else '无'}")
            print(f"❌ 处理第 {index+1} 个职位出错:", e)

    return jobs_data

jobs = scrape_jobs(driver, max_jobs=6)
print("共抓取到", len(jobs), "个职位")
