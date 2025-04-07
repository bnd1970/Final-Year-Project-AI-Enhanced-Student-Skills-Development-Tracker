# main ui
import os
import sys
import subprocess
import textwrap                          # 格式化文本
import json                              # 处理JSON文件
import pandas as pd

import matplotlib.pyplot as plt
from datetime import datetime

import matplotlib.pyplot as plt
from matplotlib.path import Path
from matplotlib.spines import Spine
from matplotlib.projections.polar import PolarAxes
import numpy as np

from pathlib import Path
from fpdf import FPDF
from pathlib import Path                 # 文件路径操作
from collections import defaultdict      # 用于统计平均分
from database import init_db
from auth import register_user, login_user, get_connection
from analysis_form import COLLAB_CRITERIA, parse_group_from_filename
from datetime import datetime
from fpdf.enums import XPos, YPos
from datetime import datetime

INPUT_DIR = Path("input_form")
OUTPUT_DIR = Path("output_form")
USER_DIR = Path("user_inform")
font_path = "fonts/NotoSansSC-Regular.ttf"

def init_directories():
    INPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_DIR.mkdir(exist_ok=True)
    USER_DIR.mkdir(exist_ok=True)

def auth_module():
    while True:
        print("\n=== User Authentication ===")
        print("1. Login")
        print("2. Register")
        print("3. Exit Program")
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == "1":
            user = login_user()
            if user:
                return user
        elif choice == "2":
            if register_user():
                print("Registration successful!")
            else:
                print("Registration failed. Please try again.")
        elif choice == "3":
            print("\nExiting system...")
            sys.exit(0)
        else:
            print("Invalid selection")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def list_files(directory, extension=".xlsx"):
    return sorted([
        f.name for f in directory.glob(f"*{extension}")
        if f.is_file() and not f.name.startswith('~$')
    ])

def select_file(files, prompt):
    print(prompt)
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    while True:
        try:
            choice = int(input("Enter selection number: "))
            return files[choice-1]
        except (ValueError, IndexError):
            print("Invalid input, please select again")

def preprocess_module():
    clear_screen()
    print("=== Preprocessing Module ===")
    
    input_files = list_files(INPUT_DIR)
    if not input_files:
        input("Input directory is empty, press Enter to return...")
        return
    
    selected = select_file(input_files, "Please select the raw file to process:")
    output_name = input("Enter output filename (without extension): ").strip() + ".xlsx"
    
    cmd = [
        sys.executable, "preprocess_form.py",
        str(INPUT_DIR/selected),
        str(OUTPUT_DIR/output_name)
    ]
    subprocess.run(cmd)
    input("\nProcessing complete, press Enter to return to main menu...")

def analysis_module():
    clear_screen()
    print("=== Analysis Module ===")
    
    output_files = list_files(OUTPUT_DIR)
    if not output_files:
        input("Output directory is empty, press Enter to return...")
        return
    
    selected = select_file(output_files, "Please select the file to analyze:")
    
    cmd = [
        sys.executable, "analysis_form.py",
        "--input", str(OUTPUT_DIR/selected)
    ]
    subprocess.run(cmd)
    input("\nAnalysis complete, press Enter to return to main menu...")

def main_menu():
    init_directories()
    init_db()
    while True:
        clear_screen()
        print("=== Team Collaboration Analysis System ===")
        user_info = auth_module()
        if not user_info:
            continue
            
        while True:
            clear_screen()
            role_display = "Leader" if user_info['role'] == "leader" else "Member"
            print(f"\nCurrent user: {user_info['username']} ({role_display})")
            print("=== Main Menu ===")
            print("1. Preprocess chat files")
            print("2. Analyze collaboration")
            print("3. Generate Personal Summary")
            if user_info['role'] == "leader":
                print("4. Manage groups")
            print("5. Profile settings")
            print("6. Logout")
            print("Type 'exit' to quit system")
            
            choice = input("Enter choice (1-5 or 'exit'): ").strip().lower()
            
            if choice == 'exit':
                print("Exiting system...")
                sys.exit()
            elif choice == "1":
                preprocess_module()
            elif choice == "2":
                analysis_module()
            elif choice == "3":
                generate_personal_summary(user_info)
            elif choice == "4" and user_info['role'] == "leader":
                manage_group_module(user_info)
            elif choice == "5":
                profile_module(user_info)  # 新增的个人设置模块
            elif choice == "6":
                break
            else:
                input("Invalid choice. Press Enter to continue...")

