一、本检索基于utf8mb4，因此在创建数据库时需要指定相应字符，创建MySQL的数据库代码如下：
--创建数据库
CREATE DATABASE ai_papers
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;
--创建相应表
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

二、然后在自动收集论文信息(1).py中把第一部分MySQL连接修改成自己的配置，接着运行该python文件，等待一会，出现“成功”字样则表示导入成功

三、运行剩下两个python文件的配置在requirements.txt中请在运行之前安装好相应的包

四、用记事本打开.env文件，将其修改成自己MySQL数据库的配置

五、最后，在该文件夹中空白处右键，选择“在终端中打开”，运行streamlit run interactive_retrieval.py（注意不是python命令），然后按住ctrl访问出现的链接即可进行高级检索

六、请注意，运行所有代码时，均需要保持MySQL处于运行状态