# home_ui.py
import tkinter as tk
from tkinter import ttk, messagebox
from auth import login_user, get_connection
from database import init_db
from pathlib import Path
import subprocess
import matplotlib.pyplot as plt
from tkinter import filedialog
import sys
import os
import matplotlib.dates as mdates
from datetime import datetime
from collections import defaultdict
import numpy as np
import json
import pandas as pd
from math import pi

os.environ["PYTHONIOENCODING"] = "utf-8" 

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
            
            result = subprocess.run(
                cmd,
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,          # 启用文本模式
                encoding='utf-8',   # 明确指定编码
                errors='replace'    # 替换无效字符
            )
            
            output = result.stdout + result.stderr
            self.preprocess_status.config(
                text=f"Processing completed:\n{output}",
                foreground="green"
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            self.preprocess_status.config(
                text=error_msg,
                foreground="red"
            )

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
            result = subprocess.run(
                cmd, 
                capture_output=True,
                text=True,  # 启用文本模式
                encoding='utf-8',  # 新增编码指定
                errors='replace',  # 替换无法解码的字符
                check=True
            )
            
            # 增强输出处理
            output = f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
            self.analysis_result.config(
                text=f"Analysis completed:\n{output}",
                foreground="green"
            )
            
        except subprocess.CalledProcessError as e:
            error_msg = f"STDOUT:\n{e.stdout}\nSTDERR:\n{e.stderr}"
            self.analysis_result.config(
                text=f"Analysis failed:\n{error_msg}",
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
        
        # 使用更专业的表格列配置
        self.report_list = ttk.Treeview(
            reports_frame, 
            columns=('date', 'participation', 'initiative', 'problem_solving', 'coordination', 'responsiveness', 'average'), 
            show='headings',
            height=10
        )
        
        # 配置专业表头
        columns_config = [
            ('date', '日期', 120),
            ('participation', '参与度', 100),
            ('initiative', '主动性', 100),
            ('problem_solving', '问题解决', 100),
            ('coordination', '协作能力', 100),
            ('responsiveness', '响应速度', 100),
            ('average', '综合评分', 100)
        ]
        
        for col_id, col_text, width in columns_config:
            self.report_list.heading(col_id, text=col_text)
            self.report_list.column(col_id, width=width, anchor='center')
        
        self.report_list.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(reports_frame, orient="vertical", command=self.report_list.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.report_list.configure(yscrollcommand=scrollbar.set)
        
        self.load_reports()
        
        # 专业排版按钮组
        button_frame = ttk.Frame(reports_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, 
                  text="Generate PDF Report", 
                  command=self.generate_pdf_report).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, 
                  text="Refresh Data", 
                  command=self.load_reports).pack(side=tk.LEFT, padx=5)
        
    def load_reports(self):
        """从用户历史文件加载真实数据"""
        for item in self.report_list.get_children():
            self.report_list.delete(item)
        
        try:
            timeline_data = self._load_history_data()
            if not timeline_data:
                messagebox.showwarning("Info", "No historical reports found")
                return
            
            for entry in timeline_data:
                # 格式化显示数据
                values = (
                    entry['date'],
                    f"{entry['scores'].get('participation', 0):.1f}",
                    f"{entry['scores'].get('initiative', 0):.1f}",
                    f"{entry['scores'].get('problem_solving', 0):.1f}",
                    f"{entry['scores'].get('coordination', 0):.1f}",
                    f"{entry['scores'].get('responsiveness', 0):.1f}",
                    f"{entry['average']:.1f}"
                )
                self.report_list.insert('', tk.END, values=values)
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load reports: {str(e)}")

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
        """从数据库加载用户真实数据生成雷达图"""
        try:
            # 获取当前用户的评分数据
            scores = self._get_user_scores()
            if not scores:
                return Path("radar_chart.png")  # 返回空图表

            # 生成雷达图
            plt.rcParams['font.sans-serif'] = ['NotoSansSC']
            plt.rcParams['axes.unicode_minus'] = False
            
            categories = list(scores.keys())
            values = list(scores.values())
            
            angles = np.linspace(0, 2*np.pi, len(categories), endpoint=False).tolist()
            values += values[:1]
            angles += angles[:1]
            
            fig = plt.figure(figsize=(6,6))
            ax = fig.add_subplot(111, polar=True)
            ax.plot(angles, values, linewidth=1, linestyle='solid')
            ax.fill(angles, values, 'b', alpha=0.1)
            plt.xticks(angles[:-1], categories)
            plt.title("协作能力雷达图", pad=20)
            
            img_path = Path("radar_chart.png")
            plt.savefig(img_path, bbox_inches='tight')
            plt.close()
            return img_path
            
        except Exception as e:
            print(f"生成雷达图失败: {str(e)}")
            return Path("radar_chart.png")

    def generate_history_chart(self):
        dates = [datetime.strptime(item['date'], '%Y-%m') for item in timeline_data]
        avg_scores = [item['average'] for item in timeline_data]

        # 2. Create a chart
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.plot(dates, avg_scores, marker='o', linestyle='-')

        # 3. Configure the date coordinate axis
        ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
        fig.autofmt_xdate()

        # 4. Set the title and tags
        ax.set_title("Historical trend of collaborative ability", fontsize=14)
        ax.set_xlabel("data", fontsize=12)
        ax.set_ylabel("average score", fontsize=12)
        ax.set_ylim(0, 5)

        # 5. Add a grid
        ax.grid(True, linestyle='--', alpha=0.6)

        # 6. Mark the values above each point
        for x, y in zip(dates, avg_scores):
            ax.text(x, y + 0.1, f'{y:.1f}', ha='center', va='bottom', fontsize=10)

        # 7. Save and close the chart
        plt.tight_layout()
        plt.savefig(output_path, dpi=300)
        plt.close(fig)

    def _get_user_scores(self):
        """从用户历史记录计算平均分"""
        timeline_data = self._load_history_data()
        if not timeline_data:
            return None
            
        # 按维度聚合数据
        score_dict = defaultdict(list)
        for entry in timeline_data:
            for criterion, score in entry['scores'].items():
                score_dict[criterion].append(score)
                
        # 计算平均分
        return {k: sum(v)/len(v) for k, v in score_dict.items()}

    def _load_history_data(self):
        user_dir = Path("user_progress")
        if not user_dir.exists():
            return []
            
        # Get mappinglralation
        with get_connection() as conn:
            mappings = pd.read_sql(
                "SELECT original_id FROM id_mappings WHERE system_id = ?",
                conn, 
                params=(self.current_user['username'],)
            ).original_id.tolist()
            
        # Traverse all relevant files
        timeline = []
        for file in user_dir.glob("*.json"):
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if data.get('original_id') in mappings:
                        timeline.append({
                            'date': datetime.fromisoformat(data['timestamp']).strftime('%Y-%m'),
                            'scores': data['analysis'].get('scores', {}),
                            'average': sum(data['analysis'].get('scores', {}).values())/5
                        })
            except Exception as e:
                print(f"加载文件 {file.name} 失败: {str(e)}")

        return sorted(timeline, key=lambda x: x['date'])

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
        # 清空当前列表
        for item in self.member_list.get_children():
            self.member_list.delete(item)
        
        try:
            with get_connection() as conn:
                # 获取当前用户的群组信息
                group_name = conn.execute(
                    "SELECT group_name FROM users WHERE username = ?",
                    (self.current_user['username'],)
                ).fetchone()[0]
                
                if not group_name:
                    messagebox.showwarning("Info", "当前未加入任何群组")
                    return

                # 获取群组创建者（Leader）
                creator = conn.execute(
                    "SELECT creator FROM groups WHERE group_name = ?",
                    (group_name,)
                ).fetchone()[0]

                # 获取所有群组成员
                members = conn.execute('''
                    SELECT username, role 
                    FROM users 
                    WHERE group_name = ?
                    ORDER BY role DESC, username
                ''', (group_name,)).fetchall()

                # 构建成员数据（自动识别leader角色）
                processed_members = []
                for username, role in members:
                    # 如果用户是群组创建者，强制设置为Leader
                    actual_role = "Leader" if username == creator else role.capitalize()
                    processed_members.append((username, actual_role))

                # 插入Treeview
                for name, role in processed_members:
                    self.member_list.insert('', tk.END, values=(name, role))

                # 自动更新群组创建者的角色显示
                conn.execute('''
                    UPDATE users 
                    SET role = 'leader' 
                    WHERE username = ? AND role != 'leader'
                ''', (creator,))
                conn.commit()

        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"无法加载群组成员:\n{str(e)}")
        except TypeError:
            messagebox.showwarning("Data Error", "群组信息不完整")
        except Exception as e:
            messagebox.showerror("Error", f"未知错误:\n{str(e)}")

    def show_id_mapping(self):
        """实现完整的ID映射管理界面"""
        if self.current_user['role'] != 'leader':
            messagebox.showerror("权限拒绝", "仅群组管理员可访问此功能")
            return

        # 创建新窗口
        mapping_win = tk.Toplevel(self.root)
        mapping_win.title("ID映射管理")
        mapping_win.geometry("800x600")

        # 主框架
        main_frame = ttk.Frame(mapping_win)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 控制按钮区域
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=5)

        ttk.Button(control_frame, text="刷新", command=self.load_mappings).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="添加映射", command=self.add_mapping).pack(side=tk.LEFT, padx=2)
        ttk.Button(control_frame, text="删除映射", command=self.delete_mapping).pack(side=tk.LEFT, padx=2)

        # 映射列表
        columns = ("原始ID", "系统ID", "群组")
        self.mapping_tree = ttk.Treeview(
            main_frame,
            columns=columns,
            show='headings',
            selectmode='browse'
        )

        # 配置列
        self.mapping_tree.heading("原始ID", text="原始ID", anchor=tk.W)
        self.mapping_tree.heading("系统ID", text="系统ID", anchor=tk.W)
        self.mapping_tree.heading("群组", text="所属群组", anchor=tk.W)
        
        self.mapping_tree.column("原始ID", width=200, minwidth=150)
        self.mapping_tree.column("系统ID", width=200, minwidth=150)
        self.mapping_tree.column("群组", width=150, minwidth=100)

        # 添加滚动条
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.mapping_tree.yview)
        self.mapping_tree.configure(yscrollcommand=scrollbar.set)
        self.mapping_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # 加载初始数据
        self.load_mappings()

    def load_mappings(self):
        """从数据库加载当前群组的映射关系"""
        # 清空现有数据
        for item in self.mapping_tree.get_children():
            self.mapping_tree.delete(item)
        
        try:
            with get_connection() as conn:
                # 获取当前群组
                group_name = conn.execute(
                    "SELECT group_name FROM users WHERE username = ?",
                    (self.current_user['username'],)
                ).fetchone()[0]

                # 查询映射数据
                mappings = conn.execute('''
                    SELECT original_id, system_id, group_name 
                    FROM id_mappings 
                    WHERE group_name = ?
                    ORDER BY original_id
                ''', (group_name,)).fetchall()

                # 插入Treeview
                for mapping in mappings:
                    self.mapping_tree.insert('', tk.END, values=mapping)

        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"无法加载映射数据:\n{str(e)}")
        except Exception as e:
            messagebox.showerror("错误", f"发生未预期错误:\n{str(e)}")

    def add_mapping(self):
        """添加新映射对话框"""
        add_dialog = tk.Toplevel(self.root)
        add_dialog.title("添加映射关系")
        
        ttk.Label(add_dialog, text="原始ID:").grid(row=0, column=0, padx=5, pady=5)
        original_entry = ttk.Entry(add_dialog)
        original_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(add_dialog, text="系统ID:").grid(row=1, column=0, padx=5, pady=5)
        system_entry = ttk.Entry(add_dialog)
        system_entry.grid(row=1, column=1, padx=5, pady=5)

        def save_mapping():
            original_id = original_entry.get().strip()
            system_id = system_entry.get().strip()
            
            if not original_id or not system_id:
                messagebox.showwarning("输入错误", "所有字段必须填写")
                return

            try:
                with get_connection() as conn:
                    # 获取当前群组
                    group_name = conn.execute(
                        "SELECT group_name FROM users WHERE username = ?",
                        (self.current_user['username'],)
                    ).fetchone()[0]

                    # 插入数据库
                    conn.execute('''
                        INSERT INTO id_mappings (original_id, system_id, group_name)
                        VALUES (?, ?, ?)
                        ON CONFLICT(original_id, group_name) 
                        DO UPDATE SET system_id = excluded.system_id
                    ''', (original_id, system_id, group_name))
                    conn.commit()
                    
                    messagebox.showinfo("成功", "映射关系已保存")
                    self.load_mappings()
                    add_dialog.destroy()

            except sqlite3.IntegrityError:
                messagebox.showerror("错误", "系统ID不存在或违反唯一约束")
            except Exception as e:
                messagebox.showerror("错误", f"保存失败: {str(e)}")

        ttk.Button(add_dialog, text="保存", command=save_mapping).grid(row=2, columnspan=2, pady=10)

    def delete_mapping(self):
        """删除选中映射"""
        selected = self.mapping_tree.selection()
        if not selected:
            messagebox.showwarning("选择错误", "请先选择要删除的映射")
            return
        
        item = self.mapping_tree.item(selected[0])
        original_id, system_id, group_name = item['values'][0:3]

        if not messagebox.askyesno("确认删除", f"确定要删除 {original_id} → {system_id} 的映射吗？"):
            return

        try:
            with get_connection() as conn:
                conn.execute('''
                    DELETE FROM id_mappings 
                    WHERE original_id = ? AND group_name = ?
                ''', (original_id, group_name))
                conn.commit()
                
                self.load_mappings()
                messagebox.showinfo("成功", "映射已删除")
                
        except sqlite3.Error as e:
            messagebox.showerror("数据库错误", f"删除失败: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = HomePage(root)
    root.mainloop()