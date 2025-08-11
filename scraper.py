from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException, ElementClickInterceptedException
from langdetect import detect
from langdetect import detect_langs
from db import save_job
from bs4 import BeautifulSoup
import re
import time
import random
import sqlite3

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
    
def find_title_and_link(job, driver, timeout: int = 10):
    """
    在单个职位卡片 job 内查找可点击的链接元素，并返回 (element, title, href)。
    通过多套选择器与显式等待，提升鲁棒性。
    """
    selectors = [
        "a.job-card-container__link",
        "a.job-card-list__title--link",
        "a[href*='/jobs/view/'][aria-label]",
        "a[aria-label]",
    ]
    for selector in selectors:
        try:
            WebDriverWait(driver, timeout).until(lambda d: job.find_element(By.CSS_SELECTOR, selector))
            el = job.find_element(By.CSS_SELECTOR, selector)
            href_value = el.get_attribute("href")
            title_value = el.get_attribute("aria-label") or el.text.strip()
            if href_value:
                return el, title_value, href_value
        except Exception:
            continue
    return None, None, None

def extract_job_id_from_url(url):
    """
    从LinkedIn职位详情URL中提取职位ID。
    """
    match = re.search(r'/jobs/view/(\d+)/', url)
    if match:
        return match.group(1)
    return None

