# 相似题推荐部分-对应xlike_rec_english_0723文件夹
llm_question_analyzer.py，调用api（参数在.env文件中），将题目给llm分析三个最相关的知识点和一个考察词汇/固定搭配的类；
TFIDF_search_engine.py，进行TFIDF相似度分析的类；
main_run.py，主函数，用于运行，需要修改其中的地址：
    db_path 数据库地址；
    index_file = question_index.pkl地址，如果文件存在就不会再次生成；
    vectorizer_file = question_vectorizer.pkl地址，如果文件存在不会再次生成；
    nltk_data_path = nltk_data文件的地址，如果文件存在不会再次生成。



# IRT难度：
θ（theta）：学生能力，范围通常为[-3, 3]，越高表示能力越强。根绝学生自己而言
a：区分度（题目区分学生能力的效果）。
b：难度（答对概率50%对应的能力值）。
c：猜测参数（即使能力为0，随机猜对的概率）

# answer_type
wrong：-1
半对：0
对：1

# 知识点掌握情况
该知识点没做过，20%以内，20%～40%，40%～60%，60%～80%，80%～100%，设置掌握程度分别写成1，2，3，4，5