import mysql.connector

class MySQLDocumentDB:

#### 密码写一下
    def __init__(self, host='localhost', user='root', password='123456', database='ai_papers'): ### 输入自己的密码
        self.conn = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        self.cursor = self.conn.cursor(dictionary=True)

    def fetch_all_documents(self):
        self.cursor.execute("SELECT paper_id, title, abstract, category, authors, published FROM arxiv_papers")
        return self.cursor.fetchall()

    def fetch_document_by_id(self, paper_id):
        self.cursor.execute("SELECT title, abstract, published FROM arxiv_papers WHERE paper_id=%s", (paper_id,))
        return self.cursor.fetchone()
    
    ## gpt_summary
    def fetch_summary_by_id(self, paper_id):
        cursor = self.conn.cursor()
        query = "SELECT summary FROM ai_processed_papers WHERE paper_id = %s"
        cursor.execute(query, (paper_id,))
        result = cursor.fetchone()
        return result[0] if result else None