def is_job_id_exists_in_db(job_id):
    """
    检查数据库中是否已存在该职位ID。
    """
    try:
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs WHERE job_id = ?", (job_id,))
        count = cursor.fetchone()[0]
        conn.close()
        return count > 0
    except Exception as e:
        print(f"检查职位ID {job_id} 是否存在数据库时出错: {e}")
        return False  # 出错时假设不存在，继续处理

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
    
    # 等待一下确保所有职位加载完成，增加随机性
    final_wait = random.uniform(3, 6)  # 从固定3秒改为3-6秒随机
    print(f"等待 {final_wait:.1f} 秒确保所有职位完全加载...")
    time.sleep(final_wait)
    
    job_list = wait.until(EC.presence_of_all_elements_located(
        (By.CSS_SELECTOR, ".scaffold-layout__list-item"))
    )

    # 新增：滚动职位列表到底部，确保所有职位都在可见范围内
    print("滚动到列表最后一个职位以激活渲染...")
    try:
        if job_list:
            driver.execute_script("arguments[0].scrollIntoView({block: 'end'});", job_list[-1])
            time.sleep(1)
            print("已滚动到最后一个职位")
    except Exception as e:
        print(f"滚动最后一个职位时出错（忽略继续）: {e}")

    jobs_data = []
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

            # 从链接中提取职位ID进行去重
            job_id = extract_job_id_from_url(href_value)
            if not job_id:
                print(f"第 {index+1} 个职位：无法从链接中提取职位ID，跳过")
                continue
                
            print(f"第 {index+1} 个职位：提取到职位ID: {job_id}")
            
            # 从数据库查询职位ID是否已存在
            if is_job_id_exists_in_db(job_id):
                print(f"第 {index+1} 个职位：职位ID {job_id} 在数据库中已存在，跳过")
                continue

            # 新增：如果title包含angular、fullstack、backend、lead、staff、Architect则标记为不符合并直接保存（不点开详情）
            if any(keyword in title.lower() for keyword in ['angular', 'fullstack', 'full-stack', 'full stack', 'backend', 'lead','head', 'staff', 'architect', 'react native']):
                print(f"第 {index+1} 个职位：标题包含angular/fullstack/backend/lead/staff/architect，将以不符合保存")
                job_data = {
                    "title": title,
                    "company": company,
                    "location": location,
                    "status": status,
                    "link": href_value,
                    "applicants": "",
                    "html": "",
                    "description": "",
                    "is_match": False,
                    "reject_reason": "title_blacklist"
                }
                if save_job(job_data):
                    jobs_data.append(job_data)
                    print(f"第 {index+1} 个职位：不符合（标题黑名单），已保存")
                # 友好延时
                if random.random() < 0.3:
                    think_time = random.uniform(1, 3)
                    print(f"第 {index+1} 个职位：思考时间 {think_time:.1f} 秒...")
                    time.sleep(think_time)
                delay_time = random.uniform(4, 8)
                print(f"第 {index+1} 个职位：等待 {delay_time:.1f} 秒后处理下一个...")
                time.sleep(delay_time)
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
            soup = BeautifulSoup(job_desc, "html.parser")
            job_desc_text = soup.get_text(separator=" ", strip=True)
            print(f"第 {index+1} 个职位：成功获取职位描述，长度: {len(job_desc_text)}")

            # 在过滤条件之前打印职位和详情长度
            print(f"第 {index+1} 个职位：{title} | {company} | {location}")
            print(f"第 {index+1} 个职位：详情长度: {len(job_desc) if job_desc else '无'}")

            # 语言过滤（改为计算is_match与reject_reason，不再直接continue）
            print(f"第 {index+1} 个职位：开始语言检测...")
            langs = detect_langs(job_desc)
            print(f"第 {index+1} 个职位：语言检测结果: {langs}")
            en_prob = 0
            for lang in langs:
                if lang.lang == "en":
                    en_prob = lang.prob
                    break
            print(f"第 {index+1} 个职位：英文概率: {en_prob}")

            is_match = True
            reject_reason = ""
            
            if en_prob < 0.85:
                is_match = False
                reject_reason = f"low_en_prob:{en_prob:.2f}"
            else:
                # 技术栈过滤：必须包含react、react.js、vue或vue.js
                print(f"第 {index+1} 个职位：开始技术栈检测...")
                required_tech = ['react', 'react.js', 'vue', 'vue.js']
                if not any(tech in job_desc_text.lower() for tech in required_tech):
                    is_match = False
                    reject_reason = "missing_required_tech"
                    print(f"第 {index+1} 个职位：职位描述不包含react/vue技术栈")
                else:
                    print(f"第 {index+1} 个职位：技术栈检测通过")
                    # 数字过滤，申请数量超过100的标记为不符合
                    print(f"第 {index+1} 个职位：开始申请人数过滤...")
                    nums = extract_numbers(apply_number)
                    print(f"第 {index+1} 个职位：申请人数解析结果: {nums}")
                    if nums and isinstance(nums[0], (int, float)) and nums[0] >= 100:
                        is_match = False
                        reject_reason = f"too_many_applicants:{nums[0]}"
                        print(f"第 {index+1} 个职位：申请人数 {nums[0]} >= 100")

            # 统一保存（无论是否符合）
            print(f"第 {index+1} 个职位：准备保存，is_match={is_match}, reject_reason='{reject_reason}'")
            job_data = {
                "title": title,
                "company": company,
                "location": location,
                "status": status,
                "link": href_value,
                "job_id": job_id,  # 新增：保存提取的职位ID
                "applicants": apply_number,
                "html": job_desc,
                "description": job_desc_text,
                "is_match": is_match,
                "reject_reason": reject_reason
            }
            
            if save_job(job_data):
                jobs_data.append(job_data)
                print(f"第 {index+1} 个职位：已保存 (is_match={is_match})")
            
            # 偶尔添加"思考时间"模拟人类行为
            if random.random() < 0.3:  # 30% 概率
                think_time = random.uniform(1, 3)
                print(f"第 {index+1} 个职位：思考时间 {think_time:.1f} 秒...")
                time.sleep(think_time)

            # 增加职位处理间隔，降低反爬虫风险
            delay_time = random.uniform(4, 8)  # 从 2-4秒 改为 4-8秒
            print(f"第 {index+1} 个职位：等待 {delay_time:.1f} 秒后处理下一个...")
            time.sleep(delay_time)

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
            
            # 增加翻页后等待时间，降低反爬虫风险
            wait_time = random.uniform(5, 10)  # 从 3秒 改为 5-10秒随机
            print(f"翻页完成，等待 {wait_time:.1f} 秒让页面加载...")
            time.sleep(wait_time)
            
            # 页面间添加随机休息时间，模拟人类浏览行为
            if page < max_pages - 1:  # 不是最后一页
                rest_time = random.uniform(15, 30)
                print(f"页面处理完成，休息 {rest_time:.1f} 秒...")
                time.sleep(rest_time)
                
        except ElementClickInterceptedException:
            print("下一页按钮被遮挡，尝试跳过本次翻页。")
            continue
        except NoSuchElementException:
            print("未找到下一页按钮，结束。"); break
    return all_jobs

jobs = scrape_all_pages(driver, max_pages=1, max_jobs_per_page=30)
print("共抓取到", len(jobs), "个职位")
