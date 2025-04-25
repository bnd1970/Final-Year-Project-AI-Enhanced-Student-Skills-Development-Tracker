# home_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from auth import login_user
from database import init_db
from pathlib import Path
import subprocess
import matplotlib.pyplot as plt
from tkinter import filedialog
import sys
import os
import numpy as np

class HomePage:
    def __init__(self, root):
        self.root = root
        self.root.title("Collaboration Analysis System")
        self.root.geometry("1200x800")
        self.current_user = None
        init_db()
        self.setup_style()
        self.show_login()

    def setup_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TFrame", background="#f0f2f5")
        style.configure("TButton", font=("Arial", 10), padding=6)
        style.configure("Header.TLabel", 
                        font=("Arial", 16, "bold"), 
                        background="#1890ff", 
                        foreground="white")
        style.map("TButton",
                foreground=[('active', 'white'), ('!disabled', 'black')],
                background=[('active', '#0052cc'), ('!disabled', '#1890ff')])

    def attempt_login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Both fields are required")
            return
        
        user = login_user(username, password)
        
        if user:
            self.current_user = user
            self.show_main_interface()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def show_login(self):
        login_frame = ttk.Frame(self.root)
        login_frame.place(relx=0.5, rely=0.5, anchor="center")
        
        ttk.Label(login_frame, 
                 text="Collaboration Analysis System", 
                 style="Header.TLabel").grid(row=0, columnspan=2, pady=20)
        
        ttk.Label(login_frame, text="Username:").grid(row=1, column=0, pady=5)
        self.username_entry = ttk.Entry(login_frame)
        self.username_entry.grid(row=1, column=1, pady=5)
        
        ttk.Label(login_frame, text="Password:").grid(row=2, column=0, pady=5)
        self.password_entry = ttk.Entry(login_frame, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)
        
        login_btn = ttk.Button(login_frame, 
                              text="Login", 
                              command=self.attempt_login)
        login_btn.grid(row=3, columnspan=2, pady=20)

    def logout(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.show_login()

    def show_main_interface(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        nav_frame = ttk.Frame(main_frame)
        nav_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
        
        role = "Leader" if self.current_user['role'] == 'leader' else 'Member'
        user_info = ttk.Label(nav_frame, 
                             text=f"Welcome {self.current_user['username']} ({role})",
                             font=("Arial", 12))
        user_info.pack(side=tk.LEFT)
        
        nav_controls = ttk.Frame(nav_frame)
        nav_controls.pack(side=tk.RIGHT)
        
        ttk.Button(nav_controls, text="Profile", command=self.show_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(nav_controls, text="Logout", command=self.logout).pack(side=tk.LEFT, padx=5)
        
        self.setup_dashboard(main_frame)

    def setup_dashboard(self, parent):
        dashboard_frame = ttk.Frame(parent)
        dashboard_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        sidebar = ttk.Frame(dashboard_frame, width=200)
        sidebar.pack(side=tk.LEFT, fill=tk.Y)
        
        menu_items = [
            ("Data Preprocess", self.show_preprocess),
            ("Collaboration Analysis", self.show_analysis),
            ("Progress Reports", self.show_reports)
        ]
        if self.current_user['role'] == 'leader':
            menu_items.append(("Group Management", self.show_group_management))
        
        for text, cmd in menu_items:
            btn = ttk.Button(sidebar, text=text, command=cmd)
            btn.pack(fill=tk.X, pady=5)
        
        self.content_area = ttk.Frame(dashboard_frame)
        self.content_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.show_profile()

    def show_profile(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        profile_frame = ttk.Frame(self.content_area)
        profile_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        ttk.Label(profile_frame, text="Profile Settings", font=("Arial", 14)).grid(row=0, column=0, sticky=tk.W)
        
        ttk.Label(profile_frame, text="New Password:").grid(row=1, column=0, pady=5)
        self.new_pass_entry = ttk.Entry(profile_frame, show="*")
        self.new_pass_entry.grid(row=1, column=1, pady=5)
        
        ttk.Button(profile_frame, 
                text="Update Password", 
                command=self.update_password).grid(row=2, columnspan=2, pady=10)

        if self.current_user['role'] == 'member':
            ttk.Label(profile_frame, text="Group Management").grid(row=3, column=0, sticky=tk.W, pady=10)
            self.group_combobox = ttk.Combobox(profile_frame)
            self.group_combobox.grid(row=3, column=1, pady=10)
            ttk.Button(profile_frame,
                    text="Join Group",
                    command=self.join_group).grid(row=4, columnspan=2)

    def update_password(self):
        new_password = self.new_pass_entry.get()
        if not new_password:
            messagebox.showerror("Error", "Password cannot be empty")
            return
            
        from auth import update_user_info, hash_password
        success = update_user_info(
            self.current_user['username'],
            {'password_hash': hash_password(new_password)}
        )
            
        if success:
            messagebox.showinfo("Success", "Password updated successfully")
            self.new_pass_entry.delete(0, tk.END)
        else:
            messagebox.showerror("Error", "Password update failed")

    def join_group(self):
        selected_group = self.group_combobox.get()
        from auth import update_user_info
        if update_user_info(
            self.current_user['username'],
            {'group_name': selected_group}
        ):
            messagebox.showinfo("Success", f"Joined group: {selected_group}")
            self.current_user['group'] = selected_group
        else:
            messagebox.showerror("Error", "Failed to join group")

    def show_preprocess(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        preprocess_frame = ttk.Frame(self.content_area)
        preprocess_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(preprocess_frame, text="Raw Chat File:").grid(row=0, column=0, sticky=tk.W)
        self.raw_file_entry = ttk.Entry(preprocess_frame, width=40)
        self.raw_file_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(preprocess_frame, 
                  text="Browse...", 
                  command=self.select_raw_file).grid(row=0, column=2)
        
        ttk.Label(preprocess_frame, text="Output Filename:").grid(row=1, column=0, sticky=tk.W, pady=10)
        self.output_file_entry = ttk.Entry(preprocess_frame, width=40)
        self.output_file_entry.grid(row=1, column=1, pady=10)
        
        process_btn = ttk.Button(preprocess_frame, 
                                text="Start Processing", 
                                command=self.run_preprocessing)
        process_btn.grid(row=2, columnspan=3, pady=20)
        
        self.preprocess_status = ttk.Label(preprocess_frame, text="")
        self.preprocess_status.grid(row=3, columnspan=3)

    def select_raw_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Raw Chat File",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if file_path:
            self.raw_file_entry.delete(0, tk.END)
            self.raw_file_entry.insert(0, file_path)

    def run_preprocessing(self):
        raw_path = self.raw_file_entry.get()
        output_name = self.output_file_entry.get()
        
        if not raw_path or not output_name:
            messagebox.showerror("Error", "Both fields are required")
            return
        
        try:
            cmd = [
                sys.executable, "preprocess_form.py",
                raw_path,
                os.path.join("output_form", f"{output_name}.xlsx")
            ]
            subprocess.run(cmd, check=True)
            self.preprocess_status.config(text="Processing completed successfully", foreground="green")
        except Exception as e:
            self.preprocess_status.config(text=f"Error: {str(e)}", foreground="red")

    def show_analysis(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        analysis_frame = ttk.Frame(self.content_area)
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(analysis_frame, text="Preprocessed File:").grid(row=0, column=0, sticky=tk.W)
        self.processed_file_entry = ttk.Entry(analysis_frame, width=40)
        self.processed_file_entry.grid(row=0, column=1, padx=5)
        
        ttk.Button(analysis_frame, 
                  text="Browse...", 
                  command=self.select_processed_file).grid(row=0, column=2)
        
        ttk.Button(analysis_frame,
                  text="Start Analysis",
                  command=self.run_analysis).grid(row=1, columnspan=3, pady=20)
        
        self.progress = ttk.Progressbar(analysis_frame, orient=tk.HORIZONTAL, mode='indeterminate')
        self.progress.grid(row=2, columnspan=3, sticky=tk.EW)
        
        self.analysis_result = ttk.Label(analysis_frame, text="")
        self.analysis_result.grid(row=3, columnspan=3)

    def select_processed_file(self):
        file_path = filedialog.askopenfilename(
            initialdir="output_form",
            title="Select Preprocessed File",
            filetypes=[("Excel Files", "*.xlsx")]
        )
        if file_path:
            self.processed_file_entry.delete(0, tk.END)
            self.processed_file_entry.insert(0, file_path)

    def run_analysis(self):
        input_file = self.processed_file_entry.get()
        if not input_file:
            messagebox.showerror("Error", "Please select a file first")
            return
        
        self.progress.start()
        try:
            cmd = [sys.executable, "analysis_form.py", "--input", input_file]
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            self.analysis_result.config(
                text=f"Analysis completed:\n{result.stdout}",
                foreground="green"
            )
        except subprocess.CalledProcessError as e:
            self.analysis_result.config(
                text=f"Analysis failed:\n{e.stderr}",
                foreground="red"
            )
        finally:
            self.progress.stop()

    def show_reports(self):
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        reports_frame = ttk.Frame(self.content_area)
        reports_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(reports_frame, text="Historical Reports").pack(anchor=tk.W)
        
        self.report_list = ttk.Treeview(reports_frame, columns=('date', 'score'), show='headings')
        self.report_list.heading('date', text='Date')
        self.report_list.heading('score', text='Average Score')
        self.report_list.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.load_reports()
        
        # 添加 PDF 生成按钮
        ttk.Button(reports_frame, 
                  text="Generate PDF Report", 
                  command=self.generate_pdf_report).pack(pady=10)

    def load_reports(self):
        for item in self.report_list.get_children():
            self.report_list.delete(item)
        
        reports = [
            ("2024-03-01", 4.2),
            ("2024-03-05", 4.5),
            ("2024-03-08", 4.8)
        ]
        for date, score in reports:
            self.report_list.insert('', tk.END, values=(date, score))

    def generate_pdf_report(self):
        try:
            from fpdf import FPDF
            from fpdf.enums import XPos, YPos
            from datetime import datetime
            import os
            
            # 确保输出目录存在
            report_dir = Path("user_reports")
            report_dir.mkdir(exist_ok=True)
            
            # 初始化PDF
            pdf = FPDF()
            pdf.add_page()
            
            # 处理中文字体（需要字体文件）
            font_path = self.get_font_path()
            if not font_path.exists():
                messagebox.showerror("Error", f"Font file not found: {font_path}")
                return
            
            pdf.add_font("NotoSansSC", "", str(font_path), uni=True)
            pdf.set_font("NotoSansSC", "", 14)
            
            # 添加标题
            pdf.cell(200, 10, f"{self.current_user['username']} Collaborative analysis report", 
                    new_x=XPos.LEFT, new_y=YPos.NEXT, align='C')
            
            # 添加基本信息
            pdf.set_font("NotoSansSC", "", 12)
            pdf.cell(200, 10, f"Generated time: {datetime.now().strftime('%Y-%m-%d %H:%M')}", 
                    new_x=XPos.LEFT, new_y=YPos.NEXT)
            pdf.cell(200, 10, f"User role: {self.current_user['role'].capitalize()}", 
                    new_x=XPos.LEFT, new_y=YPos.NEXT)
            pdf.ln(10)
            
            # 生成雷达图
            radar_img = self.generate_radar_chart()
            if radar_img.exists():
                pdf.image(str(radar_img), x=50, w=100)
                pdf.ln(80)
            
            # 生成历史趋势图
            line_img = self.generate_history_chart()
            if line_img.exists():
                pdf.add_page()
                pdf.image(str(line_img), x=25, w=160)
            
            # 保存文件
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = report_dir / f"{self.current_user['username']}_{timestamp}.pdf"
            pdf.output(str(filename))
            
            messagebox.showinfo("Success", f"PDF reports have been generated to:\n{filename}")
            
        except Exception as e:
            messagebox.showerror("Error", f"生成PDF失败: {str(e)}")

    def get_font_path(self):
        # 字体文件路径处理（需要NotoSansSC-Regular.ttf文件）
        font_dir = Path(__file__).parent / "fonts"
        font_dir.mkdir(exist_ok=True)
        return font_dir / "NotoSansSC-Regular.ttf"

    def generate_radar_chart(self):
        # 示例数据，实际应从数据库获取
        scores = {
            'participation': 4.2,
            'initiative': 3.8,
            'problem_solving': 4.5,
            'coordination': 4.0,
            'responsiveness': 3.9
        }
        
        plt.figure(figsize=(6,6))
        categories = list(scores.keys())
        values = list(scores.values())
        
        angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
        values += values[:1]
        angles += angles[:1]
        
        ax = plt.subplot(111, polar=True)
        ax.plot(angles, values)
        ax.fill(angles, values, alpha=0.25)
        plt.xticks(angles[:-1], categories)
        plt.title("Collaborative capability radar chart", pad=20)
        
        img_path = Path("radar_chart.png")
        plt.savefig(img_path, bbox_inches='tight')
        plt.close()
        return img_path

    def generate_history_chart(self):
        # 示例数据（实际应从数据库获取）
        dates = ['2023-01', '2023-02', '2023-03']
        scores = [4.2, 4.5, 4.8]
        
        # 创建画布并设置中文字体
        plt.rcParams['font.sans-serif'] = ['NotoSansSC']  # 确保字体文件存在
        plt.rcParams['axes.unicode_minus'] = False        # 解决负号显示问题
        
        plt.figure(figsize=(10, 6))
        
        # 绘制折线图
        plt.plot(dates, scores, marker='o', linestyle='-', linewidth=2, markersize=8, color='#1890ff')
        
        # 添加图表标题和轴标签
        plt.title("Collaborative capability trend analysis", fontsize=14, pad=20)
        plt.xlabel("date", fontsize=12, labelpad=10)
        plt.ylabel("score", fontsize=12, labelpad=10)
        
        # 设置Y轴范围并添加网格
        plt.ylim(0, 5)
        plt.grid(True, linestyle='--', alpha=0.6)
        
        # 添加数据标签
        for x, y in zip(dates, scores):
            plt.text(x, y + 0.1, f'{y:.1f}', 
                    ha='center', 
                    va='bottom',
                    fontsize=10,
                    color='#2f4f4f')
        
        plt.tight_layout()
        
        # 保存图片
        img_path = Path("history_chart.png")
        plt.savefig(img_path, bbox_inches='tight', dpi=150)
        plt.close()
        
        return img_path

    def show_group_management(self):
        if self.current_user['role'] != 'leader':
            messagebox.showerror("Permission Denied", "Only group leaders can access this feature")
            return
        
        for widget in self.content_area.winfo_children():
            widget.destroy()
        
        group_frame = ttk.Frame(self.content_area)
        group_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(group_frame, text="Group Members").pack(anchor=tk.W)
        
        self.member_list = ttk.Treeview(group_frame, columns=('name', 'role'), show='headings')
        self.member_list.heading('name', text='Username')
        self.member_list.heading('role', text='Role')
        self.member_list.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.load_group_members()
        
        control_frame = ttk.Frame(group_frame)
        control_frame.pack(fill=tk.X)
        
        ttk.Button(control_frame, 
                    text="Refresh List", 
                    command=self.load_group_members).pack(side=tk.LEFT)
        ttk.Button(control_frame, 
                    text="Manage ID Mapping", 
                    command=self.show_id_mapping).pack(side=tk.LEFT, padx=5)

    def load_group_members(self):
        for item in self.member_list.get_children():
            self.member_list.delete(item)
        
        members = [
            ("john_doe", "Leader"),
            ("jane_smith", "Member"),
            ("bob_wilson", "Member")
        ]
        for name, role in members:
            self.member_list.insert('', tk.END, values=(name, role))

    def show_id_mapping(self):
        messagebox.showinfo("Info", "ID mapping management UI")

if __name__ == "__main__":
    root = tk.Tk()
    app = HomePage(root)
    root.mainloop()