
import arxiv
import mysql.connector
from datetime import datetime

# 1. MySQL 链接
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="jmh86217186!",  # Workbecnch 密码，这里写了我自己的密码
    database="ai_papers"
)
cursor = db.cursor()

# 2. arXiv 论文收集
search = arxiv.Search(
    query="cat:cs.AI OR cat:cs.CL OR cat:cs.LG OR cat:stat.ML",
    max_results=1000,  
    sort_by=arxiv.SortCriterion.SubmittedDate
)

for result in search.results():
    try:
        paper_id = result.get_short_id()
        title = result.title.replace("'", "\\'")
        abstract = result.summary.replace("'", "\\'")
        authors = ", ".join([author.name for author in result.authors])
        published = result.published.strftime('%Y-%m-%d')
        category = result.primary_category
        pdf_url = result.pdf_url

        sql = f"""
        INSERT IGNORE INTO arxiv_papers 
        (paper_id, title, abstract, authors, published, category, pdf_url)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (
            paper_id, title, abstract, authors, published, category, pdf_url
        ))

    except Exception as e:
        print(f"❌ 失败: {result.title[:40]}... 原因: {e}")

db.commit()
cursor.close()
db.close()

print("✅ 成功")
