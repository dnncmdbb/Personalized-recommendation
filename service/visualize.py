import json
import random
import copy
from pyecharts import options as opts
from pyecharts.charts import Graph, Page
from typing import Dict, List, Any

# --- 全局JS HOST设置 ---
from pyecharts.globals import CurrentConfig
CurrentConfig.ONLINE_HOST = "https://cdn.bootcdn.net/ajax/libs/echarts/5.4.3/"

# --- 配置 ---
JSON_FILE_PATH = "/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/enhanced_knowledge_graph.json"
OUTPUT_HTML_FILE = "knowledge_graph_interactive.html"

# --- 掌握程度颜色映射 ---
MASTERY_COLORS = {
    0: "#CCCCCC",  # 未学过 - 灰色
    1: "#FF6B6B",  # 0-19% - 浅红
    2: "#FFA500",  # 20-39% - 橙色
    3: "#FFD700",  # 40-59% - 金色
    4: "#90EE90",  # 60-79% - 浅绿
    5: "#32CD32"    # 80-100% - 深绿
}

# --- 关系样式定义 (更新为基于掌握程度) ---
RELATION_STYLES = {
    "prerequisite": {"width": 1.8, "type": "solid"},
    "enhances": {"width": 1.2, "type": "solid"},
    "depends_on": {"width": 1.2, "type": "solid"},
    "parallel": {"width": 0.8, "type": "dotted"},
    "excludes": {"width": 0.8, "type": "dashed"},
    "default": {"width": 0.5, "type": "solid"}
}

def load_graph_data(file_path: str) -> Dict:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"成功从 {file_path} 加载了 {len(data.get('nodes', []))} 个节点和 {len(data.get('edges', []))} 条边。")
        return data
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"错误: 加载或解析JSON文件失败: {e}")
        return None

def get_edge_color(source_mastery: int, target_mastery: int) -> str:
    """根据两端节点的掌握程度计算边颜色"""
    avg_mastery = (source_mastery + target_mastery) / 2
    if avg_mastery < 1: return "#CCCCCC"
    elif avg_mastery < 2: return "#FFA07A"
    elif avg_mastery < 3: return "#FFD700"
    elif avg_mastery < 4: return "#98FB98"
    else: return "#32CD32"

