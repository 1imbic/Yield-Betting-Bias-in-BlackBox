import json
import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import logging
from datetime import datetime, timedelta
import update_json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_match_name(url):
    parts = url.split('/')
    if 'tournament' in parts:
        index = parts.index('tournament')
        if index + 1 < len(parts):
            full_name = parts[index + 1].replace('-', '_')
            name_parts = full_name.split('_')
            while name_parts and len(name_parts[-1]) == 2 and name_parts[-1].isdigit():
                name_parts.pop()
            if name_parts and name_parts[-1] == "in" and len(name_parts) > 1 and name_parts[-2] == "play":
                name_parts = name_parts[:-2]
            while name_parts and not name_parts[-1]:
                name_parts.pop()
            return '_'.join(name_parts)
    return "unknown_match"

def parse_match_time(time_str, date_str):
    try:
        if date_str == "今天":
            date = datetime.now().strftime('%m-%d')
        elif date_str == "明天":
            date = (datetime.now() + timedelta(days=1)).strftime('%m-%d')
        elif "月" in date_str:
            month, day = date_str.split("月")
            date = f"{month.strip().zfill(2)}-{day.strip().zfill(2)}"
        else:
            return None
        full_time_str = f"{datetime.now().year}-{date} {time_str}"
        return datetime.strptime(full_time_str, '%Y-%m-%d %H:%M')
    except Exception as e:
        logging.warning(f"解析时间失败: {time_str} {date_str}, 错误: {e}")
        return None

def is_time_close(time1_str, time2_str, threshold_hours=3):
    if time1_str == time2_str:
        return True
    if time1_str == "未知时间" or time2_str == "未知时间":
        return False
    time1 = parse_match_time(*time1_str.split(' ', 1)) if ' ' in time1_str else None
    time2 = parse_match_time(*time2_str.split(' ', 1)) if ' ' in time2_str else None
    if time1 and time2:
        time_diff = abs((time1 - time2).total_seconds() / 3600)
        return time_diff <= threshold_hours
    return False

