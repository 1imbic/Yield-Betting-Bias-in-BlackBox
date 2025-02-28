import tkinter as tk
from tkinter import ttk, font
import data_processor
import csv
import os

class BettingApp:
    def __init__(self, root, teams):
        self.root = root
        self.root.title("小黑盒赔率分析")
        self.teams = teams
        self.table_font = font.Font(family="Arial", size=12)
        self.input_font = font.Font(family="Arial", size=16)
        root.option_add("*Font", self.table_font)

        main_frame = tk.Frame(root)
        main_frame.pack(pady=10, fill="both", expand=True)

        self.tree = ttk.Treeview(main_frame, columns=("Team", "Odds", "LittleBlackBox_Odds", 
                                                     "Probability", "Expected_Profit", "ProfitVariance", 
                                                     "Kelly", "LittleBlackBox_Rake"), show="headings")
        self.tree.heading("Team", text="队伍")
        self.tree.heading("Odds", text="赔率")
        self.tree.heading("LittleBlackBox_Odds", text="小黑盒赔率")
        self.tree.heading("Probability", text="胜率")
        self.tree.heading("Expected_Profit", text="期望收益")
        self.tree.heading("ProfitVariance", text="收益方差")
        self.tree.heading("Kelly", text="凯利比例")
        self.tree.heading("LittleBlackBox_Rake", text="小黑盒抽成")
        
        self.tree.column("Team", width=150)
        self.tree.column("Odds", width=80)
        self.tree.column("LittleBlackBox_Odds", width=80)
        self.tree.column("Probability", width=80)
        self.tree.column("Expected_Profit", width=100)
        self.tree.column("ProfitVariance", width=100)
        self.tree.column("Kelly", width=80)
        self.tree.column("LittleBlackBox_Rake", width=100)
        
        self.tree.pack(side=tk.TOP, pady=10, fill="both", expand=True)

        # Load previous results if available
        results_file = os.path.join("Odds_Data", "ESL_Pro_League_S21_PlayIn_2025-02-11_odds.csv")
        results_data = {}
        if os.path.exists(results_file):
            with open(results_file, mode='r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    results_data[row["Team"]] = row

        # Populate the Treeview with data
        for i in range(0, len(teams), 2):
            team1 = teams[i]
            team2 = teams[i + 1] if i + 1 < len(teams) else None
            
            team1_default = {
                "Team": team1["Team"], 
                "Odds": team1["Odds"], 
                "LittleBlackBox_Odds": "",
                "Probability": "", 
                "Expected_Profit": "", 
                "ProfitVariance": "", 
                "Kelly": "", 
                "LittleBlackBox_Rake": ""
            }
            team1_values = results_data.get(team1["Team"], team1_default)
            self.tree.insert("", "end", values=(
                team1_values.get("Team", ""),
                team1_values.get("Odds", team1["Odds"]),
                team1_values.get("LittleBlackBox_Odds", ""),
                team1_values.get("Probability", ""),
                team1_values.get("Expected_Profit", ""),
                team1_values.get("ProfitVariance", ""),
                team1_values.get("Kelly", ""),
                team1_values.get("LittleBlackBox_Rake", "")
            ))
            
            if team2:
                team2_default = {
                    "Team": team2["Team"], 
                    "Odds": team2["Odds"], 
                    "LittleBlackBox_Odds": "",
                    "Probability": "", 
                    "Expected_Profit": "", 
                    "ProfitVariance": "", 
                    "Kelly": "", 
                    "LittleBlackBox_Rake": ""
                }
                team2_values = results_data.get(team2["Team"], team2_default)
                self.tree.insert("", "end", values=(
                    team2_values.get("Team", ""),
                    team2_values.get("Odds", team2["Odds"]),
                    team2_values.get("LittleBlackBox_Odds", ""),
                    team2_values.get("Probability", ""),
                    team2_values.get("Expected_Profit", ""),
                    team2_values.get("ProfitVariance", ""),
                    team2_values.get("Kelly", ""),
                    team2_values.get("LittleBlackBox_Rake", "")
                ))
            if i + 2 < len(teams):
                self.tree.insert("", "end", values=("", "", "", "", "", "", "", ""))

        input_frame = tk.Frame(main_frame)
        input_frame.pack(side=tk.BOTTOM, pady=10, fill="both", expand=True)
        self.notebook = ttk.Notebook(input_frame)
        self.notebook.pack(fill="both", expand=True)

        self.entries = {}
        self.results = {}
        saved_inputs = data_processor.load_inputs()

        for i in range(0, len(teams), 2):
            page = tk.Frame(self.notebook)
            self.notebook.add(page, text=f"第 {i//2 + 1} 组")
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
                    if team in results_data and results_data[team].get("LittleBlackBox_Odds"):
                        entry.insert(0, results_data[team]["LittleBlackBox_Odds"])
                    elif team in saved_inputs and saved_inputs[team]:
                        entry.insert(0, str(saved_inputs[team]))
                    entry.bind("<Return>", lambda event, t=team, p=page, idx=i//2, next_idx=j+1: self.handle_enter(t, p, idx, next_idx))

    def handle_enter(self, team, page, page_idx, next_idx):
        self.calculate_for_team(team, page_idx)
        lbb_odds = self.entries[team].get()
        if lbb_odds:
            saved_inputs = data_processor.load_inputs()
            saved_inputs[team] = float(lbb_odds) if lbb_odds else None
            data_processor.save_inputs(saved_inputs)
        if hasattr(self, 'results'):
            data_processor.save_results(list(self.results.values()))
        
        current_entries = [self.entries[t] for t in self.entries if t in [self.teams[page_idx * 2]["Team"], 
                         self.teams[page_idx * 2 + 1]["Team"]] if page_idx * 2 + 1 < len(self.teams)]
        if next_idx < len(current_entries):
            current_entries[next_idx].focus_set()
        else:
            all_filled = all(self.entries[t].get() for t in self.entries if t in [self.teams[page_idx * 2]["Team"], 
                            self.teams[page_idx * 2 + 1]["Team"]] if page_idx * 2 + 1 < len(self.teams))
            if all_filled and page_idx < (len(self.teams) - 1) // 2:
                self.notebook.select(page_idx + 1)
                next_page_entries = [self.entries[t] for t in self.entries if t in [self.teams[(page_idx + 1) * 2]["Team"], 
                                    self.teams[(page_idx + 1) * 2 + 1]["Team"]] if (page_idx + 1) * 2 + 1 < len(self.teams)]
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
        result = data_processor.calculate_team_metrics(team, odds, lbb_odds, opponent_data, self.teams)
        
        for item in self.tree.get_children():
            values = self.tree.item(item, "values")
            if values[0] == team:
                self.tree.item(item, values=(team, result["Odds"], result["LittleBlackBox_Odds"],
                                           f"{result['Probability']:.2f}" if result["Probability"] != "N/A" else "N/A",
                                           f"{(result['Expected_Profit'] * 100):.2f}%" if result["Expected_Profit"] != "N/A" else "N/A",
                                           f"{result['ProfitVariance']:.2f}" if result["ProfitVariance"] != "N/A" else "N/A",
                                           f"{result['Kelly']:.2f}" if result["Kelly"] != "N/A" else "N/A",
                                           f"{result['LittleBlackBox_Rake']:.3%}" if result["LittleBlackBox_Rake"] != "N/A" else "N/A"))
                break
        
        self.results[team] = result