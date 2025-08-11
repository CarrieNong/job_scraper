from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from langdetect import detect
from langdetect import detect_langs
from db import save_job
import re
import time
import random

chrome_options = Options()
# chrome_options.add_argument('--user-data-dir=/tmp/chrome_selenium_profile')
# /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --remote-debugging-port=9222 --user-data-dir="/tmp/chrome_selenium"
chrome_options.add_experimental_option("debuggerAddress", "127.0.0.1:9222")
driver = webdriver.Chrome(options=chrome_options)

driver.get("https://www.linkedin.com/jobs/search/?f_TPR=r86400&geoId=101282230&keywords=frontend%20react%20vue&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true")

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
    
    # 先滚动页面加载更多职位
    print("开始滚动页面加载更多职位...")
    last_height = driver.execute_script("return document.body.scrollHeight")
    scroll_count = 0
    while scroll_count < 5:  # 最多滚动5次，避免无限循环
        # 滚动到底部
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)  # 等待加载
        
        # 计算新的页面高度
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("页面高度未变化，停止滚动")
            break
        last_height = new_height
        scroll_count += 1
        print(f"第 {scroll_count} 次滚动：页面高度从 {last_height} 增加到 {new_height}")
    
    print(f"页面滚动完成，共滚动 {scroll_count} 次")
    
    # 等待一下确保所有职位加载完成
    time.sleep(3)
    
    job_list = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, ".scaffold-layout__list-item"))
    )

    # 新增：滚动职位列表到底部，确保所有职位都在可见范围内
    print("开始滚动职位列表到底部...")
    try:
        # 找到职位列表容器
        job_list_container = driver.find_element(By.CSS_SELECTOR, ".jobs-search__results-list")
        # 滚动到列表底部
        driver.execute_script("arguments[0].scrollTop = arguments[0].scrollHeight", job_list_container)
        time.sleep(2)  # 等待滚动完成
        print("职位列表滚动完成")
    except Exception as e:
        print(f"滚动职位列表时出错: {e}")

    jobs_data = []
    processed_links = set()  # 用于去重的链接集合
    print(f"找到 {len(job_list)} 个职位卡片，准备处理前 {min(max_jobs, len(job_list))} 个")

    for index in range(min(max_jobs, len(job_list))):
        print(f"\n=== 开始处理第 {index+1} 个职位 ===")
        try:
            # 每次都重新获取职位列表，避免 stale element
            print(f"第 {index+1} 个职位：重新获取职位列表...")
            current_job_list = driver.find_elements(By.CSS_SELECTOR, ".scaffold-layout__list-item")
            if index >= len(current_job_list):
                print(f"第 {index+1} 个职位：索引超出范围，跳过")
                continue
                
            job = current_job_list[index]
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", job)
            # 等待 job 内部的 link 出现（虚拟列表渲染完成）
            wait.until(EC.presence_of_element_located((
                By.CSS_SELECTOR,
                ".job-card-container__link"
            )))
                
            print(f"第 {index+1} 个职位：成功获取职位元素")


            print(f"第 {index+1} 个职位：开始获取基本信息...")
            title = job.find_element(By.CSS_SELECTOR, ".job-card-container__link").get_attribute("aria-label")
            print(f"第 {index+1} 个职位：成功获取标题: {title}")
            
            company = job.find_element(By.CSS_SELECTOR, ".artdeco-entity-lockup__subtitle span").text.strip()
            print(f"第 {index+1} 个职位：成功获取公司: {company}")
            
            location = job.find_element(By.CSS_SELECTOR, ".job-card-container__metadata-wrapper li span").text.strip()
            print(f"第 {index+1} 个职位：成功获取地点: {location}")
            
            status = get_status(job)
            print(f"第 {index+1} 个职位：成功获取状态: {status}")
            
            href_value = job.find_element(By.CSS_SELECTOR, ".job-card-container__link").get_attribute("href")
            print(f"第 {index+1} 个职位：成功获取链接: {href_value[:50]}...")

            # 内存中去重检查
            if href_value in processed_links:
                print(f"第 {index+1} 个职位：链接已存在，跳过")
                continue

            # 点击职位卡
            print(f"第 {index+1} 个职位：开始点击职位卡片...")
            job.click()
            print(f"第 {index+1} 个职位：成功点击职位卡片")

            # 等详情面板出现
            print(f"第 {index+1} 个职位：等待详情面板加载...")
            wait.until(EC.presence_of_element_located(
                (By.CSS_SELECTOR, ".job-details-jobs-unified-top-card__tertiary-description-container")
            ))
            print(f"第 {index+1} 个职位：详情面板加载完成")

            # 获取申请人数量
            print(f"第 {index+1} 个职位：开始获取申请人数...")
            span_elem = driver.find_element(
                By.CSS_SELECTOR, 
                ".job-details-jobs-unified-top-card__tertiary-description-container > span"
            )
            apply_number = span_elem.find_element(By.XPATH, "./*[last()-1]").text.strip()
            print(f"第 {index+1} 个职位：成功获取申请人数: {apply_number}")

            # 获取职位描述
            print(f"第 {index+1} 个职位：开始获取职位描述...")
            job_desc = driver.find_element(
                By.CSS_SELECTOR, 
                ".jobs-box__html-content"
            ).get_attribute("innerHTML")
            print(f"第 {index+1} 个职位：成功获取职位描述，长度: {len(job_desc)}")

            # 在过滤条件之前打印职位和详情长度
            print(f"第 {index+1} 个职位：{title} | {company} | {location}")
            print(f"第 {index+1} 个职位：详情长度: {len(job_desc) if job_desc else '无'}")

            # 语言过滤
            print(f"第 {index+1} 个职位：开始语言检测...")
            langs = detect_langs(job_desc)
            print(f"第 {index+1} 个职位：语言检测结果: {langs}")
            # langs 是类似 [en:0.85, de:0.10] 这样的列表
            en_prob = 0
            for lang in langs:
                if lang.lang == "en":
                    en_prob = lang.prob
                    break
            print(f"第 {index+1} 个职位：英文概率: {en_prob}")
            if en_prob < 0.85:
                print(f"第 {index+1} 个职位：英文概率 {en_prob} < 0.85，跳过")
                continue  # 不满足阈值，跳过

            # 新增：如果title包含angular、fullstack、backend则跳过
            if any(keyword in title.lower() for keyword in ['angular', 'fullstack', 'backend']):
                print(f"第 {index+1} 个职位：标题包含angular/fullstack/backend，跳过")
                continue

            # 数字过滤，申请数量超过100的跳过
            print(f"第 {index+1} 个职位：开始申请人数过滤...")
            nums = extract_numbers(apply_number)
            print(f"第 {index+1} 个职位：申请人数解析结果: {nums}")
            if nums and isinstance(nums[0], (int, float)) and nums[0] >= 100:
                print(f"第 {index+1} 个职位：申请人数 {nums[0]} >= 100，跳过")
                continue

            print(f"第 {index+1} 个职位：通过所有过滤条件，准备保存...")
            job_data = {
                "title": title,
                "company": company,
                "location": location,
                "status": status,
                "link": href_value,
                "applicants": apply_number,
                "description": job_desc
            }
            
            # 保存到数据库并更新内存中的已处理链接集合
            if save_job(job_data):
                jobs_data.append(job_data)
                processed_links.add(href_value)  # 添加到已处理集合
                print(f"第 {index+1} 个职位：成功保存到数据库")
            else:
                print(f"第 {index+1} 个职位：数据库中已存在，跳过")

            time.sleep(random.uniform(2, 4))  # 随机延迟

        except StaleElementReferenceException:
            print(f"第{index+1}个职位遇到 stale element，已跳过。")
            continue
        except TimeoutException:
            print(f"⚠️ 第 {index+1} 个职位详情加载超时")
        except Exception as e:
            print(f"❌ 第 {index+1} 个职位处理出错: {e}")
            print(f"错误类型: {type(e).__name__}")
            continue

    print(f"\n=== 职位处理完成，共成功处理 {len(jobs_data)} 个职位 ===")
    return jobs_data

def scrape_all_pages(driver, max_pages=10, max_jobs_per_page=30):
    """
    自动翻页抓取职位数据，最多抓取 max_pages 页。
    每页最多抓取 max_jobs_per_page 条。
    """
    all_jobs = []
    for page in range(max_pages):
        print(f"正在抓取第 {page+1} 页...")
        jobs = scrape_jobs(driver, max_jobs=max_jobs_per_page)
        all_jobs.extend(jobs)
        try:
            next_btn = driver.find_element(By.CSS_SELECTOR, 'button[aria-label="View next page"]')
            driver.execute_script("arguments[0].scrollIntoView();", next_btn)
            time.sleep(0.5)
            next_btn.click()
            time.sleep(3)  # 等待页面加载
        except ElementClickInterceptedException:
            print("下一页按钮被遮挡，尝试跳过本次翻页。")
            continue
        except NoSuchElementException:
            print("未找到下一页按钮，结束。"); break
    return all_jobs

jobs = scrape_all_pages(driver, max_pages=1, max_jobs_per_page=30)
print("共抓取到", len(jobs), "个职位")
