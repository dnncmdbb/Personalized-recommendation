# TFIDF_search_engine.py
import pandas as pd
import sqlite3
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import string
import os


class QuestionSearchEngine:
    def __init__(self, db_path, index_file, vectorizer_file, nltk_data_path):
        """初始化搜索引擎。

        Args:
            db_path (str): SQLite 数据库文件路径。
            index_file (str): TF-IDF 索引保存路径。
            vectorizer_file (str): TF-IDF 向量化器保存路径。
            nltk_data_path (str, optional): NLTK 数据目录路径。如果提供，将添加到 NLTK 数据路径。
        """
        self.db_path = db_path
        self.index_file = index_file
        self.vectorizer_file = vectorizer_file
        self.nltk_data_path = nltk_data_path  # 保存 nltk_data_path 为实例属性
        self._ensure_nltk_resources()  # 检查并配置 NLTK 资源
        # 其他初始化代码...

    def _ensure_nltk_resources(self):
        """检查并确保必要的 NLTK 资源（punkt_tab, stopwords, wordnet）。"""
        # 如果提供了 nltk_data_path，添加到 NLTK 数据路径
        if self.nltk_data_path and self.nltk_data_path not in nltk.data.path:
            nltk.data.path.append(self.nltk_data_path)
            print(f"已添加 NLTK 数据路径: {self.nltk_data_path}")

        required_resources = ['punkt_tab', 'stopwords', 'wordnet']
        for resource in required_resources:
            if resource == 'wordnet':
                # 特别处理 wordnet，检查 wordnet.zip 是否存在
                wordnet_zip_path = os.path.join(self.nltk_data_path, 'corpora', 'wordnet.zip')
                if os.path.exists(wordnet_zip_path):
                    print(f"NLTK 资源 wordnet.zip 已存在于 {wordnet_zip_path}，无需下载。")
                    continue  # 跳过下载
            else:
                # 检查其他资源（punkt_tab, stopwords）
                resource_path = f'tokenizers/{resource}' if resource == 'punkt_tab' else f'corpora/{resource}'
                try:
                    nltk.data.find(resource_path)
                    print(f"NLTK 资源 {resource} 已存在于 {self.nltk_data_path}，无需下载。")
                    continue  # 跳过下载
                except LookupError:
                    pass  # 继续执行下载逻辑

            # 如果资源不存在，下载到指定路径
            if self.nltk_data_path:
                print(f"下载 NLTK 资源: {resource} 到 {self.nltk_data_path}...")
                nltk.download(resource, download_dir=self.nltk_data_path)
            else:
                print(f"未提供 nltk_data_path，下载 NLTK 资源 {resource} 到默认路径...")
                nltk.download(resource)

    def read_questions(self):
        """从数据库读取题目和知识点。

        Returns:
            tuple: (questions_data, original_questions)
                - questions_data: 字典，{qid: 合并文本}，包含题干、元信息、父题干和知识点。
                - original_questions: 列表，仅包含原始题干。
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        query = """
        SELECT e.question_id, e.stem, e.metas, e.parent_id, q.knowledge_point_name
        FROM english_questions e
        LEFT JOIN questions q ON e.question_id = q.question_parent_id
        """
        df = pd.read_sql_query(query, conn)
        
        combined_questions = []
        original_questions = []
        
        for _, row in df.iterrows():
            question_id = row['question_id']
            stem = row['stem'] if pd.notna(row['stem']) else ""
            metas = row['metas'] if pd.notna(row['metas']) else ""
            parent_id = row['parent_id'] if pd.notna(row['parent_id']) else 0
            knowledge_point = row['knowledge_point_name'] if pd.notna(row['knowledge_point_name']) else ""
            
            parent_stem = ""
            if parent_id != 0:
                cursor.execute("SELECT stem FROM parent_questions WHERE parent_id = ?", (parent_id,))
                parent_result = cursor.fetchone()
                parent_stem = parent_result[0] if parent_result and pd.notna(parent_result[0]) else ""
            
            combined_text = f"{stem} {metas} {parent_stem} {knowledge_point}".strip()
            combined_questions.append(combined_text)
            original_questions.append(stem)
            
        conn.close()
        
        return {f"q{i}": q for i, q in enumerate(combined_questions)}, original_questions
    
    def preprocess_text(self, text):
        """预处理文本，清洗和规范化以用于 TF-IDF 向量化。

        Args:
            text (str): 输入文本。

        Returns:
            str: 预处理后的文本。
        """
        text = text.lower()
        words = word_tokenize(text)
        words = [word for word in words if word not in string.punctuation and not word.isdigit()]
        stop_words = set(stopwords.words('english'))
        words = [word for word in words if word not in stop_words]
        lemmatizer = WordNetLemmatizer()
        words = [lemmatizer.lemmatize(word) for word in words]
        words = [word for word in words if len(word) > 2]
        return ' '.join(words)
    
    def preprocess_questions(self, questions_data):
        """批量预处理题目数据。

        Args:
            questions_data (dict): {qid: 合并文本} 的字典。

        Returns:
            dict: {qid: 预处理文本} 的字典。
        """
        processed_data = {}
        for qid, question in questions_data.items():
            processed_data[qid] = self.preprocess_text(question)
        return processed_data
    
    def create_tfidf_index(self, processed_data):
        """创建 TF-IDF 索引和向量化器。

        Args:
            processed_data (dict): 预处理后的题目数据。

        Returns:
            tuple: (TF-IDF 矩阵, TfidfVectorizer 对象)。
        """
        vectorizer = TfidfVectorizer()
        corpus = list(processed_data.values())
        X = vectorizer.fit_transform(corpus)
        return X, vectorizer
    
    def save_index(self, index, vectorizer):
        """保存 TF-IDF 索引和向量化器到磁盘。

        Args:
            index: TF-IDF 矩阵。
            vectorizer: TfidfVectorizer 对象。
        """
        with open(self.index_file, 'wb') as f:
            pickle.dump(index, f)
        with open(self.vectorizer_file, 'wb') as f:
            pickle.dump(vectorizer, f)
    
    def load_index(self):
        """从磁盘加载 TF-IDF 索引和向量化器。

        Returns:
            tuple: (TF-IDF 矩阵, TfidfVectorizer 对象)。
        """
        with open(self.index_file, 'rb') as f:
            index = pickle.load(f)
        with open(self.vectorizer_file, 'rb') as f:
            vectorizer = pickle.load(f)
        return index, vectorizer
    
    def search_similar_questions(self, query, top_n=5):
        """搜索与查询最相似的题目。

        Args:
            query (str): 用户输入的查询文本。
            top_n (int): 返回的最相似题目数量，默认为 5。

        Returns:
            list: 包含相似题目信息的列表，每个元素为 {'question_id': qid, 'question': 合并文本, 'similarity': 分数}。
        """
        questions_data, _ = self.read_questions()
        index, vectorizer = self.load_index()
        
        processed_query = self.preprocess_text(query)
        query_vector = vectorizer.transform([processed_query])
        
        cosine_similarities = cosine_similarity(index, query_vector)
        
        top_indices = cosine_similarities.ravel().argsort()[-top_n:][::-1]
        
        results = []
        for idx in top_indices:
            qid = list(questions_data.keys())[idx]
            question = questions_data[qid]  # 使用合并后的题目内容
            similarity = cosine_similarities[idx][0]
            results.append({
                'question_id': qid,
                'question': question,
                'similarity': round(similarity, 4)
            })
        
        return results
    
    def initialize_index(self):
        """初始化 TF-IDF 索引。

        从数据库读取题目，预处理后构建 TF-IDF 索引并保存到磁盘。
        """
        questions_data, _ = self.read_questions()
        processed_data = self.preprocess_questions(questions_data)
        index, vectorizer = self.create_tfidf_index(processed_data)
        self.save_index(index, vectorizer)
        print("索引初始化完成！")