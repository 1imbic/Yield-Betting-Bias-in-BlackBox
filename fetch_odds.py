# fetch_odds.py
import csv
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def extract_match_name(url):
    """从 URL 提取比赛名称"""
    if "esl-pro-league-season-21-play-in-11-02" in url:
        return "ESL_Pro_League_S21_PlayIn_2025-02-11"
    # 可以根据其他 URL 模式添加更多规则
    return "default_match_" + url.split("/")[-1].replace("-", "_")

def fetch_team_odds(url="https://cyber-ggbet.com/cn/esports/tournament/esl-pro-league-season-21-play-in-11-02"):
    """从指定URL获取队伍赔率数据并保存到CSV文件"""
    # 创建 Odds_Data 文件夹（如果不存在）
    odds_data_folder = "Odds_Data"
    if not os.path.exists(odds_data_folder):
        os.makedirs(odds_data_folder)

    # 提取比赛名称作为文件名
    match_name = extract_match_name(url)
    csv_filename = os.path.join(odds_data_folder, f"{match_name}_odds.csv")

    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        print(f"初始化 WebDriver 时出错: {e}")
        return -1, None  # 返回错误码和 None 文件名

    driver.get(url)
    team_odds_data = []

    try:
        WebDriverWait(driver, 20).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test^="odd-button"]'))
        )
        title_elements = driver.find_elements(By.CSS_SELECTOR, '[data-test="odd-button__title"]')
        result_elements = driver.find_elements(By.CSS_SELECTOR, '[data-test="odd-button__result"]')

        min_length = min(len(title_elements), len(result_elements))
        for i in range(min_length):
            try:
                team_name = title_elements[i].text.strip() or "未知队伍"
                odds_text = result_elements[i].text.strip() or "-"
                if not (team_name.startswith(('+', '-')) and any(char.isdigit() for char in team_name)):
                    if not (team_name == "未知队伍" and odds_text == "-"):
                        if odds_text:
                            team_odds_data.append({"Team": team_name, "Odds": odds_text})
            except Exception as e:
                print(f"处理元素对 {i} 时出错: {e}")
                continue

    except Exception as e:
        print(f"加载页面或等待元素时出错: {e}")
    finally:
        driver.quit()

    if team_odds_data:
        try:
            with open(csv_filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["Team", "Odds"])
                writer.writeheader()
                writer.writerows(team_odds_data)
            print(f"数据已成功保存到 {csv_filename}")
            return 0, csv_filename  # 返回成功码和文件名
        except Exception as e:
            print(f"保存 CSV 文件时出错: {e}")
            return -1, None
    else:
        print("没有有效数据可保存，返回错误值: -1")
        return -1, None

if __name__ == "__main__":
    fetch_team_odds()