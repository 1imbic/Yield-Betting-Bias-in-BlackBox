import json
import os

def update_json_files(match_folder, new_matches):
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

    for match in new_matches:
        match_id = match["MatchID"]
        
        if not any(item["MatchID"] == match_id for item in existing_data["odds_probability"]["odds"]):
            existing_data["odds_probability"]["odds"].append({
                "MatchID": match_id,
                "TeamA_Odds": float(match["TeamA_Odds"]) if match["TeamA_Odds"] != "N/A" else "N/A",
                "TeamA_Probability": "N/A",
                "TeamA_PlatformRake": "N/A",
                "TeamB_Odds": float(match["TeamB_Odds"]) if match["TeamB_Odds"] != "N/A" else "N/A",
                "TeamB_Probability": "N/A",
                "TeamB_PlatformRake": "N/A"
            })

        if not any(item["MatchID"] == match_id for item in existing_data["littleblackbox_odds"]["littleblackbox"]):
            existing_data["littleblackbox_odds"]["littleblackbox"].append({
                "MatchID": match_id,
                "TeamA_LittleBlackBox_Odds": "N/A",
                "TeamA_LittleBlackBox_Rake": "N/A",
                "TeamB_LittleBlackBox_Odds": "N/A",
                "TeamB_LittleBlackBox_Rake": "N/A"
            })

        if not any(item["MatchID"] == match_id for item in existing_data["expected_profit_variance"]["profit"]):
            existing_data["expected_profit_variance"]["profit"].append({
                "MatchID": match_id,
                "TeamA_Expected_Profit": "N/A",
                "TeamA_ProfitVariance": "N/A",
                "TeamA_Kelly": "N/A",
                "TeamB_Expected_Profit": "N/A",
                "TeamB_ProfitVariance": "N/A",
                "TeamB_Kelly": "N/A"
            })

    try:
        for key, filepath in files.items():
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(existing_data[key], f, ensure_ascii=False, indent=2)
        print(f"已更新 JSON 文件到 {match_folder}，新增 {len(new_matches)} 个条目")
    except Exception as e:
        print(f"更新 JSON 文件时出错: {e}")

if __name__ == "__main__":
    sample_new_matches = [
        {
            "MatchID": "0001",
            "MatchName": "esl_pro_league_season_21",
            "MatchTime": "03-03 18:00",
            "TeamA": "Team X",
            "TeamB": "Team Y",
            "TeamA_Odds": "1.80",
            "TeamB_Odds": "2.00"
        }
    ]
    update_json_files("match_data/test_match", sample_new_matches)