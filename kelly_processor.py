import csv
import os
from tkinter import ttk, font, Tk
import tkinter as tk

def generate_kelly_sorted_csv(original_file):
    """生成按Kelly值排序的新CSV文件"""
    base_path, base_name = os.path.split(original_file)
    new_file_name = f"Ky_{base_name}"
    new_file_path = os.path.join(base_path, new_file_name)

    data = []
    with open(original_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if float(row["Kelly"]) > 0:
                data.append(row)

    data.sort(key=lambda x: float(x["Kelly"]), reverse=True)

    with open(new_file_path, 'w', encoding='utf-8', newline='') as f:
        fieldnames = reader.fieldnames + ["Allocated_Coins"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

    return new_file_path, data

def calculate_coin_allocation(data, total_coins):
    """计算并分配coins"""
    kelly_sum = sum(float(row["Kelly"]) for row in data)
    remaining_coins = total_coins
    allocated_data = []

    # 第一次分配
    for row in data:
        kelly = float(row["Kelly"])
        if kelly_sum > 1:
            proportion = kelly / kelly_sum
            coins = proportion * total_coins
        else:
            coins = kelly * total_coins
        
        allocated_coins = min(coins, 5000)
        remaining_coins -= allocated_coins
        row["Allocated_Coins"] = allocated_coins
        allocated_data.append(row)

    # 处理剩余coins，避免无限循环
    if remaining_coins > 0:
        # 只对未达上限的行重新分配
        remaining_data = [row for row in allocated_data if row["Allocated_Coins"] < 5000 and float(row["Kelly"]) > 0]
        while remaining_coins > 0.01 and remaining_data:  # 设置最小阈值避免浮点误差无限循环
            kelly_sum = sum(float(row["Kelly"]) for row in remaining_data)
            if kelly_sum <= 0:
                break
            
            coins_per_cycle = min(remaining_coins, 5000 * len(remaining_data))  # 限制单次分配总量
            temp_remaining = remaining_coins
            
            for row in remaining_data[:]:  # 使用副本避免修改列表时出错
                kelly = float(row["Kelly"])
                proportion = kelly / kelly_sum
                coins = proportion * coins_per_cycle
                current_coins = row["Allocated_Coins"]
                new_coins = min(coins, 5000 - current_coins)
                
                if new_coins < 0.01:  # 如果新增coins太小，跳过以减少计算量
                    remaining_data.remove(row)
                    continue
                
                row["Allocated_Coins"] += new_coins
                temp_remaining -= new_coins
                
                if row["Allocated_Coins"] >= 4999.99:  # 考虑浮点误差
                    remaining_data.remove(row)
            
            remaining_coins = temp_remaining
            if remaining_coins < 0.01:  # 防止浮点误差导致的微小负值
                remaining_coins = 0

    # 四舍五入到两位小数
    for row in allocated_data:
        row["Allocated_Coins"] = round(row["Allocated_Coins"], 2)

    return allocated_data

class KellyApp:
    def __init__(self, root, csv_file):
        self.root = root
        self.root.title("Kelly排序分析")
        self.csv_file = csv_file
        self.table_font = font.Font(family="Arial", size=12)
        self.input_font = font.Font(family="Arial", size=16)
        root.option_add("*Font", self.table_font)

        self.kelly_file, self.data = generate_kelly_sorted_csv(csv_file)

        main_frame = tk.Frame(root)
        main_frame.pack(pady=10, fill="both", expand=True)

        input_frame = tk.Frame(main_frame)
        input_frame.pack(side=tk.TOP, pady=5)
        tk.Label(input_frame, text="总Coins:", font=self.input_font).pack(side=tk.LEFT)
        self.coins_entry = tk.Entry(input_frame, width=10, font=self.input_font)
        self.coins_entry.pack(side=tk.LEFT)
        self.coins_entry.bind("<Return>", self.update_table)

        self.tree = ttk.Treeview(main_frame, columns=("Team", "Odds", "LittleBlackBox_Odds", 
                                                      "Probability", "Expected_Profit", "ProfitVariance", 
                                                      "Kelly", "LittleBlackBox_Rake", "Allocated_Coins"), 
                                 show="headings")
        self.tree.heading("Team", text="队伍")
        self.tree.heading("Odds", text="赔率")
        self.tree.heading("LittleBlackBox_Odds", text="小黑盒赔率")
        self.tree.heading("Probability", text="胜率")
        self.tree.heading("Expected_Profit", text="期望收益")
        self.tree.heading("ProfitVariance", text="收益方差")
        self.tree.heading("Kelly", text="凯利比例")
        self.tree.heading("LittleBlackBox_Rake", text="小黑盒抽成")
        self.tree.heading("Allocated_Coins", text="分配Coins")
        
        self.tree.column("Team", width=150)
        self.tree.column("Odds", width=80)
        self.tree.column("LittleBlackBox_Odds", width=80)
        self.tree.column("Probability", width=80)
        self.tree.column("Expected_Profit", width=100)
        self.tree.column("ProfitVariance", width=100)
        self.tree.column("Kelly", width=80)
        self.tree.column("LittleBlackBox_Rake", width=100)
        self.tree.column("Allocated_Coins", width=100)
        
        self.tree.pack(side=tk.TOP, pady=10, fill="both", expand=True)

        self.update_table(None)

    def update_table(self, event):
        """更新表格显示分配结果"""
        self.tree.delete(*self.tree.get_children())
        
        total_coins_str = self.coins_entry.get()
        if not total_coins_str:
            total_coins = 0
        else:
            try:
                total_coins = float(total_coins_str)
            except ValueError:
                total_coins = 0

        if total_coins > 0:
            allocated_data = calculate_coin_allocation(self.data.copy(), total_coins)
        else:
            allocated_data = [dict(row, Allocated_Coins=0) for row in self.data]

        for row in allocated_data:
            self.tree.insert("", "end", values=(
                row["Team"],
                row["Odds"],
                row["LittleBlackBox_Odds"],
                row["Probability"],
                row["Expected_Profit"],
                row["ProfitVariance"],
                row["Kelly"],
                row["LittleBlackBox_Rake"],
                f"{row['Allocated_Coins']:.2f}"
            ))

        with open(self.kelly_file, 'w', encoding='utf-8', newline='') as f:
            fieldnames = ["Team", "Odds", "LittleBlackBox_Odds", "Probability", 
                         "Expected_Profit", "ProfitVariance", "Kelly", "LittleBlackBox_Rake", "Allocated_Coins"]
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(allocated_data)