def fetch_team_odds(url="https://cyber-ggbet.com/cn/esports/matches"):
    match_name = extract_match_name(url)
    match_folder = os.path.join("match_data", match_name)
    if not os.path.exists(match_folder):
        os.makedirs(match_folder)
    
    json_filename = os.path.join(match_folder, "matches_info.json")
    existing_data = {"matches": []}
    if os.path.exists(json_filename):
        with open(json_filename, 'r', encoding='utf-8') as file:
            existing_data = json.load(file)

    options = Options()
    options.headless = True
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--ignore-ssl-errors")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    try:
        driver = webdriver.Chrome(options=options)
    except Exception as e:
        logging.error(f"初始化 WebDriver 时出错: {e}")
        return -1, None

    max_attempts = 3
    attempt = 0
    success = False
    filtered_teams = []
    time_elements = []

    while attempt < max_attempts and not success:
        attempt += 1
        try:
            logging.info(f"尝试第 {attempt} 次加载页面: {url}")
            driver.get(url)
            
            WebDriverWait(driver, 60).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[data-test^="odd-button"]'))
            )
            
            title_elements = driver.find_elements(By.CSS_SELECTOR, '[data-test="odd-button__title"]')
            result_elements = driver.find_elements(By.CSS_SELECTOR, '[data-test="odd-button__result"]')
            time_elements = driver.find_elements(By.CSS_SELECTOR, 'div.text-sm.text-grey-500, div.text-sm.text-grey-500.opacity-100')

            logging.info(f"第 {attempt} 次提取到的队伍数量: {len(title_elements)}, 赔率数量: {len(result_elements)}, 时间数量: {len(time_elements)}")

            filtered_teams = []
            min_length = min(len(title_elements), len(result_elements))
            for i in range(0, min_length, 2):
                try:
                    team1_name = title_elements[i].text.strip()
                    odds1_text = result_elements[i].text.strip()
                    team2_name = title_elements[i + 1].text.strip() if i + 1 < min_length else ""
                    odds2_text = result_elements[i + 1].text.strip() if i + 1 < min_length else ""

                    if odds1_text == '-':
                        odds1_text = '1.0417'
                    if odds2_text == '-':
                        odds2_text = '1.0417'

                    if team1_name and not team1_name.startswith(('+', '-')):
                        filtered_teams.append((team1_name, odds1_text))
                    if team2_name and not team2_name.startswith(('+', '-')) and i + 1 < min_length:
                        filtered_teams.append((team2_name, odds2_text))
                except Exception as e:
                    logging.error(f"处理队伍对 {i} 时出错: {e}")
                    continue

            logging.info(f"第 {attempt} 次过滤后的有效队伍数量: {len(filtered_teams)}")

            expected_time_elements = len(filtered_teams) // 2
            bo_detected = any(
                len(driver.find_elements(By.XPATH, f"//div[contains(text(), 'BO')]")) > 0
                for _ in range(len(time_elements))
            )
            if len(time_elements) >= expected_time_elements or (len(time_elements) > 0 and bo_detected):
                success = True
            else:
                logging.warning(f"第 {attempt} 次爬取结果不完整，时间元素数量: {len(time_elements)}，预期: {expected_time_elements}")
                if attempt < max_attempts:
                    logging.info("等待 5 秒后重试...")
                    driver.refresh()
                    time.sleep(5)
        except TimeoutException:
            logging.error(f"第 {attempt} 次页面加载超时，未找到预期元素")
            if attempt == max_attempts:
                return -1, None
        except Exception as e:
            logging.error(f"第 {attempt} 次加载页面或提取数据时出错: {e}")
            if attempt == max_attempts:
                return -1, None

    if not success:
        logging.error(f"经过 {max_attempts} 次尝试仍未成功爬取完整数据")
        driver.quit()
        return -1, None

    matches_dict = {}
    match_index = max([int(m["MatchID"]) for m in existing_data["matches"]] + [0]) if existing_data["matches"] else 0
    for match in existing_data["matches"]:
        key = (match["MatchName"], match["MatchTime"], match["TeamA"], match["TeamB"])
        matches_dict[key] = match

    new_entries = []
    for i in range(0, len(filtered_teams), 2):
        try:
            team1_name, odds1_text = filtered_teams[i]
            team2_name = (filtered_teams[i + 1][0] if i + 1 < len(filtered_teams) else "")
            odds2_text = (filtered_teams[i + 1][1] if i + 1 < len(filtered_teams) else "")

            match_idx = i // 2
            if match_idx < len(time_elements):
                time_div = time_elements[match_idx]
                time_parts = time_div.find_elements(By.TAG_NAME, 'div')
                if len(time_parts) >= 2:
                    part1 = time_parts[0].text.strip()
                    part2 = time_parts[1].text.strip()

                    if part1.startswith("BO"):
                        match_time = "未知时间"
                        special_info = f"{part1} {part2}"
                        continue
                    else:
                        time_str = part1
                        date_str = part2
                        if date_str == "今天":
                            match_time = datetime.now().strftime('%m-%d') + ' ' + time_str
                        elif date_str == "明天":
                            tomorrow = datetime.now() + timedelta(days=1)
                            match_time = tomorrow.strftime('%m-%d') + ' ' + time_str
                        elif "月" in date_str:
                            month, day = date_str.split("月")
                            month = month.strip()
                            day = day.strip()
                            match_time = f"{month.zfill(2)}-{day.zfill(2)} {time_str}"
                        else:
                            match_time = "未知时间"
                        special_info = None
                else:
                    match_time = "未知时间"
                    special_info = None
            else:
                match_time = "未知时间"
                special_info = None

            if team1_name:
                match_key = (match_name, match_time, team1_name, team2_name)
                existing_match = matches_dict.get(match_key)

                if existing_match:
                    existing_match["TeamA_Odds"] = odds1_text
                    existing_match["TeamB_Odds"] = odds2_text
                    existing_match["MatchTime"] = match_time
                    if special_info:
                        existing_match["SpecialInfo"] = special_info
                    elif "SpecialInfo" in existing_match:
                        del existing_match["SpecialInfo"]
                    matches_dict[match_key] = existing_match
                else:
                    match_index += 1
                    match_id = f"{match_index:04d}"
                    match_data = {
                        "MatchID": match_id,
                        "MatchName": match_name,
                        "MatchTime": match_time,
                        "TeamA": team1_name,
                        "TeamB": team2_name,
                        "TeamA_Odds": odds1_text,
                        "TeamB_Odds": odds2_text
                    }
                    if special_info:
                        match_data["SpecialInfo"] = special_info
                    matches_dict[match_key] = match_data
                    new_entries.append(match_data)
        except Exception as e:
            logging.error(f"处理比赛 {i} 时出错: {e}")
            continue

    new_matches_info = {"matches": list(matches_dict.values())}

    if new_matches_info["matches"]:
        try:
            with open(json_filename, 'w', encoding='utf-8') as file:
                json.dump(new_matches_info, file, ensure_ascii=False, indent=2)
            logging.info(f"数据已成功保存到 {json_filename}")
            
            if new_entries:
                update_json.update_json_files(match_folder, new_entries)
            
            driver.quit()
            return 0, json_filename
        except Exception as e:
            logging.error(f"保存 JSON 文件时出错: {e}")
            driver.quit()
            return -1, None
    else:
        logging.warning("没有有效数据可保存")
        driver.quit()
        return -1, None

if __name__ == "__main__":
    fetch_team_odds("https://cyber-ggbet.com/cn/esports/tournament/esl-pro-league-season-21-play-in-11-02")