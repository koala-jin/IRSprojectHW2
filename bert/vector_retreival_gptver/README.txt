📘 向量检索系统 使用说明（简体中文）

一、环境准备

1. 请确保已安装 Python 3.10 或以上版本
2. 安装依赖库：
在该文件夹中空白处右键，选择“在终端中打开”，运行下面指令

   pip install -r requirements.txt

！！！ 这边openai包跟googletrans包发生冲突，运行boolen_retrieval文件夹时注意一下

3. 修正密码的文件目录 ：

（1）streamlit_app.py上有2处，你要修改自己的密码。如下部分：

               db = MySQLDocumentDB(password='123456')

（2）自动收集论文信息(1).py
（3）get_summary.py
（4）bert_engine/database.py

二、数据库配置（MySQL）


*****************************************************************************
*** data文件夹中有ai_papers.sql。把这文件导入到自己的sql workbench上***
*****************************************************************************


上述方法不能做的话 ，做下面的操作 ：
1. 使用以下 SQL 创建数据库（编码需为 utf8mb4）：

-- DB 
CREATE DATABASE ai_papers
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
-- TABLEarxiv_papers
USE ai_papers;

CREATE TABLE IF NOT EXISTS arxiv_papers (
    paper_id VARCHAR(50) PRIMARY KEY,
    title TEXT,
    abstract TEXT,
    authors TEXT,
    published DATE,
    category VARCHAR(20),
    pdf_url TEXT
);

2. 然后在自动收集论文信息(1).py中把第一部分MySQL连接修改成自己的配置，接着运行该python文件，等待一会，出现“成功”字样则表示导入成功

3. 运行get_summary.py。gpt大概需要30分钟左右时间。

三、运行系统

1. 在命令行中运行以下命令：
在该文件夹中空白处右键，选择“在终端中打开”，运行下面指令
   streamlit run streamlit_app.py

2. 浏览器中打开提示的网址即可使用系统

四、系统说明

- 本系统支持使用 Bert 模型进行语义检索
- 支持中文和英文查询（英文将自动翻译为中文）
- 支持结果排序和分页显示