def manage_group_module(user_info):
    while True:
        clear_screen()
        print("=== Group Management ===")
        print("1. View members")
        print("2. Manage ID mapping")
        print("3. Return")
        choice = input("Enter choice (1-3): ")
        
        if choice == '1':
            from auth import get_available_groups  # 新增导入
            print(f"Current group: {user_info['group']}")
            print("\nMember List:")
            
            # 从数据库获取成员信息
            with get_connection() as conn:
                members = pd.read_sql('''
                    SELECT username, role 
                    FROM users 
                    WHERE group_name = ?
                ''', conn, params=(user_info['group'],))
                
            print(members.to_string(index=False))
            input("\nPress Enter to return...")
        elif choice == '2':
            from auth import update_user_mapping
            update_user_mapping(user_info['group'])  # 进入新界面
        elif choice == '3':
            break
        else:
            print("Invalid selection")
        input("\nPress Enter to continue...")

def profile_module(user_info):
    while True:
        clear_screen()
        print("=== Profile Management ===")
        print(f"Username: {user_info['username']}")
        print(f"Role: {user_info['role'].capitalize()}")
        print(f"Group: {user_info['group']}")
        
        print("\n1. Change password")
        print("2. Manage group")
        print("3. Return to main menu")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            new_pw = input("Enter new password: ").strip()
            if new_pw:
                from auth import hash_password, update_user_info
                success = update_user_info(user_info['username'], 
                    {'password_hash': hash_password(new_pw)}
                )
                print("Password updated!" if success else "Update failed!")
            input("Press Enter to continue...")
        
        elif choice == '2':
            if user_info['role'] == 'member':
                member_group_operations(user_info)
            else:
                leader_group_operations(user_info)
        
        elif choice == '3':
            break

def member_group_operations(user_info):
    """组员的小组操作"""
    from auth import get_available_groups, update_user_info
    
    while True:
        clear_screen()
        print("=== Group Operations ===")
        print("Current group:", user_info['group'])
        print("1. Join a group")
        print("2. Leave group")
        print("3. Return")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            groups = get_available_groups()
            if groups.empty:
                print("No available groups!")
                input()
                continue
                
            print("Available groups:")
            print(groups[['group_name', 'creator']].to_string(index=False))
            group_name = input("Enter group name to join: ").strip()
            
            if group_name in groups['group_name'].values:
                if update_user_info(user_info['username'], {'group': group_name}):
                    print("Successfully joined group!")
                    user_info['group'] = group_name
                else:
                    print("Failed to join group!")
            else:
                print("Invalid group name!")
            input()
        
        elif choice == '2':
            if update_user_info(user_info['username'], {'group': ''}):
                print("Left group successfully!")
                user_info['group'] = ''
            else:
                print("Failed to leave group!")
            input()
        
        elif choice == '3':
            break

