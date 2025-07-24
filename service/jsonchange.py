import json
import pandas as pd
from dotenv import load_dotenv

# 加载.env文件
load_dotenv()

# 文件路径
mastery_csv = "/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/student_5583697_knowledge_mastery.csv"
knowledge_graph_json = "/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/knowledge_graph.json"
output_json = "/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/enhanced_knowledge_graph.json"

# 1. 读取学生掌握程度数据
mastery_df = pd.read_csv(mastery_csv)
# 去除NaN值
mastery_df = mastery_df.dropna(subset=['knowledge_point'])
# 创建知识点到掌握程度的映射字典
mastery_dict = dict(zip(mastery_df['knowledge_point'], mastery_df['mastery_level']))

# 2. 读取原始知识图谱
with open(knowledge_graph_json, 'r', encoding='utf-8') as f:
    kg = json.load(f)

# 3. 增强知识图谱数据
enhanced_nodes = []
for node in kg['nodes']:
    # 为每个节点添加mastery_level属性
    enhanced_node = {
        "id": node,
        "mastery_level": int(mastery_dict.get(node, 0))  # 默认0表示未学习
    }
    enhanced_nodes.append(enhanced_node)

# 4. 构建增强后的知识图谱
enhanced_kg = {
    "nodes": enhanced_nodes,
    "edges": kg['edges']  # 保留原始关系
}

# 5. 保存结果
with open(output_json, 'w', encoding='utf-8') as f:
    json.dump(enhanced_kg, f, ensure_ascii=False, indent=2)

print(f"增强后的知识图谱已保存至: {output_json}")