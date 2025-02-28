import tkinter as tk
from tkinter import ttk, messagebox
import fetch_odds
import data_processor
import odds_gui
import kelly_processor  # 新增导入
import os
import json
import csv

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("电竞赔率工具")
        self.root.geometry("400x300")

        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(self.main_frame, text="输入URL:").grid(row=0, column=0, pady=5, sticky=tk.W)
        self.url_entry = ttk.Entry(self.main_frame, width=40)
        self.url_entry.grid(row=1, column=0, pady=5, sticky=(tk.W, tk.E))
        self.url_entry.insert(0, "https://cyber-ggbet.com/cn/esports/tournament/esl-pro-league-season-21-play-in-11-02")

        self.fetch_button = ttk.Button(self.main_frame, text="获取/检查赔率数据", command=self.check_or_fetch_odds)
        self.fetch_button.grid(row=2, column=0, pady=10)

        self.analyze_button = ttk.Button(self.main_frame, text="分析赔率", command=self.open_analysis, state="disabled")
        self.analyze_button.grid(row=3, column=0, pady=10)

        self.kelly_button = ttk.Button(self.main_frame, text="Kelly分析", command=self.open_kelly_analysis, state="disabled")
        self.kelly_button.grid(row=4, column=0, pady=10)

        self.status_label = ttk.Label(self.main_frame, text="状态: 就绪")
        self.status_label.grid(row=5, column=0, pady=5, sticky=tk.W)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        self.url_cache = {}
        self.load_url_cache()

    def load_url_cache(self):
        cache_file = "url_cache.json"
        if os.path.exists(cache_file):
            with open(cache_file, 'r', encoding='utf-8') as f:
                self.url_cache = json.load(f)

    def save_url_cache(self):
        cache_file = "url_cache.json"
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(self.url_cache, f)

    def check_or_fetch_odds(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("错误", "请输入有效的URL")
            return

        match_name = fetch_odds.extract_match_name(url)
        csv_filename = os.path.join("Odds_Data", f"{match_name}_odds.csv")
        if url in self.url_cache and os.path.exists(self.url_cache[url]):
            result = messagebox.askyesno("使用旧数据", f"已找到旧数据（{self.url_cache[url]}），是否使用？\n选择否将重新联网获取。")
            if result:
                self.status_label.config(text="状态: 使用旧数据")
                self.analyze_button.config(state="normal")
                self.kelly_button.config(state="normal")
                return
            else:
                if os.path.exists(self.url_cache[url]):
                    os.remove(self.url_cache[url])

        self.status_label.config(text="状态: 正在获取数据...")
        self.fetch_button.config(state="disabled")
        self.root.update()

        try:
            result, filename = fetch_odds.fetch_team_odds(url)
            if result == 0 and filename:
                self.status_label.config(text="状态: 数据获取成功")
                messagebox.showinfo("成功", f"赔率数据已保存到 {filename}")
                self.url_cache[url] = filename
                self.save_url_cache()
                self.analyze_button.config(state="normal")
                self.kelly_button.config(state="normal")
            else:
                self.status_label.config(text="状态: 数据获取失败")
                messagebox.showerror("失败", "获取数据时出错，请检查日志")
        except Exception as e:
            self.status_label.config(text="状态: 程序出错")
            messagebox.showerror("错误", f"程序运行出错: {e}")
        finally:
            self.fetch_button.config(state="normal")

    def open_analysis(self):
        url = self.url_entry.get().strip()
        if url in self.url_cache and os.path.exists(self.url_cache[url]):
            teams = data_processor.read_csv(self.url_cache[url])
            if not teams:
                messagebox.showerror("错误", "没有找到团队数据，请先获取数据")
                return
            analysis_window = tk.Toplevel(self.root)
            odds_gui.BettingApp(analysis_window, teams)
        else:
            messagebox.showerror("错误", "请先获取赔率数据")

    def open_kelly_analysis(self):
        url = self.url_entry.get().strip()
        if url in self.url_cache and os.path.exists(self.url_cache[url]):
            csv_file = os.path.join("Odds_Data", "ESL_Pro_League_S21_PlayIn_2025-02-11_odds.csv")
            if not os.path.exists(csv_file):
                messagebox.showerror("错误", "请先完成赔率分析生成结果文件")
                return
            kelly_window = tk.Toplevel(self.root)
            kelly_processor.KellyApp(kelly_window, csv_file)
        else:
            messagebox.showerror("错误", "请先获取赔率数据")

def main():
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()