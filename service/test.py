import pandas as pd

# 读取CSV文件
file_path = "/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/random_with_irt_params.csv"
df = pd.read_csv(file_path)

# 获取第7列列名（索引为6）
knowledge_col = df.columns[6]

# 去除知识点名称两侧的引号（处理字符串类型）
df[knowledge_col] = df[knowledge_col].astype(str).str.strip('"')

# 直接覆盖原文件（替换原列）
df.to_csv(file_path, index=False, encoding='utf-8')

print(f"处理完成！已去除知识点名称的引号并覆盖原文件: {file_path}")