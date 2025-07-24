import pandas as pd
from dotenv import load_dotenv
import os

# 加载.env文件
load_dotenv()

# 从环境变量获取文件路径
file_path = os.getenv("EMBEDDING_MODEL_PATH")
if not file_path:
    raise ValueError("EMBEDDING_MODEL_PATH 未在.env文件中设置")

# 读取数据（强制指定学生ID为字符串类型）
if file_path.endswith('.xlsx'):
    df = pd.read_excel(file_path, dtype={'学生ID': str})
elif file_path.endswith('.csv'):
    df = pd.read_csv(file_path, dtype={'学生ID': str})
else:
    raise ValueError("文件格式不支持，请使用.xlsx或.csv文件")

# 定义列位置
student_col = '学生ID'
knowledge_col = df.columns[6]
result_col = df.columns[11]

# 输入处理
target_student = input("请输入要分析的学生ID: ").strip()

# 安全查询（统一字符串类型比较）
student_data = df[df[student_col].astype(str).str.strip() == target_student].copy()  # 显式创建副本

if student_data.empty:
    print(f"未找到学生 {target_student} 的记录")
    exit()

# 预处理知识点列（使用.loc避免警告）
student_data.loc[:, knowledge_col] = student_data[knowledge_col].astype(str).str.strip('"')
student_data.loc[:, 'knowledge_split'] = student_data[knowledge_col].str.split(',')

# 展开多知识点
expanded_data = student_data.explode('knowledge_split')

# 计算掌握程度（修复NaN处理）
def calculate_mastery(df):
    stats = df.groupby('knowledge_split')[result_col].agg(
        total='count',
        correct=lambda x: (x == 1).sum(),
        half_correct=lambda x: (x == 0).sum()
    )
    
    stats['correct_rate'] = (stats['correct'] + stats['half_correct'] * 0.5) / stats['total']
    
    # 关键修复：先填充NaN再分级
    stats['mastery_level'] = pd.cut(
        stats['correct_rate'].fillna(-1),  # 填充NaN
        bins=[-1, 0.19, 0.39, 0.59, 0.79, 1],
        labels=[1, 2, 3, 4, 5],
        right=True
    ).astype(int)
    
    return stats[['correct_rate', 'mastery_level']]

# 计算并保存结果
mastery_df = calculate_mastery(expanded_data)
mastery_df.reset_index(inplace=True)
mastery_df.rename(columns={'knowledge_split': 'knowledge_point'}, inplace=True)

output_path = os.path.join(os.path.dirname(file_path), f"student_{target_student}_knowledge_mastery.csv")
mastery_df[['knowledge_point', 'mastery_level']].to_csv(output_path, index=False)

print(f"分析完成！结果已保存至: {output_path}")
print(mastery_df[['knowledge_point', 'mastery_level']])