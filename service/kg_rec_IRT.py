import sqlite3
import numpy as np
import os

# --- 配置区域 ---
# 数据库文件的路径
DB_PATH = 'student_data.db'
# 您要为其推荐试题的学生ID
STUDENT_ID = 5583697

def calculate_p_theta(a, b, c, theta):
    """
    根据IRT三参数模型计算学生答对某题的概率 P(θ)。
    """
    # 确保所有输入都是有效的浮点数
    try:
        a, b, c, theta = float(a), float(b), float(c), float(theta)
    except (ValueError, TypeError):
        # 如果任何一个参数无法转换（例如为空或None），则返回None
        return None
        
    # 防止指数溢出或分母为零等数学问题
    try:
        exponent = -a * (theta - b)
        probability = c + (1 - c) / (1 + np.exp(exponent))
    except (OverflowError, ZeroDivisionError):
        return None
        
    return probability

def main():
    """
    主执行函数，所有操作均在数据库中完成，并直接读取数值型参数。
    """
    print(f"流程开始：为学生 {STUDENT_ID} 推荐试题 (纯数据库模式, 直接参数)。")
    
    conn = None
    try:
        # --- 步骤 0: 连接数据库 ---
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        print(f"成功连接到数据库: {DB_PATH}")

        # --- 步骤 1: 查找学生掌握程度最低的知识点 ---
        knowledge_table_name = f'kg_{STUDENT_ID}'
        query_min_mastery = f"SELECT MIN(mastery_level) FROM {knowledge_table_name} WHERE mastery_level > 0"
        cursor.execute(query_min_mastery)
        min_mastery_result = cursor.fetchone()
        
        if not min_mastery_result or min_mastery_result[0] is None:
            print(f"错误：在表 '{knowledge_table_name}' 中未找到 mastery_level > 0 的知识点。")
            return
        min_mastery = min_mastery_result[0]

        query_weakest_entities = f"SELECT entity_id FROM {knowledge_table_name} WHERE mastery_level = ?"
        cursor.execute(query_weakest_entities, (min_mastery,))
        weakest_entity_ids = [item[0] for item in cursor.fetchall()]
        
        print(f"\n[步骤 1] 成功: 找到学生最薄弱的知识点ID (掌握度为 {min_mastery:.4f})：")
        print(weakest_entity_ids)

        # --- 步骤 2: 获取用户输入 ---
        chosen_entity_id = None
        while True:
            try:
                user_input = input("\n[步骤 2] 请从以上列表中输入一个您想具体分析的 entity_id: ")
                chosen_entity_id = int(user_input)
                if chosen_entity_id in weakest_entity_ids:
                    break
                else:
                    print("输入错误，请输入上面列表中显示的ID之一。")
            except ValueError:
                print("输入错误，请输入一个有效的数字ID。")

        # --- 步骤 3 & 4: 查找知识点名称和相关试题ID ---
        cursor.execute("SELECT entity_name FROM kg_entity_id WHERE entity_id = ?", (chosen_entity_id,))
        entity_name_result = cursor.fetchone()
        if not entity_name_result:
            print(f"错误：在数据库表 'kg_entity_id' 中未找到ID为 {chosen_entity_id} 的知识点。")
            return
        entity_name = entity_name_result[0]
        print(f"\n[步骤 3] 成功: 您选择的知识点是 '{entity_name}' (ID: {chosen_entity_id})")

        cursor.execute("SELECT DISTINCT question_id FROM question_entity WHERE entity_name = ?", (entity_name,))
        question_ids = [item[0] for item in cursor.fetchall()]
        if not question_ids:
            print(f"提示：在表 'question_entity' 中未找到与知识点 '{entity_name}' 相关的试题。")
            return
        print(f"[步骤 4] 成功: 找到与该知识点相关的试题共 {len(question_ids)} 道。")

        # --- 步骤 5: 获取学生Theta值和所有相关试题的IRT参数 ---
        print("\n[步骤 5] 正在从数据库加载学生能力值(theta)和试题参数...")
        
        # 从 'students' 表中获取学生的Theta值
        cursor.execute("SELECT theta FROM students WHERE `学生ID` = ?", (STUDENT_ID,)) # 注意列名可能有中文
        theta_result = cursor.fetchone()
        if not theta_result:
             print(f"错误：在 'students' 表中未找到学生ID {STUDENT_ID} 的记录。")
             return
        student_theta = theta_result[0]
        print(f"成功: 学生的能力值 (theta) 为 {student_theta:.4f}。")

        # 【核心改动】直接从 'questions' 表中获取 a, b, c 参数
        # 创建SQL占位符 '?,?,?' 用于 'IN' 子句
        placeholders = ','.join(['?'] * len(question_ids))
        query_params = f"""
            SELECT `试题ID`, a_param, b_param, c_param 
            FROM questions 
            WHERE `试题ID` IN ({placeholders})
        """
        cursor.execute(query_params, question_ids)
        question_params_list = cursor.fetchall()
        print(f"成功: 从 'questions' 表中找到了 {len(question_params_list)} 道题的IRT参数。")

        # --- 步骤 6: 计算并输出P(θ) ---
        print("\n[步骤 6] 正在为推荐的试题计算预测答对概率 P(θ)...")
        print("-" * 60)
        print(f"{'试题ID (Question ID)':<30} | {'预测答对概率 P(θ)':<25}")
        print("-" * 60)

        for q_id, a, b, c in question_params_list:
            p_theta = calculate_p_theta(a, b, c, student_theta)
            
            if p_theta is not None:
                print(f"{q_id:<30} | {p_theta:<25.4f}")
            else:
                print(f"{q_id:<30} | 计算失败 (参数: a={a}, b={b}, c={c})")
        
        print("-" * 60)
        print("\n流程结束。")

    except sqlite3.Error as e:
        print(f"\n发生数据库错误: {e}")
        # 如果是操作错误，可能是表名或列名不正确
        if isinstance(e, sqlite3.OperationalError):
            print("提示: 请检查数据库中的表名和列名是否与脚本中的完全一致（包括中文名）。")
    finally:
        if conn:
            conn.close()
            print("\n数据库连接已关闭。")

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print(f"错误：数据库文件 '{DB_PATH}' 不存在。请确保它与脚本在同一目录下。")
    else:
        main()