def leader_group_operations(user_info):
    """组长的小组操作"""
    from auth import get_connection  # 新增导入
    
    while True:
        clear_screen()
        print("=== Leader Operations ===")
        print("1. Transfer leadership")
        print("2. Leave group")
        print("3. Return")
        
        choice = input("Enter choice (1-3): ").strip()
        
        if choice == '1':
            try:
                with get_connection() as conn:
                    # 从数据库获取成员列表
                    members = pd.read_sql('''
                        SELECT username, role 
                        FROM users 
                        WHERE group_name = ? 
                        AND username != ?
                    ''', conn, params=(user_info['group'], user_info['username']))
                    
                    if members.empty:
                        print("没有可转让权限的成员！")
                        input()
                        continue
                        
                    print("选择新组长:")
                    print(members.to_string(index=False))
                    new_leader = input("输入用户名: ").strip()
                    
                    # 验证用户名有效性
                    if new_leader not in members['username'].values:
                        print("无效的用户名！")
                        input()
                        continue
                        
                    # 执行权限转移
                    from auth import transfer_leadership
                    if transfer_leadership(user_info['username'], new_leader, user_info['group']):
                        print("组长权限已成功转移！")
                        user_info['role'] = 'member'
                        return
                    else:
                        print("权限转移失败！")
                    input()
            
            except sqlite3.Error as e:
                print(f"数据库错误: {str(e)}")
                input()
        
        elif choice == '2':
            try:
                with get_connection() as conn:
                    # 检查是否还有其他成员
                    count = conn.execute('''
                        SELECT COUNT(*) 
                        FROM users 
                        WHERE group_name = ?
                    ''', (user_info['group'],)).fetchone()[0]
                    
                    if count > 1:
                        print("转让组长权限后才能退出群组！")
                    else:
                        from auth import update_user_info
                        if update_user_info(user_info['username'], {'group_name': ''}):
                            print("已成功退出群组！")
                            user_info['group'] = ''
                        else:
                            print("退出群组失败！")
                    input()
            
            except sqlite3.Error as e:
                print(f"数据库错误: {str(e)}")
                input()
        
        elif choice == '3':
            break

def generate_radar_chart(scores: dict) -> str:
    """生成雷达图并返回图片路径"""
    # 数据准备
    criteria = list(COLLAB_CRITERIA.values())
    values = [scores.get(k, 0) for k in COLLAB_CRITERIA.keys()]
    angles = np.linspace(0, 2*np.pi, len(criteria), endpoint=False).tolist()
    values += values[:1]  # 闭合图形
    angles += angles[:1]

    # 绘图配置
    fig = plt.figure(figsize=(6,6))
    ax = fig.add_subplot(111, polar=True)
    ax.plot(angles, values, linewidth=1, linestyle='solid')
    ax.fill(angles, values, 'b', alpha=0.1)
    ax.set_theta_offset(np.pi/2)
    ax.set_theta_direction(-1)
    ax.set_rlabel_position(0)
    plt.xticks(angles[:-1], criteria)
    plt.ylim(0,5)

    # 保存图片
    img_path = "radar_chart.png"
    plt.savefig(img_path, bbox_inches='tight')
    plt.close()
    return img_path

def generate_history_line_chart(timeline_data):
    """生成历史得分折线图"""
    plt.figure(figsize=(8, 4))
    
    # 转换时间戳为日期对象
    dates = [datetime.strptime(entry['date'], "%Y-%m-%d") for entry in timeline_data]
    dates_str = [d.strftime("%m-%d") for d in dates]  # 仅显示月-日
    
    # 绘制每个维度的折线
    for criterion in COLLAB_CRITERIA.keys():
        scores = [entry['scores'].get(criterion, 0) for entry in timeline_data]
        plt.plot(dates_str, scores, marker='o', label=COLLAB_CRITERIA[criterion])
    
    plt.title("历史能力得分趋势")
    plt.xlabel("日期")
    plt.ylabel("得分")
    plt.ylim(0, 5)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.tight_layout()
    
    # 保存图片
    chart_path = "history_line_chart.png"
    plt.savefig(chart_path, bbox_inches='tight')
    plt.close()
    return chart_path

