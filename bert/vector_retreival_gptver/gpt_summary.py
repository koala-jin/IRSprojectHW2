import mysql.connector
import openai
import re
import time
import os
from dotenv import load_dotenv

# 这里是我自己的api_key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# 目前的prompt1，需要改
def analyze_abstract(abstract):
    prompt = f"""
请根据以下论文摘要完成以下任务：

1. 用 2~3 句话总结这篇论文的核心内容，涵盖研究问题、方法和结果；
2. 判断该论文是否属于人工智能的核心研究内容（如 LLM、NLP、CV、RL、生成模型等）。请回答 “是” 或 “否”；
3. 根据摘要内容为该论文指定一个主分类（例如：LLM、自然语言处理、图像识别、语音处理、强化学习、非AI等）。

摘要如下：
{abstract}

请用如下格式回答：
总结: ...
是否核心AI论文: 是/否
主分类: ...
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    content = response.choices[0].message.content

    summary = re.search(r"总结:\s*(.*)", content)
    is_core = re.search(r"是否核心AI论文:\s*(.*)", content)
    main_cat = re.search(r"主分类:\s*(.*)", content)

    return {
        "summary": summary.group(1).strip() if summary else "",
        "is_core_ai": is_core.group(1).strip() if is_core else "否",
        "main_category": main_cat.group(1).strip() if main_cat else "未知"
    }

# 我自己的mySQL密码
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="123456",  
    database="ai_papers"
)
cursor = db.cursor(dictionary=True)


cursor.execute("""
CREATE TABLE IF NOT EXISTS ai_processed_papers (
    paper_id VARCHAR(50) PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    authors TEXT,
    published DATE,
    category VARCHAR(20),
    main_category VARCHAR(100),
    pdf_url TEXT,
    summary TEXT
)
""")


cursor.execute("SELECT * FROM arxiv_papers")
papers = cursor.fetchall()

insert_sql = """
INSERT IGNORE INTO ai_processed_papers
(paper_id, title, abstract, authors, published, category, main_category, pdf_url, summary)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
"""

for paper in papers:
    try:
        result = analyze_abstract(paper['abstract'])
        if result['is_core_ai'] == '是':
            cursor.execute(insert_sql, (
                paper['paper_id'], paper['title'], paper['abstract'],
                paper['authors'], paper['published'], paper['category'],
                result['main_category'], paper['pdf_url'], result['summary']
            ))
            print(f"成功: {paper['paper_id']}")
        else:
            print(f"失败(非核心): {paper['paper_id']}")
        time.sleep(1) 
    except Exception as e:
        print(f"失败({paper['paper_id']}): {e}")
        continue


db.commit()
cursor.close()
db.close()
print("结束")
