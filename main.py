import tkinter as tk
from tkinter import ttk, messagebox
import fetch_odds
import data_processor
import odds_gui
import os
import json
import profit_analysis

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电竞赔率工具")
        self.root.geometry("500x300")

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.main_frame, text="输入或选择URL:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.url_combo = ttk.Combobox(self.main_frame, width=37)
        self.url_combo.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        self.url_combo.insert(0, "https://cyber-ggbet.com/cn/esports/tournament/esl-pro-league-season-21-play-in-11-02")

        self.fetch_button = ttk.Button(self.main_frame, text="获取/检查赔率数据", command=self.check_or_fetch_odds)
        self.fetch_button.grid(row=2, column=0, pady=10)

        self.analyze_button = ttk.Button(self.main_frame, text="分析赔率", command=self.open_analysis, state="disabled")
        self.analyze_button.grid(row=3, column=0, pady=10)

        self.profit_button = ttk.Button(self.main_frame, text="统计收益", command=self.open_profit_analysis, state="disabled")
        self.profit_button.grid(row=4, column=0, pady=10)

        self.status_label = ttk.Label(self.main_frame, text="状态: 就绪")
        self.status_label.grid(row=5, column=0, pady=5, sticky=tk.W)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.load_url_cache()
        self.load_url_history()

    def load_url_cache(self):
        cache_file = "url_cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.url_cache = json.load(f)
            new_cache = {}
            for url, filepath in self.url_cache.items():
                if filepath.endswith('.csv') and 'Odds_Data' in filepath:
                    match_name = fetch_odds.extract_match_name(url)
                    new_path = os.path.join("match_data", match_name, "matches_info.json")
                    new_cache[url] = new_path
                else:
                    new_cache[url] = filepath
            self.url_cache = new_cache
            self.save_url_cache()
        else:
            self.url_cache = {}

    def save_url_cache(self):
        cache_file = "url_cache.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.url_cache, f, ensure_ascii=False, indent=2)

    def load_url_history(self):
        self.url_combo['values'] = list(self.url_cache.keys())

    def update_url_history(self, url, filename):
        self.url_cache[url] = filename
        self.url_combo['values'] = list(self.url_cache.keys())
        self.save_url_cache()
        print(f"更新缓存: {url} -> {filename}")

    def check_or_fetch_odds(self):
        url = self.url_combo.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入有效的URL")
            return

        cached_file = self.url_cache.get(url)
        print(f"检查缓存路径: {cached_file}")
        if cached_file and os.path.exists(cached_file):
            result = messagebox.askyesno("使用旧数据", f"已找到旧数据（{cached_file}），是否使用？\n选择否将重新联网获取并合并数据。")
            if result:
                self.status_label.config(text="状态: 使用旧数据")
                self.analyze_button.config(state="normal")
                self.profit_button.config(state="normal")
                return

        self.status_label.config(text="状态: 正在获取数据...")
        self.fetch_button.config(state="disabled")
        self.root.update()

        try:
            result, filename = fetch_odds.fetch_team_odds(url)
            print(f"fetch_team_odds 返回的路径: {filename}")
            if result == 0 and filename:
                self.status_label.config(text="状态: 数据获取成功")
                messagebox.showinfo("成功", f"赔率数据已保存到 {filename}")
                self.update_url_history(url, filename)
                self.analyze_button.config(state="normal")
                self.profit_button.config(state="normal")
            else:
                self.status_label.config(text="状态: 数据获取失败")
                messagebox.showerror("失败", "获取数据时出错，请检查日志")
        except Exception as e:
            self.status_label.config(text="状态: 程序出错")
            messagebox.showerror("错误", f"程序运行出错: {e}")
        finally:
            self.fetch_button.config(state="normal")

    def open_analysis(self):
        url = self.url_combo.get().strip()
        cached_file = self.url_cache.get(url)
        print(f"尝试打开分析，文件路径: {cached_file}")
        if cached_file and os.path.exists(cached_file):
            print(f"文件存在，读取数据: {cached_file}")
            teams = data_processor.read_json(cached_file)
            print(f"读取到的队伍数据: {teams}")
            if not teams:
                messagebox.showerror("错误", "没有找到团队数据，请先获取数据")
                return
            match_name = fetch_odds.extract_match_name(url)
            analysis_window = tk.Toplevel(self.root)
            odds_gui.BettingApp(analysis_window, teams, match_name)
        else:
            messagebox.showerror("错误", "请先获取赔率数据")

    def open_profit_analysis(self):
        url = self.url_combo.get().strip()
        cached_file = self.url_cache.get(url)
        if cached_file and os.path.exists(cached_file):
            match_name = fetch_odds.extract_match_name(url)
            match_folder = os.path.join("match_data", match_name)
            profit_window = tk.Toplevel(self.root)
            profit_analysis.ProfitStatsApp(profit_window, match_folder)
        else:
            messagebox.showerror("错误", "请先获取赔率数据")

def main():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()