import csv
import json
import os
import math

def read_csv(team_odds_file):
    """读取队伍赔率数据，从 Odds_Data 文件夹中查找"""
    odds_data_folder = "Odds_Data"
    if not os.path.exists(odds_data_folder):
        print(f"警告: Odds_Data 文件夹不存在")
        return []

    if not os.path.exists(team_odds_file):
        print(f"错误: 文件 {team_odds_file} 不存在")
        return []
    
    teams = []
    try:
        with open(team_odds_file, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                team = row["Team"].strip()
                odds = row["Odds"].strip()
                print(f"读取行: Team={team}, Odds={odds}")
                if team:
                    teams.append({"Team": team, "Odds": odds})
        print(f"成功读取 {len(teams)} 条数据")
    except Exception as e:
        print(f"读取文件 {team_odds_file} 时出错: {e}")
        return []
    
    return teams

def save_inputs(inputs, file_path='inputs.json'):
    """保存用户输入"""
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(inputs, f)

def load_inputs(file_path='inputs.json'):
    """加载之前的输入"""
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_results(results, output_file='ESL_Pro_League_S21_PlayIn_2025-02-11_odds.csv'):
    odds_data_folder = "Odds_Data"
    if not os.path.exists(odds_data_folder):
        os.makedirs(odds_data_folder)
    output_file = os.path.join(odds_data_folder, output_file)

    with open(output_file, mode='w', encoding='utf-8', newline='') as file:
        fieldnames = ["Team", "Odds", "LittleBlackBox_Odds", "Probability", 
                     "Expected_Profit", "ProfitVariance", "Kelly", "LittleBlackBox_Rake"]
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        
        # 处理每对队伍的小黑盒抽成
        for i in range(0, len(results), 2):
            if i + 1 < len(results):
                team1 = results[i]
                team2 = results[i + 1]
                lbb_odds1 = team1["LittleBlackBox_Odds"]
                lbb_odds2 = team2["LittleBlackBox_Odds"]
                
                # 调整赔率并计算抽成
                adj_odds1 = adjust_odds_for_calculation(lbb_odds1)
                adj_odds2 = adjust_odds_for_calculation(lbb_odds2)
                
                rake = "N/A"
                if adj_odds1 is not None and adj_odds2 is not None:
                    total_odds1 = adj_odds1 + 1  # 小黑盒赔率为净赔率，需加1
                    total_odds2 = adj_odds2 + 1
                    prob1 = 1 / total_odds1
                    prob2 = 1 / total_odds2
                    total_prob = prob1 + prob2
                    rake = max(0.0, total_prob - 1)
                    rake = round(rake, 5)  # 避免浮点精度问题
                
                formatted_rake = f"{rake:.3%}" if rake != "N/A" else "N/A"
                team1["LittleBlackBox_Rake"] = formatted_rake
                team2["LittleBlackBox_Rake"] = formatted_rake
        
        # 写入修正后的结果
        for result in results:
            writer.writerow({
                "Team": result["Team"],
                "Odds": result["Odds"],
                "LittleBlackBox_Odds": result["LittleBlackBox_Odds"],
                "Probability": f"{result['Probability']:.2f}" if result["Probability"] != "N/A" else "N/A",
                "Expected_Profit": f"{(result['Expected_Profit'] * 100):.2f}%" if result["Expected_Profit"] != "N/A" else "N/A",
                "ProfitVariance": f"{result['ProfitVariance']:.2f}" if result["ProfitVariance"] != "N/A" else "N/A",
                "Kelly": f"{result['Kelly']:.2f}" if result["Kelly"] != "N/A" else "N/A",
                "LittleBlackBox_Rake": result["LittleBlackBox_Rake"]
            })
            
def adjust_odds_for_calculation(odds):
    """调整特殊赔率值"""
    if odds == "25":
        return 25.0
    elif odds == "-":
        return 1.04
    else:
        try:
            return float(odds)
        except ValueError:
            return None

def calculate_little_black_box_rake(prob1, prob2):
    """计算小黑盒抽成"""
    if prob1 == "N/A" or prob2 == "N/A" or prob1 is None or prob2 is None:
        return "N/A"
    total_prob = prob1 + prob2
    if total_prob <= 1:
        return 0
    return total_prob - 1

def kelly_criterion(bet_odds, win_prob):
    """计算凯利比例"""
    if win_prob == "N/A" or bet_odds is None:
        return "N/A"
    b = bet_odds - 1
    p = win_prob
    if b <= 0 or p <= 0:
        return 0
    return max(0, (p * (b + 1) - 1) / b)

def calculate_team_metrics(team, odds, lbb_odds, opponent_data, teams):
    """计算单个队伍的指标，确保与对手概率一致"""
    prob, exp_profit, var, kelly, rake = "N/A", "N/A", "N/A", "N/A", "N/A"
    opponent = opponent_data["team"]
    opp_lbb_odds = opponent_data["lbb_odds"]

    odds1 = adjust_odds_for_calculation(odds)
    # 确保找到正确的对手队伍
    opponent_team = opponent_data["team"]
    # 查找对手的Odds
    opponent_entry = next((t for t in teams if t["Team"] == opponent_team), None)
    if not opponent_entry:
        odds2 = None
    else:
        odds2 = adjust_odds_for_calculation(opponent_entry["Odds"])
    if odds1 is not None and odds2 is not None:
        # Calculate base implied probabilities
        implied_prob1 = 1 / odds1
        implied_prob2 = 1 / odds2
        c = implied_prob1 + implied_prob2  # Total implied probability
        
        # Normalize probabilities to sum to 1 (before rake adjustment)
        prob = implied_prob1 / c
        opp_prob = implied_prob2 / c

        if lbb_odds is not None:
            actual_odds = float(lbb_odds) + 1
            opp_actual_odds = float(opp_lbb_odds) + 1 if opp_lbb_odds is not None else None

            if opp_actual_odds is not None:
                # Calculate rake from LittleBlackBox odds
                total_implied_prob = 1 / actual_odds + 1 / opp_actual_odds
                rake = max(0, total_implied_prob - 1)
                
                # No need to adjust probabilities with rake here; they should sum to 1 based on expected odds
                # If rake adjustment is desired, it should affect profit, not base probability
            else:
                rake = 0

            # Compute metrics for the current team
            exp_profit = (actual_odds * prob) - 1
            profit_if_win = (actual_odds - 1)
            loss_if_lose = -1
            var = prob * (profit_if_win - exp_profit)**2 + (1 - prob) * (loss_if_lose - exp_profit)**2
            kelly = kelly_criterion(actual_odds, prob)

    return {
        "Team": team,
        "Odds": odds,
        "LittleBlackBox_Odds": lbb_odds if lbb_odds is not None else "N/A",
        "Probability": prob,
        "Expected_Profit": exp_profit,
        "ProfitVariance": var,
        "Kelly": kelly,
        "LittleBlackBox_Rake": rake if rake != "N/A" else "N/A"
    }