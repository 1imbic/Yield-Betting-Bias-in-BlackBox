import json
import os

def read_json(json_file):
    if not os.path.exists(json_file):
        print(f"错误: 文件 {json_file} 不存在")
        return []
    
    teams = []
    try:
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            for match in data.get("matches", []):
                teams.append({
                    "MatchTime": match["MatchTime"],
                    "Team": match["TeamA"],
                    "Odds": match["TeamA_Odds"]
                })
                if match["TeamB"]:
                    teams.append({
                        "MatchTime": match["MatchTime"],
                        "Team": match["TeamB"],
                        "Odds": match["TeamB_Odds"]
                    })
            if not teams:
                print(f"警告: 文件 {json_file} 中没有有效数据")
            else:
                print(f"成功读取 {len(teams)} 条数据")
    except Exception as e:
        print(f"读取文件 {json_file} 时出错: {e}")
        return []
    
    return teams

def save_results(results, match_folder, match_name):
    files = {
        "odds_probability": os.path.join(match_folder, "odds_probability.json"),
        "littleblackbox_odds": os.path.join(match_folder, "littleblackbox_odds.json"),
        "expected_profit_variance": os.path.join(match_folder, "expected_profit_variance.json")
    }

    existing_data = {}
    for key, filepath in files.items():
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data[key] = json.load(f)
        else:
            existing_data[key] = {key: []}

    matches_file = os.path.join(match_folder, "matches_info.json")
    match_id_map = {}
    if os.path.exists(matches_file):
        with open(matches_file, 'r', encoding='utf-8') as f:
            matches_data = json.load(f)
            for match in matches_data["matches"]:
                match_id_map[(match["MatchTime"], match["TeamA"])] = match["MatchID"]
                if match["TeamB"]:
                    match_id_map[(match["MatchTime"], match["TeamB"])] = match["MatchID"]

    for i in range(0, len(results), 2):
        if i + 1 < len(results):
            team1 = results[i]
            team2 = results[i + 1]
            match_key1 = (team1["MatchTime"], team1["Team"])
            match_id = match_id_map.get(match_key1, f"{i//2:04d}")

            lbb_odds1 = team1["LittleBlackBox_Odds"]
            lbb_odds2 = team2["LittleBlackBox_Odds"]
            
            adj_odds1 = adjust_odds_for_calculation(lbb_odds1)
            adj_odds2 = adjust_odds_for_calculation(lbb_odds2)
            
            rake = "N/A"
            normalized_prob1 = team1["Probability"] if team1["Probability"] != "N/A" else "N/A"
            normalized_prob2 = team2["Probability"] if team2["Probability"] != "N/A" else "N/A"

            if adj_odds1 is not None and adj_odds2 is not None:
                total_odds1 = adj_odds1 + 1
                total_odds2 = adj_odds2 + 1
                prob1 = 1 / total_odds1
                prob2 = 1 / total_odds2
                total_prob = prob1 + prob2
                rake = max(0.0, total_prob - 1)
                rake = round(rake, 5)
                
                normalized_prob1 = prob1 / total_prob if total_prob > 0 else 0.5
                normalized_prob2 = prob2 / total_prob if total_prob > 0 else 0.5

            odds_entry = next((item for item in existing_data["odds_probability"]["odds"] if item["MatchID"] == match_id), None)
            if odds_entry:
                odds_entry.update({
                    "TeamA_Odds": float(team1["Odds"]),
                    "TeamA_Probability": normalized_prob1 if normalized_prob1 is not None else "N/A",
                    "TeamA_PlatformRake": rake,
                    "TeamB_Odds": float(team2["Odds"]),
                    "TeamB_Probability": normalized_prob2 if normalized_prob2 is not None else "N/A",
                    "TeamB_PlatformRake": rake
                })
            else:
                existing_data["odds_probability"]["odds"].append({
                    "MatchID": match_id,
                    "TeamA_Odds": float(team1["Odds"]),
                    "TeamA_Probability": normalized_prob1 if normalized_prob1 is not None else "N/A",
                    "TeamA_PlatformRake": rake,
                    "TeamB_Odds": float(team2["Odds"]),
                    "TeamB_Probability": normalized_prob2 if normalized_prob2 is not None else "N/A",
                    "TeamB_PlatformRake": rake
                })

            lbb_entry = next((item for item in existing_data["littleblackbox_odds"]["littleblackbox"] if item["MatchID"] == match_id), None)
            if lbb_entry:
                lbb_entry.update({
                    "TeamA_LittleBlackBox_Odds": float(lbb_odds1) if lbb_odds1 != "N/A" else "N/A",
                    "TeamA_LittleBlackBox_Rake": rake,
                    "TeamB_LittleBlackBox_Odds": float(lbb_odds2) if lbb_odds2 != "N/A" else "N/A",
                    "TeamB_LittleBlackBox_Rake": rake
                })
            else:
                existing_data["littleblackbox_odds"]["littleblackbox"].append({
                    "MatchID": match_id,
                    "TeamA_LittleBlackBox_Odds": float(lbb_odds1) if lbb_odds1 != "N/A" else "N/A",
                    "TeamA_LittleBlackBox_Rake": rake,
                    "TeamB_LittleBlackBox_Odds": float(lbb_odds2) if lbb_odds2 != "N/A" else "N/A",
                    "TeamB_LittleBlackBox_Rake": rake
                })

            profit_entry = next((item for item in existing_data["expected_profit_variance"]["profit"] if item["MatchID"] == match_id), None)
            if profit_entry:
                profit_entry.update({
                    "TeamA_Expected_Profit": team1["Expected_Profit"] if team1["Expected_Profit"] != "N/A" else "N/A",
                    "TeamA_ProfitVariance": team1["ProfitVariance"] if team1["ProfitVariance"] != "N/A" else "N/A",
                    "TeamA_Kelly": team1["Kelly"] if team1["Kelly"] != "N/A" else "N/A",
                    "TeamB_Expected_Profit": team2["Expected_Profit"] if team2["Expected_Profit"] != "N/A" else "N/A",
                    "TeamB_ProfitVariance": team2["ProfitVariance"] if team2["ProfitVariance"] != "N/A" else "N/A",
                    "TeamB_Kelly": team2["Kelly"] if team2["Kelly"] != "N/A" else "N/A"
                })
            else:
                existing_data["expected_profit_variance"]["profit"].append({
                    "MatchID": match_id,
                    "TeamA_Expected_Profit": team1["Expected_Profit"] if team1["Expected_Profit"] != "N/A" else "N/A",
                    "TeamA_ProfitVariance": team1["ProfitVariance"] if team1["ProfitVariance"] != "N/A" else "N/A",
                    "TeamA_Kelly": team1["Kelly"] if team1["Kelly"] != "N/A" else "N/A",
                    "TeamB_Expected_Profit": team2["Expected_Profit"] if team2["Expected_Profit"] != "N/A" else "N/A",
                    "TeamB_ProfitVariance": team2["ProfitVariance"] if team2["ProfitVariance"] != "N/A" else "N/A",
                    "TeamB_Kelly": team2["Kelly"] if team2["Kelly"] != "N/A" else "N/A"
                })

    try:
        with open(files["odds_probability"], 'w', encoding='utf-8') as f:
            json.dump(existing_data["odds_probability"], f, ensure_ascii=False, indent=2)
        with open(files["littleblackbox_odds"], 'w', encoding='utf-8') as f:
            json.dump(existing_data["littleblackbox_odds"], f, ensure_ascii=False, indent=2)
        with open(files["expected_profit_variance"], 'w', encoding='utf-8') as f:
            json.dump(existing_data["expected_profit_variance"], f, ensure_ascii=False, indent=2)
        print(f"结果已保存到 {match_folder}")
    except Exception as e:
        print(f"保存文件时出错: {e}")

