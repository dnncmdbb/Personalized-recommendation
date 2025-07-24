import os
from llm_question_analyzer import QuestionAnalyzer
from TFIDF_search_engine import QuestionSearchEngine

def main():
    # 配置路径
    db_path = '/Users/dengniannian/Downloads/教育大模型/kgcd_7_17/data/student_data.db'
    index_file = '/Users/dengniannian/Downloads/教育大模型/qa_analysis/xlike_rec_english_0723/question_index.pkl'
    vectorizer_file = '/Users/dengniannian/Downloads/教育大模型/qa_analysis/xlike_rec_english_0723/question_vectorizer.pkl'
    nltk_data_path = '/Users/dengniannian/Downloads/教育大模型/qa_analysis/xlike_rec_english/nltk_data'

    # 初始化分析器和搜索引擎
    analyzer = QuestionAnalyzer()
    search_engine = QuestionSearchEngine(db_path, index_file, vectorizer_file, nltk_data_path)

    # 初始化索引（如果需要）
    if not (os.path.exists(index_file) and os.path.exists(vectorizer_file)):
        print("首次运行，正在初始化索引...")
        search_engine.initialize_index()

    print("题目分析与相似题目搜索系统（输入q退出）")
    while True:
        question = input("\n请输入英语题目：").strip()
        if question.lower() == 'q':
            break

        print("\n正在分析题目...")
        analysis_result = analyzer.analyze_question(question)

        if analysis_result:
            print("\n分析结果：")
            print(analysis_result)
        else:
            print("\n分析失败")

        # 使用题目和分析结果进行搜索
        query = f"{question} {analysis_result}" if analysis_result else question
        print("\n正在搜索相似题目...")
        results = search_engine.search_similar_questions(query)

        print(f"\n找到 {len(results)} 个相似题目：")
        for i, result in enumerate(results, 1):
            print(f"{i}. [相似度: {result['similarity']:.2f}] {result['question']}")

if __name__ == "__main__":
    main()