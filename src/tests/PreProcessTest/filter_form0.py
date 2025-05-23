# save_as: preprocess_chat.py
import pandas as pd
import re
import sys
from datetime import datetime

def validate_input_file(input_path):
    try:
        with open(input_path, 'rb') as f:
            pass
        return True
    except FileNotFoundError:
        print(f"错误：输入文件 {input_path} 不存在")
        return False
    except Exception as e:
        print(f"文件访问错误: {str(e)}")
        return False

def clean_message(msg):
    if pd.isna(msg):
        return ""
    # 清理HTML标签
    msg = re.sub(r'<.*?>', '', str(msg))
    # 清理URL（保留文字描述）
    msg = re.sub(r'http\S+', '[链接]', msg)
    # 清理文件路径
    msg = re.sub(r'FileStorage\\\S+', '[文件]', msg)
    # 去除首尾空白
    return msg.strip()

def main(input_path="input_form/test5.xlsx", output_path="output_form/cleaned_chat.xlsx"):
    if not validate_input_file(input_path):
        sys.exit(1)
        
    try:
        # 读取原始数据并转换为字符串类型）
        df = pd.read_excel(
            input_path,
            sheet_name="44778409919@chatroom_0_284",
            dtype=str,
            keep_default_na=False
        )
        
        # 列处理
        essential_columns = ['id', 'CreateTime', 'talker', 'type_name', 'msg']
        df = df[essential_columns]
        
        # 过滤无效消息类型
        valid_types = ['文本', '文件', '引用回复', '图片']
        df = df[df['type_name'].isin(valid_types)]
        
        # 数据清洗
        df['msg'] = df['msg'].apply(clean_message)
        df['CreateTime'] = pd.to_datetime(df['CreateTime'], errors='coerce')
        
        # 删除空消息和时间无效的记录
        df = df[(df['msg'] != '') & (df['CreateTime'].notna())]
        
        # 生成输出文件
        df.to_excel(output_path, index=False, engine='openpyxl')
        print(f"成功处理 {len(df)} 条记录")
        print(f"输出文件已保存至: {output_path}")
        
    except Exception as e:
        print(f"处理过程中发生错误: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    # 使用示例（支持命令行参数）
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        main()