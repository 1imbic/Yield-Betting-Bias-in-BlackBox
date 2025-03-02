import json
import os
from tkinter import ttk, font, Tk, messagebox, StringVar
import tkinter as tk
from datetime import datetime, timedelta

class ProfitStatsApp:
    def __init__(self, root, match_folder):
        self.root = root
        self.root.title("收益统计")
        self.match_folder = match_folder
        self.setup_fonts()
        self.load_data()
        self.setup_ui()
        self.load_existing_data()

    def setup_fonts(self):
        self.table_font = font.Font(family="Arial", size=12)
        self.input_font = font.Font(family="Arial", size=16)
        self.root.option_add("*Font", self.table_font)

    def load_data(self):
        self.matches_info = self._load_json("matches_info.json")
        self.exp_variance = self._load_json("expected_profit_variance.json")
        self.lbb_odds = self._load_json("littleblackbox_odds.json")
        self.stats_file = os.path.join(self.match_folder, "profit_stats.json")
        self.current_date = datetime(2025, 3, 2)

    def _load_json(self, filename):
        path = os.path.join(self.match_folder, filename)
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"加载文件 {path} 时出错: {e}")
            return {}

    def setup_ui(self):
        main_frame = tk.Frame(self.root)
        main_frame.pack(pady=10, fill="both", expand=True)

        # 搜索区域
        self.search_frame = self._create_search_frame(main_frame)
        
        # 比赛显示区域
        self.matches_frame = tk.Frame(main_frame)
        self.matches_frame.pack(fill="x", pady=5)
        self.match_entries = {}
        
        # 统计区域
        self.stats_label = tk.Label(main_frame, text="统计结果：\n总投入: 0.00\n总收益: 0.00\n成功率: 0.00%", 
                                  font=self.input_font)
        self.stats_label.pack(pady=10)

    def _create_search_frame(self, parent):
        frame = tk.Frame(parent)
        frame.pack(fill="x", pady=5)
        
        tk.Label(frame, text="搜索队伍:", font=self.input_font).pack(side=tk.LEFT)
        self.search_var = StringVar()
        search_entry = tk.Entry(frame, width=30, font=self.input_font, textvariable=self.search_var)
        search_entry.pack(side=tk.LEFT, padx=5)
        search_entry.bind("<KeyRelease>", self._update_search)
        
        self.search_list = tk.Listbox(frame, height=5, width=50, font=self.input_font)
        self.search_list.pack(side=tk.LEFT, padx=5)
        self.search_list.bind("<<ListboxSelect>>", self._on_select_match)
        
        # 添加队伍选择单选按钮
        self.team_choice = StringVar(value="TeamA")
        tk.Radiobutton(frame, text="TeamA", variable=self.team_choice, value="TeamA", 
                      font=self.input_font).pack(side=tk.LEFT, padx=5)
        tk.Radiobutton(frame, text="TeamB", variable=self.team_choice, value="TeamB", 
                      font=self.input_font).pack(side=tk.LEFT, padx=5)
        
        ttk.Button(frame, text="添加比赛", command=self._add_match).pack(side=tk.LEFT, padx=5)
        return frame

    def _parse_time(self, time_str):
        try:
            if time_str == "未知时间":
                return None
            date, time = time_str.split(' ', 1)
            month, day = date.split('-')
            return datetime.strptime(f"2025-{month}-{day} {time}", '%Y-%m-%d %H:%M')
        except Exception as e:
            print(f"时间解析错误 {time_str}: {e}")
            return None

    def _is_recent(self, match_time):
        match_dt = self._parse_time(match_time)
        return match_dt and match_dt >= self.current_date - timedelta(days=3)

    def _get_kelly(self, match_id, team):
        profit_data = self.exp_variance.get("profit", [])
        return next((float(item[f"{team}_Kelly"]) for item in profit_data 
                    if item["MatchID"] == match_id and item[f"{team}_Kelly"] != "N/A"), 0)

    def _get_odds(self, match_id, team):
        odds_data = self.lbb_odds.get("littleblackbox", [])
        odds = next((float(item[f"{team}_LittleBlackBox_Odds"]) for item in odds_data 
                    if item["MatchID"] == match_id and item[f"{team}_LittleBlackBox_Odds"] != "N/A"), None)
        return odds if odds is not None else "N/A"

    def load_existing_data(self):
        for match in self.matches_info.get("matches", []):
            if not self._is_recent(match["MatchTime"]):
                continue
            match_id = match["MatchID"]
            for team in ["TeamA", "TeamB"]:
                kelly = self._get_kelly(match_id, team)
                if kelly > 0:
                    self._add_match_entry(match, team, kelly)

        stats_data = self._load_json("profit_stats.json")
        for stat in stats_data.get("stats", []):
            match = next((m for m in self.matches_info["matches"] if m["MatchID"] == stat["MatchID"]), None)
            if match and self._is_recent(match["MatchTime"]):
                team = "TeamA" if stat["Team"] == match["TeamA"] else "TeamB"
                key = f"{stat['MatchID']}_{team}"
                if key not in self.match_entries:
                    self._add_match_entry(match, team, self._get_kelly(stat["MatchID"], team))
                entry = self.match_entries[key]
                entry["coins"].delete(0, tk.END)
                entry["coins"].insert(0, str(stat["Coins"]))
                entry["result"].set(stat["Result"])
                self._update_radio_style(key)
        self._update_stats_display()

    def _add_match_entry(self, match, team, kelly):
        match_id = match["MatchID"]
        key = f"{match_id}_{team}"
        team_name = match[team]
        odds = self._get_odds(match_id, team)
        
        frame = tk.Frame(self.matches_frame)
        frame.pack(fill="x", pady=2)
        
        tk.Label(frame, text=f"{match['MatchTime']} - {team_name} (Kelly: {kelly:.4f}, Odds: {odds})", 
                font=self.input_font).pack(side=tk.LEFT)
        
        coins = tk.Entry(frame, width=10, font=self.input_font)
        coins.pack(side=tk.LEFT)
        coins.bind("<Return>", lambda e: self.save_and_update())
        
        result = StringVar(value="None")
        win = tk.Radiobutton(frame, text="Win", variable=result, value="Win", 
                           font=self.input_font, command=lambda: self._update_radio_style(key))
        lose = tk.Radiobutton(frame, text="Lose", variable=result, value="Lose", 
                            font=self.input_font, command=lambda: self._update_radio_style(key))
        win.pack(side=tk.LEFT)
        lose.pack(side=tk.LEFT)
        win.bind("<Return>", lambda e: self.save_and_update())
        lose.bind("<Return>", lambda e: self.save_and_update())
        
        ttk.Button(frame, text="×", command=lambda: self._remove_match(key, frame)).pack(side=tk.RIGHT)
        
        self.match_entries[key] = {"frame": frame, "coins": coins, "result": result, 
                                 "win": win, "lose": lose, "match": match, "team": team}

    def _remove_match(self, key, frame):
        frame.destroy()
        del self.match_entries[key]

    def _update_search(self, event):
        search_text = self.search_var.get().lower()
        self.search_list.delete(0, tk.END)
        for match in self.matches_info.get("matches", []):
            if not self._is_recent(match["MatchTime"]):
                continue
            if search_text in match["TeamA"].lower() or (match["TeamB"] and search_text in match["TeamB"].lower()):
                self.search_list.insert(tk.END, f"{match['MatchTime']} - {match['TeamA']} vs {match['TeamB']}")

    def _on_select_match(self, event):
        if self.search_list.curselection():
            self.search_var.set(self.search_list.get(self.search_list.curselection()))

    def _add_match(self):
        selected = self.search_var.get()
        if not selected:
            messagebox.showwarning("警告", "请选择比赛")
            return
        
        try:
            time, teams = selected.split(" - ", 1)
            team_a, team_b = teams.split(" vs ")
            match = next((m for m in self.matches_info["matches"] 
                        if m["MatchTime"] == time and m["TeamA"] == team_a and m["TeamB"] == team_b), None)
            if not match:
                raise ValueError("未找到比赛")
                
            team = self.team_choice.get()
            key = f"{match['MatchID']}_{team}"
            if key in self.match_entries:
                messagebox.showwarning("警告", "该队伍已添加")
                return
                
            self._add_match_entry(match, team, self._get_kelly(match["MatchID"], team))
        except Exception as e:
            messagebox.showerror("错误", f"添加失败: {e}")

    def _update_radio_style(self, key):
        entry = self.match_entries[key]
        result = entry["result"].get()
        bold_font = ("Arial", 16, "bold")
        normal_font = ("Arial", 16)
        
        entry["win"].config(font=bold_font if result == "Win" else normal_font,
                          foreground="red" if result == "Win" else "black")
        entry["lose"].config(font=bold_font if result == "Lose" else normal_font,
                           foreground="red" if result == "Lose" else "black")

    def save_and_update(self):
        stats = []
        total_coins = total_profit = wins = matches = 0
        
        for key, entry in self.match_entries.items():
            match_id = key.split("_")[0]
            coins = float(entry["coins"].get() or 0)
            result = entry["result"].get()
            odds = self._get_odds(match_id, entry["team"])
            profit = (odds * coins if result == "Win" and odds != "N/A" else -coins) if coins > 0 else 0
            
            stats.append({
                "MatchID": match_id,
                "MatchTime": entry["match"]["MatchTime"],
                "Team": entry["match"][entry["team"]],
                "Coins": coins,
                "Result": result,
                "Profit": profit
            })
            
            if coins > 0:
                total_coins += coins
                total_profit += profit
                wins += 1 if result == "Win" else 0
                matches += 1
                
        summary = {
            "TotalCoins": total_coins,
            "TotalProfit": total_profit,
            "SuccessRate": wins / matches if matches > 0 else 0
        }
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump({"stats": stats, "summary": summary}, f, ensure_ascii=False, indent=2)
            
        self._update_stats_display()

    def _update_stats_display(self):
        data = self._load_json("profit_stats.json")
        s = data.get("summary", {})
        text = f"统计结果：\n总投入: {s.get('TotalCoins', 0):.2f}\n总收益: {s.get('TotalProfit', 0):.2f}\n" \
              f"成功率: {s.get('SuccessRate', 0):.2%}"
        self.stats_label.config(text=text)

if __name__ == "__main__":
    root = Tk()
    app = ProfitStatsApp(root, "match_data/esl_pro_league_season_21")
    root.mainloop()