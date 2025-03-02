import tkinter as tk
from tkinter import ttk, font, messagebox
import data_processor
import json
import os

class BettingApp:
    def __init__(self, root, teams, match_name):
        self.root = root
        self.root.title("小黑盒赔率分析")
        self.teams = teams
        self.match_name = match_name
        self.table_font = font.Font(family="Arial", size=12)
        self.input_font = font.Font(family="Arial", size=16)
        root.option_add("*Font", self.table_font)

        main_frame = tk.Frame(root)
        main_frame.pack(pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(main_frame, columns=("MatchTime", "Team", "Odds", "LittleBlackBox_Odds", 
                                                      "Probability", "Expected_Profit", "ProfitVariance", 
                                                      "Kelly", "LittleBlackBox_Rake"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100 if col not in ["MatchTime", "Team"] else 150)
        
        self.tree.pack(side=tk.TOP, pady=10, fill="both", expand=True)

        match_folder = os.path.join("match_data", match_name)
        self.matches_file = os.path.join(match_folder, "matches_info.json")
        self.result_files = {
            "odds_probability": os.path.join(match_folder, "odds_probability.json"),
            "littleblackbox_odds": os.path.join(match_folder, "littleblackbox_odds.json"),
            "expected_profit_variance": os.path.join(match_folder, "expected_profit_variance.json")
        }

        self.results = {}
        self.load_existing_data()

        self.tree_items = {}
        self.special_info_entries = {}
        self.entries = {}

        self.odds_changed = self.check_odds_changed()

        with open(self.matches_file, 'r', encoding='utf-8') as f:
            matches_data = json.load(f)

        for i in range(0, len(teams), 2):
            match_time = teams[i]["MatchTime"]
            team1 = teams[i]
            team2 = teams[i + 1] if i + 1 < len(teams) else None
            
            team1_key = (match_time, team1["Team"])
            team1_values = self.results.get(team1_key, {
                "MatchTime": match_time,
                "Team": team1["Team"],
                "Odds": float(team1["Odds"]) if team1["Odds"] != "N/A" else "N/A",
                "LittleBlackBox_Odds": "N/A",
                "Probability": "N/A",
                "Expected_Profit": "N/A",
                "ProfitVariance": "N/A",
                "Kelly": "N/A",
                "LittleBlackBox_Rake": "N/A"
            })
            
            item1 = self.tree.insert("", "end", values=(
                team1_values["MatchTime"],
                team1_values["Team"],
                f"{team1_values['Odds']:.2f}" if isinstance(team1_values['Odds'], (int, float)) else "",
                f"{team1_values['LittleBlackBox_Odds']:.2f}" if isinstance(team1_values['LittleBlackBox_Odds'], (int, float)) else "",
                f"{team1_values['Probability']:.2f}" if isinstance(team1_values['Probability'], (int, float)) else "",
                f"{team1_values['Expected_Profit'] * 100:.2f}%" if isinstance(team1_values['Expected_Profit'], (int, float)) else "",
                f"{team1_values['ProfitVariance']:.2f}" if isinstance(team1_values['ProfitVariance'], (int, float)) else "",
                f"{team1_values['Kelly']:.9f}" if isinstance(team1_values['Kelly'], (int, float)) else "",
                f"{team1_values['LittleBlackBox_Rake']:.3%}" if isinstance(team1_values['LittleBlackBox_Rake'], (int, float)) else ""
            ))
            self.tree_items[team1["Team"]] = item1
            
            if team2:
                team2_key = (match_time, team2["Team"])
                team2_values = self.results.get(team2_key, {
                    "MatchTime": match_time,
                    "Team": team2["Team"],
                    "Odds": float(team2["Odds"]) if team2["Odds"] != "N/A" else "N/A",
                    "LittleBlackBox_Odds": "N/A",
                    "Probability": "N/A",
                    "Expected_Profit": "N/A",
                    "ProfitVariance": "N/A",
                    "Kelly": "N/A",
                    "LittleBlackBox_Rake": "N/A"
                })
                item2 = self.tree.insert("", "end", values=(
                    team2_values["MatchTime"],
                    team2_values["Team"],
                    f"{team2_values['Odds']:.2f}" if isinstance(team2_values['Odds'], (int, float)) else "",
                    f"{team2_values['LittleBlackBox_Odds']:.2f}" if isinstance(team2_values['LittleBlackBox_Odds'], (int, float)) else "",
                    f"{team2_values['Probability']:.2f}" if isinstance(team2_values['Probability'], (int, float)) else "",
                    f"{team2_values['Expected_Profit'] * 100:.2f}%" if isinstance(team2_values['Expected_Profit'], (int, float)) else "",
                    f"{team2_values['ProfitVariance']:.2f}" if isinstance(team2_values['ProfitVariance'], (int, float)) else "",
                    f"{team2_values['Kelly']:.9f}" if isinstance(team2_values['Kelly'], (int, float)) else "",
                    f"{team2_values['LittleBlackBox_Rake']:.3%}" if isinstance(team2_values['LittleBlackBox_Rake'], (int, float)) else ""
                ))
                self.tree_items[team2["Team"]] = item2
            if i + 2 < len(teams):
                self.tree.insert("", "end", values=("", "", "", "", "", "", "", "", ""))

        input_frame = tk.Frame(main_frame)
        input_frame.pack(side=tk.BOTTOM, pady=10, fill="both", expand=True)
        self.notebook = ttk.Notebook(input_frame)
        self.notebook.pack(fill="both", expand=True)

        for i in range(0, len(teams), 2):
            page = tk.Frame(self.notebook)
            self.notebook.add(page, text=f"第 {i//2 + 1} 组")
            match = matches_data["matches"][i // 2] if i // 2 < len(matches_data["matches"]) else {}

            if "SpecialInfo" in match and match["SpecialInfo"]:
                special_frame = tk.Frame(page)
                special_frame.pack(pady=5)
                tk.Label(special_frame, text=f"特殊信息 ({match['SpecialInfo']}):", font=self.input_font).pack(side=tk.LEFT)
                special_entry = tk.Entry(special_frame, width=20, font=self.input_font)
                special_entry.pack(side=tk.LEFT)
                special_entry.bind("<Return>", lambda event, m=match: self.update_special_info(m, special_entry))
                self.special_info_entries[match["MatchID"]] = special_entry

            for j in range(2):
                if i + j < len(teams):
                    team = teams[i + j]["Team"]
                    odds = teams[i + j]["Odds"]
                    frame = tk.Frame(page)
                    frame.pack(pady=5)
                    tk.Label(frame, text=f"{team} (赔率: {odds})", width=30, anchor="w", font=self.input_font).pack(side=tk.LEFT)
                    tk.Label(frame, text="小黑盒赔率:", font=self.input_font).pack(side=tk.LEFT)
                    entry = tk.Entry(frame, width=10, font=self.input_font)
                    entry.pack(side=tk.LEFT)
                    self.entries[team] = entry
                    team_key = (teams[i + j]["MatchTime"], team)
                    if team_key in self.results and self.results[team_key]["LittleBlackBox_Odds"] != "N/A":
                        entry.insert(0, str(self.results[team_key]["LittleBlackBox_Odds"]))
                    entry.bind("<Return>", lambda event, t=team, p=page, idx=i//2, next_idx=j+1: self.handle_enter(t, p, idx, next_idx))

    def load_existing_data(self):
        """加载所有 JSON 文件并合并到 self.results"""
        with open(self.matches_file, 'r', encoding='utf-8') as f:
            matches_data = json.load(f)
            for match in matches_data["matches"]:
                match_id = match["MatchID"]
                match_time = match["MatchTime"]
                for team_key, team_name in [("TeamA", match["TeamA"]), ("TeamB", match["TeamB"])]:
                    if team_name:
                        key = (match_time, team_name)
                        odds = match[f"{team_key}_Odds"]
                        self.results[key] = {
                            "MatchID": match_id,
                            "MatchTime": match_time,
                            "Team": team_name,
                            "Odds": float(odds) if odds != "N/A" else "N/A",
                            "LittleBlackBox_Odds": "N/A",
                            "Probability": "N/A",
                            "Expected_Profit": "N/A",
                            "ProfitVariance": "N/A",
                            "Kelly": "N/A",
                            "LittleBlackBox_Rake": "N/A"
                        }

        # 加载 odds_probability.json
        if os.path.exists(self.result_files["odds_probability"]):
            with open(self.result_files["odds_probability"], 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("odds", []):
                    match_id = item["MatchID"]
                    for team_key in ["TeamA", "TeamB"]:
                        odds_key = f"{team_key}_Odds"
                        team_name = next((t["Team"] for t in self.teams if str(t["Odds"]) == str(item[odds_key])), None)
                        if team_name:
                            match_time = next(t["MatchTime"] for t in self.teams if t["Team"] == team_name)
                            key = (match_time, team_name)
                            if key in self.results:
                                self.results[key].update({
                                    "Probability": float(item[f"{team_key}_Probability"]) if item[f"{team_key}_Probability"] != "N/A" else "N/A",
                                    "LittleBlackBox_Rake": float(item[f"{team_key}_PlatformRake"]) if item[f"{team_key}_PlatformRake"] != "N/A" else "N/A"
                                })

        # 加载 littleblackbox_odds.json
        if os.path.exists(self.result_files["littleblackbox_odds"]):
            with open(self.result_files["littleblackbox_odds"], 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("littleblackbox", []):
                    match_id = item["MatchID"]
                    for team_key in ["TeamA", "TeamB"]:
                        lbb_odds_key = f"{team_key}_LittleBlackBox_Odds"
                        team_name = next((m[team_key] for m in matches_data["matches"] if m["MatchID"] == match_id), None)
                        if team_name:
                            match_time = next(m["MatchTime"] for m in matches_data["matches"] if m["MatchID"] == match_id)
                            key = (match_time, team_name)
                            if key in self.results:
                                self.results[key].update({
                                    "LittleBlackBox_Odds": float(item[lbb_odds_key]) if item[lbb_odds_key] != "N/A" else "N/A"
                                })

        # 加载 expected_profit_variance.json
        if os.path.exists(self.result_files["expected_profit_variance"]):
            with open(self.result_files["expected_profit_variance"], 'r', encoding='utf-8') as f:
                data = json.load(f)
                for item in data.get("profit", []):
                    match_id = item["MatchID"]
                    for team_key in ["TeamA", "TeamB"]:
                        exp_profit_key = f"{team_key}_Expected_Profit"
                        var_key = f"{team_key}_ProfitVariance"
                        kelly_key = f"{team_key}_Kelly"
                        team_name = next((m[team_key] for m in matches_data["matches"] if m["MatchID"] == match_id), None)
                        if team_name:
                            match_time = next(m["MatchTime"] for m in matches_data["matches"] if m["MatchID"] == match_id)
                            key = (match_time, team_name)
                            if key in self.results:
                                self.results[key].update({
                                    "Expected_Profit": float(item[exp_profit_key]) if item[exp_profit_key] != "N/A" else "N/A",
                                    "ProfitVariance": float(item[var_key]) if item[var_key] != "N/A" else "N/A",
                                    "Kelly": float(item[kelly_key]) if item[kelly_key] != "N/A" else "N/A"
                                })

    def check_odds_changed(self):
        with open(self.matches_file, 'r', encoding='utf-8') as f:
            matches_data = json.load(f)
        
        for match in matches_data["matches"]:
            match_id = match["MatchID"]
            for team_key in ["TeamA", "TeamB"]:
                team_name = match[team_key]
                if not team_name:
                    continue
                key = (match["MatchTime"], team_name)
                current_odds = float(match[f"{team_key}_Odds"]) if match[f"{team_key}_Odds"] != "N/A" else "N/A"
                current_lbb_odds = self.entries.get(team_name, tk.Entry()).get()
                current_lbb_odds = float(current_lbb_odds) if current_lbb_odds else "N/A"
                if key in self.results:
                    stored_odds = float(self.results[key]["Odds"]) if self.results[key]["Odds"] != "N/A" else "N/A"
                    stored_lbb_odds = self.results[key].get("LittleBlackBox_Odds", "N/A")
                    if current_odds != stored_odds or (stored_lbb_odds != "N/A" and current_lbb_odds != stored_lbb_odds):
                        return True
        return False

    def update_special_info(self, match, entry):
        new_time = entry.get().strip()
        if new_time:
            with open(self.matches_file, 'r', encoding='utf-8') as f:
                matches_data = json.load(f)
            for m in matches_data["matches"]:
                if m["MatchID"] == match["MatchID"]:
                    m["MatchTime"] = new_time
                    if "SpecialInfo" in m:
                        del m["SpecialInfo"]
                    break
            with open(self.matches_file, 'w', encoding='utf-8') as f:
                json.dump(matches_data, f, ensure_ascii=False, indent=2)
            
            for team in [match["TeamA"], match["TeamB"]]:
                if team in self.tree_items:
                    item = self.tree_items[team]
                    values = list(self.tree.item(item, "values"))
                    values[0] = new_time
                    self.tree.item(item, values=tuple(values))

    def handle_enter(self, team, page, page_idx, next_idx):
        # 更新当前队伍
        self.calculate_for_team(team, page_idx)
        lbb_odds = self.entries[team].get()
        if lbb_odds:
            team_idx = next(i for i, t in enumerate(self.teams) if t["Team"] == team)
            match_time = self.teams[team_idx]["MatchTime"]
            team_key = (match_time, team)
            if team_key in self.results:
                self.results[team_key]["LittleBlackBox_Odds"] = float(lbb_odds)

        # 检查是否为第二支队伍，若是则同步更新两支队伍的数据
        opponent_idx = team_idx + 1 if team_idx % 2 == 0 else team_idx - 1
        if opponent_idx < len(self.teams):
            opponent = self.teams[opponent_idx]["Team"]
            opp_lbb_odds = self.entries[opponent].get()
            if opp_lbb_odds:  # 如果对手的小黑盒赔率已输入，同步更新两支队伍
                opp_key = (match_time, opponent)
                if opp_key in self.results:
                    self.results[opp_key]["LittleBlackBox_Odds"] = float(opp_lbb_odds)
                # 重新计算两支队伍的指标
                self.calculate_for_team(team, page_idx)
                self.calculate_for_team(opponent, page_idx)

        # 保存到结果文件
        match_folder = os.path.join("match_data", self.match_name)
        data_processor.save_results(list(self.results.values()), match_folder, self.match_name)
        
        current_entries = [self.entries[t] for t in self.entries if t in [self.teams[page_idx * 2]["Team"], 
                                                                        self.teams[page_idx * 2 + 1]["Team"]] 
                          if page_idx * 2 + 1 < len(self.teams)]
        if next_idx < len(current_entries):
            current_entries[next_idx].focus_set()
        else:
            all_filled = all(self.entries[t].get() for t in self.entries if t in [self.teams[page_idx * 2]["Team"], 
                                                                                 self.teams[page_idx * 2 + 1]["Team"]] 
                            if page_idx * 2 + 1 < len(self.teams))
            if all_filled and page_idx < (len(self.teams) - 1) // 2:
                self.notebook.select(page_idx + 1)
                next_page_entries = [self.entries[t] for t in self.entries if t in [self.teams[(page_idx + 1) * 2]["Team"], 
                                                                                   self.teams[(page_idx + 1) * 2 + 1]["Team"]] 
                                    if (page_idx + 1) * 2 + 1 < len(self.teams)]
                if next_page_entries:
                    next_page_entries[0].focus_set()

    def calculate_for_team(self, team, page_idx):
        odds = next(t["Odds"] for t in self.teams if t["Team"] == team)
        lbb_odds = self.entries[team].get()
        lbb_odds = float(lbb_odds) if lbb_odds else None
        
        team_idx = next(i for i, t in enumerate(self.teams) if t["Team"] == team)
        opponent_idx = team_idx + 1 if team_idx % 2 == 0 else team_idx - 1
        opponent = self.teams[opponent_idx]["Team"] if opponent_idx < len(self.teams) else None
        opp_lbb_odds = self.entries[opponent].get() if opponent else None
        opp_lbb_odds = float(opp_lbb_odds) if opp_lbb_odds else None

        opponent_data = {"team": opponent, "lbb_odds": opp_lbb_odds}
        match_time = self.teams[team_idx]["MatchTime"]
        result = data_processor.calculate_team_metrics(team, odds, lbb_odds, opponent_data, self.teams)
        
        result["MatchTime"] = match_time
        item = self.tree_items.get(team)
        if item:
            self.tree.item(item, values=(
                result["MatchTime"],
                result["Team"],
                f"{result['Odds']:.2f}" if isinstance(result['Odds'], (int, float)) and result['Odds'] != "N/A" else str(result['Odds']) if result['Odds'] != "N/A" else "N/A",
                f"{result['LittleBlackBox_Odds']:.2f}" if result['LittleBlackBox_Odds'] != "N/A" else "N/A",
                f"{result['Probability']:.2f}" if result['Probability'] != "N/A" else "N/A",
                f"{result['Expected_Profit'] * 100:.2f}%" if result['Expected_Profit'] != "N/A" else "N/A",
                f"{result['ProfitVariance']:.2f}" if result['ProfitVariance'] != "N/A" else "N/A",
                f"{result['Kelly']:.9f}" if result['Kelly'] != "N/A" else "N/A",
                f"{result['LittleBlackBox_Rake']:.3%}" if result['LittleBlackBox_Rake'] != "N/A" else "N/A"
            ))
        self.results[(match_time, team)] = result