def create_interactive_graph(original_graph_data: Dict, sample_nodes_count: int = None):
    graph_data = copy.deepcopy(original_graph_data)
    
    # 抽样逻辑保持不变
    if sample_nodes_count and sample_nodes_count < len(graph_data['nodes']):
        print(f"数据量过大，将随机抽样 {sample_nodes_count} 个节点进行可视化...")
        sampled_nodes = random.sample(graph_data['nodes'], sample_nodes_count)
        sampled_node_names = [node['id'] for node in sampled_nodes]
        sampled_edges = [edge for edge in graph_data['edges'] 
                         if edge[0] in sampled_node_names and edge[2] in sampled_node_names]
        graph_data['nodes'] = [node for node in graph_data['nodes'] if node['id'] in sampled_node_names]
        graph_data['edges'] = sampled_edges
        print(f"抽样后，将可视化 {len(graph_data['nodes'])} 个节点和 {len(graph_data['edges'])} 条边。")

    # --- 节点数据处理 ---
    nodes_data: List[Dict[str, Any]] = []
    node_degrees = {node['id']: 0 for node in graph_data['nodes']}
    node_mastery = {node['id']: node.get('mastery_level', 0) for node in graph_data['nodes']}
    
    # 计算节点度数
    for source, _, target in graph_data['edges']:
        if source in node_degrees: node_degrees[source] += 1
        if target in node_degrees: node_degrees[target] += 1
    
    core_concepts = {"时态和语态": 0, "名词性从句": 1, "非谓语动词": 2, "定语从句": 3, "状语从句": 4}
    
    for node in graph_data['nodes']:
        node_name = node['id']
        degree = node_degrees.get(node_name, 0)
        mastery = node.get('mastery_level', 0)
        
        nodes_data.append({
            "name": node_name,
            "symbolSize": 15 + degree * 0.8,
            "category": core_concepts.get(node_name, 5),
            "itemStyle": {
                "color": MASTERY_COLORS.get(mastery, "#CCCCCC")
            },
            "label": {
                "show": True,
                "fontSize": 10,
                "color": "#333" if mastery > 2 else "#666",
                "fontWeight": "bold" if mastery > 3 else "normal"
            },
            "tooltip": {
                "formatter": f"知识点: {node_name}<br/>掌握程度: {mastery}/5"
            }
        })

    # --- 边数据处理 ---
    edges_data: List[Dict[str, Any]] = []
    for source, rel, target in graph_data['edges']:
        source_mastery = node_mastery.get(source, 0)
        target_mastery = node_mastery.get(target, 0)
        style = RELATION_STYLES.get(rel, RELATION_STYLES["default"])
        
        edges_data.append({
            "source": source,
            "target": target,
            "value": rel, # The relationship type is stored here for tooltip
            "lineStyle": {
                "color": get_edge_color(source_mastery, target_mastery),
                "width": style["width"],
                "type": style["type"],
                "curveness": 0.15,
                "opacity": 0.7
            },
            "tooltip": { # Add tooltip specifically for edges
                "formatter": f"关系: {rel}<br/>{source} --> {target}"
            }
        })

    categories = [
        {"name": "80%～100%", "itemStyle": {"color": MASTERY_COLORS[5]}},
        {"name": "60%～79%", "itemStyle": {"color": MASTERY_COLORS[4]}},
        {"name": "40%～59%", "itemStyle": {"color": MASTERY_COLORS[3]}},
        {"name": "20%～39%", "itemStyle": {"color": MASTERY_COLORS[2]}},
        {"name": "0～19%", "itemStyle": {"color": MASTERY_COLORS[1]}},
        {"name": "无数据", "itemStyle": {"color": MASTERY_COLORS[0]}}
    ]

    graph = Graph(init_opts=opts.InitOpts(
        width="100%",  
        height="95vh",  
        page_title="英语语法知识图谱(带掌握程度)",  
        bg_color="#f7f7f7",
        animation_opts=opts.AnimationOpts(animation=False)
    ))

    graph.add(
        series_name="",
        nodes=nodes_data,
        links=edges_data,
        categories=categories,
        layout="force",
        repulsion=500,
        gravity=0.03,
        edge_length=80,
        label_opts=opts.LabelOpts(is_show=True, position="right"),
        # Set is_show to False to hide edge labels by default
        edge_label=opts.LabelOpts(
            is_show=False, # <-- THIS IS THE KEY CHANGE
            position="middle",
            formatter="{c}", # {c} refers to the 'value' of the edge, which is the relationship type
            font_size=8,
            color="#666"
        ),
        linestyle_opts=opts.LineStyleOpts(width=0.6, opacity=0.7, curve=0.1),
        edge_symbol=["", "arrow"],
        edge_symbol_size=8,
    )

    graph.set_global_opts(
        title_opts=opts.TitleOpts(
            title="英语语法知识图谱(带掌握程度)",  
            subtitle="颜色深浅表示掌握程度 | 拖拽节点交互",
            pos_left="center",  
            pos_top="2%"
        ),
        legend_opts=opts.LegendOpts(
            orient="vertical",  
            pos_left="2%",  
            pos_top="10%",
            item_width=25,
            item_height=14,
            textstyle_opts=opts.TextStyleOpts(font_size=10)
        ),
        tooltip_opts=opts.TooltipOpts(
            trigger="item",
            # This formatter is for nodes by default. Edge tooltips are handled per-edge.
            formatter="{b}<br/>掌握程度: {c}/5" 
        ),
    )

    # Adding edge-specific tooltip is done within the edge data in pyecharts
    # and controlled by the 'tooltip' key in each edge dictionary.
    # The global tooltip_opts will apply to nodes if no specific tooltip is set for them.
    graph.set_series_opts(
        label_opts=opts.LabelOpts(
            position="right",
            color="#333",
            font_size=10,
            formatter="{b}"
        )
    )

    page = Page(layout=Page.SimplePageLayout)
    page.add(graph)
    page.render(OUTPUT_HTML_FILE)

    print(f"\n交互式知识图谱已成功生成: {OUTPUT_HTML_FILE}")

if __name__ == "__main__":
    graph_data = load_graph_data(JSON_FILE_PATH)
    if graph_data:
        NUMBER_OF_NODES_TO_SHOW = 100  # 可调整抽样数量
        create_interactive_graph(graph_data, sample_nodes_count=NUMBER_OF_NODES_TO_SHOW)