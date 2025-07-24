# llm_question_analyzer.py
import sqlite3
from openai import OpenAI
import os
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

class QuestionAnalyzer:
    def __init__(self):
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        load_dotenv()
        self.embedding_model = SentenceTransformer(os.getenv("EMBEDDING_MODEL_PATH"))
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
        self.db_path = "/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/student_data.db"

    def get_top3_knowledge_points(self, question):
        """从数据库获取最匹配的3个知识点"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # 获取所有知识点
        cursor.execute("SELECT entity_name FROM kg_entity_id")
        knowledge_points = [row[0] for row in cursor.fetchall()]
        
        # 计算相似度
        question_embedding = self.embedding_model.encode(question)
        point_embeddings = self.embedding_model.encode(knowledge_points)
        similarities = cosine_similarity([question_embedding], point_embeddings)[0]
        
        # 取TOP3
        top3_indices = similarities.argsort()[-3:][::-1]
        return [knowledge_points[i] for i in top3_indices]

    def analyze_question(self, question):
        """分析题目并返回知识点"""
        top3_points = self.get_top3_knowledge_points(question)
        
        prompt = f"""
            请完成以下英语题目分析任务：
            
            1. 请严格从以下候选知识点中选择1-3个最相关的知识点，不要自行发明知识点：
            候选知识点：{", ".join(top3_points)}
            
            2. 词汇考察判断：
            识别题目中重点考察的词汇（如有）
            
            3. 最终输出格式要求：
            知识点1, 知识点2, 知识点3; 考察词汇/固定搭配
            
            示例：
            题目："When she found her daughter was running a high fever, she（） took her to hospital.	A: promptly    B: consequently C: consistently  D: provokingly"
            输出：
            副词的辨析,词汇及语法结构（单选题）,形容词、副词及其比较等级; promptly
            
            题目："George is delighted ______ his new secretary because she works very hard.	A: to  B: with  C: of  D: at"
            输出：
            词汇及语法结构（单选题）,连词、介词及介词短语,介词的搭配; with


            待分析题目：「{question}」
            """
        
        try:
            response = self.client.chat.completions.create(
                model="qwen3-32b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                extra_body={"enable_thinking": False}
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"API调用失败: {str(e)}")
            return None