def generate_personal_summary(user_info):

    def validate_report_data(data: dict) -> bool:
        """弹性字段验证"""
        required = {
            "0.5.0": ['scores', 'feedback'],
            "0.2.0": ['feedback']
        }
        version = data.get('schema_version', '0.2.0')
        min_fields = required.get(version.split('.')[0]+'.'+version.split('.')[1], [])
        return all(k in data.get('analysis', {}) for k in min_fields)

    def parse_historical_scores(analysis_data: dict) -> dict:
        """支持嵌套evaluation字段并强制转换评分值为浮点数"""
        scores = {}

        # 旧版结构（直接使用scores字段）
        if "scores" in analysis_data:
            raw_scores = analysis_data["scores"]
        # 新版结构（使用evaluation字段）
        elif "evaluation" in analysis_data:
            raw_scores = analysis_data["evaluation"]
            # 将comments字段映射到feedback（如果存在）
            raw_scores["feedback"] = raw_scores.get("comments", "")
        else:
            return {}

        # 字段名标准化（根据实际需求调整）
        key_mapping = {
            "problem_solving": "problem_solving",  # 如果字段名需要更改（如下划线转连字符）
            "response_time": "responsiveness"       # 示例：旧版字段名到新版字段名的映射
        }

        # 强制转换评分值为浮点数，并处理异常值
        for key, value in raw_scores.items():
            # 跳过非评分字段（如feedback）
            if key not in COLLAB_CRITERIA and key != "feedback":
                continue

            # 字段名标准化
            mapped_key = key_mapping.get(key, key)
            try:
                # 尝试转换为浮点数（处理字符串或无效类型）
                scores[mapped_key] = float(value)
            except (ValueError, TypeError):
                # 记录警告并设置默认值0.0
                print(f"警告：字段 {key} 的值 {value} 无效，已设为0分")
                scores[mapped_key] = 0.0

        return scores

    clear_screen()
    print("=== 个人成长报告生成 ===")
    
    try:
        # ================== 1. 获取用户所有关联的原始ID ==================
        with get_connection() as conn:
            # 查询所有关联的原始ID（包括跨群组）
            mapping_df = pd.read_sql('''
                SELECT original_id, group_name 
                FROM id_mappings 
                WHERE system_id = ?
            ''', conn, params=(user_info['username'],))
            
            if mapping_df.empty:
                # 新增友好提示和操作引导
                print("提示：您尚未建立ID映射关系，请按以下步骤操作：")
                print("1. 组长进入群组管理 → 管理ID映射 → 添加映射")
                print("2. 确保分析文件中的原始ID与系统ID正确关联")
                input("\n按回车返回主菜单...")
                return
                
            # 提取所有原始ID（去重）
            original_ids = mapping_df['original_id'].unique().tolist()

        # ================== 2. 加载所有关联的历史报告文件 ==================
        report_dir = Path("user_progress")
        report_files = []
        for oid in original_ids:
            # 匹配格式如 fengyuantong_*.json 的所有文件
            report_files += list(report_dir.glob(f"{oid}_*.json"))
        
        if not report_files:
            input("未找到历史分析记录，按回车返回...")
            return

        # ================== 3. 解析并合并报告数据 ==================
        all_data = []
        for report_file in sorted(report_files, key=lambda x: x.stem.split('_')[-1], reverse=True):
            try:
                with open(report_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                    if not validate_report_data(data):
                        print(f"警告：文件 {report_file.name} 结构不兼容")
                        continue

                    # 调试：打印原始数据类型
                    print(f"\n[调试] 加载文件: {report_file.name}")
                    print("原始数据字段类型:")
                    if 'scores' in data.get('analysis', {}):
                        for k, v in data['analysis']['scores'].items():
                            print(f"  {k}: {type(v)}")
                    elif 'evaluation' in data.get('analysis', {}):
                        for k, v in data['analysis']['evaluation'].items():
                            print(f"  {k}: {type(v)}")

                    # 数据处理逻辑
                    processed = {
                        "messages_count": int(data.get("messages_count", 0)),  # 强制转换为整数
                        "analysis": {
                            "scores": parse_historical_scores(data.get('analysis', {})),
                            "feedback": data.get('analysis', {}).get('feedback', '')
                        },
                        "timestamp": data.get('timestamp', '1970-01-01'),
                        "original_id": data.get('talker', 'unknown'),
                        "group": data.get('group', parse_group_from_filename(str(report_file)))
                    }

                    # 添加异常处理
                    try:
                        processed["messages_count"] = int(processed["messages_count"])
                    except (ValueError, TypeError):
                        print(f"警告：文件 {report_file.name} 的 messages_count 字段无效，已设为0")
                        processed["messages_count"] = 0

                    # 有效性检查（新增总分验证）
                    total_score = sum(processed['analysis']['scores'].values())
                    if total_score <= 0 and not processed['analysis']['feedback']:
                        print(f"跳过无效记录：{report_file.name}（总分={total_score}）")
                        continue
                        
                    all_data.append(processed)
                    print(f"✓ 已加载 {report_file.name} [v{data.get('schema_version','?')}]")

            except Exception as e:
                print(f"加载报告文件 {report_file.name} 失败: {str(e)}")
                continue

        # ================== 4. 生成统计摘要 ==================

        valid_reports = [
            d for d in all_data 
            if any(d['analysis'].values())  # 只要存在任意有效字段
            or d.get('feedback', '').strip() != ''
        ]
        if not valid_reports:
            input("\n所有报告均为无效记录，按回车返回...")
            return

        summary = {
            "user_id": user_info['username'],
            "total_reports": len(all_data),
            "average_scores": defaultdict(float),
            "feedback_history": [],
            "timeline": [],
            "groups": list(mapping_df['group_name'].unique())  # 新增群组信息
        }

        # 计算各维度平均分（跨群组合并）
        for criterion in COLLAB_CRITERIA.keys():
            valid_scores = [
                d['analysis']['scores'].get(criterion, 0) 
                for d in all_data 
                if 'scores' in d['analysis']  # 新增检查
            ]
            if valid_scores:
                summary['average_scores'][criterion] = sum(valid_scores) / len(valid_scores)
            else:
                summary['average_scores'][criterion] = 0.0

        # 收集时间线数据（按时间倒序）
        for report in sorted(all_data, key=lambda x: x['timestamp'], reverse=True):
            try:
                summary['feedback_history'].append(report['analysis'].get('feedback', ''))
                summary['timeline'].append({
                    'date': report['timestamp'][:10],
                    'scores': report['analysis']['scores'],
                    'original_id': report['original_id'],
                    'group': report['group']
                })
            except KeyError:
                continue

        # ================== 5. 显示增强版报告 ==================
        print(f"\n=== {user_info['username']} 个人成长总结 ===")
        print(f"关联群组: {', '.join(summary['groups'])}")
        print(f"分析报告总数: {summary['total_reports']}")
        
        print("\n平均能力得分（跨群组）:")
        for criterion, score in summary['average_scores'].items():
            print(f"  {COLLAB_CRITERIA[criterion]}: {score:.1f}/5")
        
        print("\n历史反馈摘要（最近3次，按时间倒序）:")
        for i, entry in enumerate(summary['timeline'][:3], 1):
            print(f"\n第{i}次反馈（{entry['date']}）:")
            print(f"  原始ID: {entry['original_id']}")
            print(f"  所属群组: {entry['group']}")
            print(textwrap.fill(summary['feedback_history'][i-1], width=80, subsequent_indent='    '))

        # ================== 6. 报告历史信息 ==================
        print("\n=== 详细报告预览 ===")
        input("按回车查看第一份报告...")
        
        for idx, report in enumerate(all_data, 1):
            try:
                print(f"=== 报告 {idx}/{len(all_data)} ===")
                print(f"生成时间: {report['timestamp']}")
                print(f"原始ID: {report['original_id']}")
                print(f"所属群组: {report['group']}")
                print(f"消息数量: {report['messages_count']}")
                
                # 显示评分
                print("\n技能评分:")
                for criterion, score in report['analysis']['scores'].items():
                    print(f"  {COLLAB_CRITERIA[criterion]}: {score}/5")
                
                # 显示详细反馈（自动换行）
                print("\n详细反馈:")
                print(textwrap.fill(report['analysis'].get('feedback', '无可用反馈'), width=80))
            
                # 分页控制
                if idx < len(all_data):
                    choice = input("\n输入 'n' 查看下一份，其他键退出预览: ").strip().lower()
                    if choice != 'n':
                        break

                if 'scores' in report['analysis']:
                    print("\n技能评分:")
                    for criterion, score in report['analysis']['scores'].items():
                        print(f"  {COLLAB_CRITERIA[criterion]}: {score}/5")
                else:
                    print("\n警告：此报告缺少评分数据")
                    
            except KeyError as e:
                print(f"\n数据损坏：无法解析报告 {report_file.name} ({str(e)})")

        # ================== 7. 更新PDF报告生成 ==================
        if input("\n生成PDF报告？(y/n): ").lower() == 'y':
            generate_pdf_report(summary, user_info)

    except Exception as e:
        print(f"生成报告时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    input("\n按回车返回主菜单...")

def generate_pdf_report(summary, user_info):

    font_path = "fonts/NotoSansSC-Regular.ttf"
    if not Path(font_path).exists():
        raise FileNotFoundError(f"中文字体文件 {font_path} 未找到")
    
    # 生成折线图
    if len(summary['timeline']) >= 1:
        try:
            line_chart_path = generate_history_line_chart(summary['timeline'])
            pdf.add_page()
            pdf.set_font("NotoSansSC", "", 16)
            pdf.cell(200, 10, text="历史能力得分趋势", new_x=XPos.LEFT, new_y=YPos.NEXT, align='C')
            pdf.image(line_chart_path, x=25, w=160)
        except Exception as e:
            print(f"折线图生成失败: {str(e)}")

    # 生成雷达图
    try:
        chart_path = generate_radar_chart(summary['average_scores'])
    except Exception as e:
        print(f"雷达图生成失败: {str(e)}")
        chart_path = None

    if not Path(font_path).exists():
        raise FileNotFoundError(f"字体文件 {font_path} 未找到")

    # 创建PDF
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font("NotoSansSC", "", font_path)
    pdf.set_font("NotoSansSC", "", 12)  # 必须放在内容生成前
    
    # 标题
    pdf.cell(200, 10, text=f"{user_info['username']} 个人成长报告", new_x=XPos.LEFT, new_y=YPos.NEXT, align='C')
    
    # 基本信息
    pdf.cell(200, 10, text=f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}", new_x=XPos.LEFT, new_y=YPos.NEXT)
    pdf.cell(200, 10, text=f"分析报告总数: {summary['total_reports']}", new_x=XPos.LEFT, new_y=YPos.NEXT)
    
    # 能力雷达图
    pdf.image(generate_radar_chart(summary['average_scores']), x=25, w=150)
    
    # 详细分数
    pdf.add_page()
    pdf.cell(200, 10, text="维度平均得分:", new_x=XPos.LEFT, new_y=YPos.NEXT)
    for criterion, score in summary['average_scores'].items():
        pdf.cell(200, 10, text=f"- {COLLAB_CRITERIA[criterion]}: {score}/5", new_x=XPos.LEFT, new_y=YPos.NEXT)
    
    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"user_reports/{user_info['username']}_{timestamp}_summary.pdf"
    pdf.output(filename)
    print(f"PDF 报告已生成至: {filename}")

def get_id_mapping():
    try:
        mapping_path = Path(__file__).parent / "user_inform/user_mapping.xlsx"
        mapping_df = pd.read_excel(mapping_path, engine='openpyxl')
        return mapping_df.set_index('original_id')['system_id'].to_dict()
    except FileNotFoundError:
        return {}

if __name__ == "__main__":
    OUTPUT_DIR.mkdir(exist_ok=True)
    main_menu()