def adjust_odds_for_calculation(odds):
    if odds == "25":
        return 25.0
    elif odds == "-":
        return 1.0417
    elif odds == "N/A":
        return None
    else:
        try:
            return float(odds)
        except ValueError:
            return None

def calculate_team_metrics(team, odds, lbb_odds, opponent_data, teams):
    prob, exp_profit, var, kelly, rake = "N/A", "N/A", "N/A", "N/A", "N/A"
    opponent = opponent_data["team"]
    opp_lbb_odds = opponent_data["lbb_odds"]

    odds1 = adjust_odds_for_calculation(odds)
    opponent_team = opponent_data["team"]
    opponent_entry = next((t for t in teams if t["Team"] == opponent_team), None)
    if not opponent_entry:
        odds2 = None
    else:
        odds2 = adjust_odds_for_calculation(opponent_entry["Odds"])
    
    if odds1 is not None and odds2 is not None:
        implied_prob1 = 1 / (odds1 + 1)
        implied_prob2 = 1 / (odds2 + 1)
        total_prob = implied_prob1 + implied_prob2
        
        prob = implied_prob1 / total_prob if total_prob > 0 else 0.5
        opp_prob = implied_prob2 / total_prob if total_prob > 0 else 0.5

        if lbb_odds is not None and opp_lbb_odds is not None:
            b1 = float(lbb_odds)
            b2 = float(opp_lbb_odds)
            
            total_implied_prob_lbb = (1 / (b1 + 1)) + (1 / (b2 + 1))
            rake = max(0, total_implied_prob_lbb - 1)
            rake = round(rake, 5) if rake is not None else "N/A"

            exp_profit = ((b1 + 1) * prob) - 1
            profit_if_win = b1
            loss_if_lose = -1
            var = prob * (profit_if_win - exp_profit)**2 + (1 - prob) * (loss_if_lose - exp_profit)**2

            kelly = ((prob * b1) - (1 - prob)) / b1 if prob != "N/A" and b1 != 0 else "N/A"
            if kelly < 0:
                kelly = 0

    return {
        "Team": team,
        "Odds": odds,
        "LittleBlackBox_Odds": lbb_odds if lbb_odds is not None else "N/A",
        "Probability": prob,
        "Expected_Profit": exp_profit,
        "ProfitVariance": var,
        "Kelly": kelly,
        "LittleBlackBox_Rake": rake
    }