import pymysql
import re
import os
from datetime import datetime
from difflib import get_close_matches
from googletrans import Translator
from dotenv import load_dotenv
from typing import List, Dict, Tuple, Optional

load_dotenv()

translator = Translator(service_urls=['translate.google.cn'])

# ================== 完整分类映射系统 ==================
CATEGORY_TAXONOMY = {
    # 人工智能（父类）
    "cs.AI": {
        "zh_name": "人工智能",
        "en_name": "Artificial Intelligence",
        "zh_aliases": ["AI", "智能系统"],
        "en_aliases": ["AI"],
        "subclasses": ["cs.CL", "cs.CV", "cs.LG"]
    },

    # 自然语言处理（cs.AI子类）
    "cs.CL": {
        "zh_name": "自然语言处理",
        "en_name": "Natural Language Processing",
        "zh_aliases": ["NLP", "语义分析"],
        "en_aliases": ["NLP"],
        "subclasses": ["llm"]  # 新增LLM子类
    },

    # 计算机视觉（cs.AI子类）
    "cs.CV": {
        "zh_name": "计算机视觉",
        "en_name": "Computer Vision",
        "zh_aliases": ["CV", "图像识别"],
        "en_aliases": ["CV"],
        "subclasses": []
    },

    # 机器学习（cs.AI子类）
    "cs.LG": {
        "zh_name": "机器学习",
        "en_name": "Machine Learning",
        "zh_aliases": ["ML", "深度学习","监督学习","无监督学习"],
        "en_aliases": ["ML"],
        "subclasses": []
    },

    # 统计机器学习（独立大类）
    "stat.ML": {
        "zh_name": "统计机器学习",
        "en_name": "Statistical Machine Learning",
        "zh_aliases": ["统计学习","机器学习"],
        "en_aliases": ["Stat ML"],
        "subclasses": []
    },

    # 大语言模型（cs.CL子类）
    "llm": {
        "zh_name": "大语言模型",
        "en_name": "Large Language Model",
        "zh_aliases": ["LLM", "GPT"],
        "en_aliases": ["LLM"],
        "subclasses": []
    }
}

# 构建分类映射字典
CATEGORY_MAPPING = {}
HIERARCHY_MAPPING = {}

for code, info in CATEGORY_TAXONOMY.items():
    # 中文映射
    CATEGORY_MAPPING[info["zh_name"].lower()] = code
    for alias in info["zh_aliases"]:
        CATEGORY_MAPPING[alias.lower()] = code

    # 英文映射
    CATEGORY_MAPPING[info["en_name"].lower()] = code
    HIERARCHY_MAPPING[code] = {
        'name': info["zh_name"],
        'subclasses': info["subclasses"]
    }

# 构建分类建议字典
CATEGORY_SUGGESTIONS = {}
for code, info in CATEGORY_TAXONOMY.items():
    CATEGORY_SUGGESTIONS[info["zh_name"]] = code
    CATEGORY_SUGGESTIONS[info["en_name"].lower()] = code
    for alias in info["zh_aliases"] + info["en_aliases"]:
        CATEGORY_SUGGESTIONS[alias.lower()] = code

# ================== 分类建议函数 ==================
def suggest_category(input_str: str) -> List[str]:
    """提供分类建议（支持中英文）"""
    input_str = input_str.strip().lower()

    # 精确匹配
    if input_str in CATEGORY_SUGGESTIONS:
        return [CATEGORY_TAXONOMY[CATEGORY_SUGGESTIONS[input_str]]["zh_name"]]

    # 模糊匹配
    matches = get_close_matches(
        input_str,
        CATEGORY_SUGGESTIONS.keys(),
        n=3,
        cutoff=0.6
    )

    # 去重标准化
    seen = set()
    suggestions = []
    for match in matches:
        code = CATEGORY_SUGGESTIONS[match]
        zh_name = CATEGORY_TAXONOMY[code]["zh_name"]
        if zh_name not in seen:
            suggestions.append(zh_name)
            seen.add(zh_name)

    return suggestions[:3]

# ================== 同义词系统 ==================
KEYWORD_SYNONYMS = {
    "大语言模型": ["llm", "large language model", "llm模型"],
    "llm": ["大语言模型", "large language model"]
}


def expand_synonyms(keyword: str) -> List[str]:
    """扩展同义词"""
    return KEYWORD_SYNONYMS.get(keyword.lower(), [keyword]) + [keyword]

def safe_translate(text: str) -> str:
    """带异常处理的翻译"""
    try:
        return translator.translate(text, src='zh-cn', dest='en').text
    except:
        return text

# ================== 检索核心类 ==================
class PaperRetriever:
    def __init__(self):
        self.conn = pymysql.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            port=int(os.getenv('DB_PORT', 3306)),
            charset='utf8mb4',
            cursorclass=pymysql.cursors.DictCursor
        )
        self.current_query = None

    def _resolve_category(self, input_str: str) -> List[str]:
        """解析分类输入（含子类扩展）"""
        input_str = input_str.lower().strip()
        code = CATEGORY_MAPPING.get(input_str, None)

        if not code:
            return []

        # 获取所有子类
        all_codes = [code]
        stack = [code]
        while stack:
            current = stack.pop()
            for subclass in HIERARCHY_MAPPING.get(current, {}).get('subclasses', []):
                all_codes.append(subclass)
                stack.append(subclass)

        return list(set(all_codes))

    def _translate_keyword(self, keyword: str) -> str:
        """翻译关键词（中->英）"""
        try:
            return translator.translate(keyword, src='zh-cn', dest='en').text
        except:
            return keyword

    def parse_query(self, query: str) -> Tuple[str, List]:
        """增强的查询解析"""
        tokens = re.split(r'\s+(AND|OR|NOT)\s+', query)
        conditions = []
        params = []
        current_logic = "AND"

        for token in tokens:
            if token in ("AND", "OR", "NOT"):
                current_logic = token
                continue

            if ":" in token:
                field, value = token.split(":", 1)
                field = field.strip()
                value = value.strip().lower()

                # 处理主题分类
                if field == "主题分类":
                    codes = self._resolve_category(value)
                    if not codes:
                        continue

                    placeholders = ",".join(["%s"] * len(codes))
                    conditions.append(f"{current_logic} category IN ({placeholders})")
                    params.extend(codes)

                # 处理关键词（含同义词扩展和翻译）
                elif field == "关键词":
                    synonyms = expand_synonyms(value)
                    translated = [self._translate_keyword(s) for s in synonyms]

                    # 构建搜索条件
                    clauses = []
                    for word in translated:
                        clauses.append("(title LIKE %s OR abstract LIKE %s)")
                        params.extend([f"%{word}%", f"%{word}%"])

                    conditions.append(f"{current_logic} ({' OR '.join(clauses)})")

                # 处理作者
                elif field == "作者":
                    conditions.append(f"{current_logic} authors LIKE %s")
                    params.append(f"%{value}%")

                # 处理日期
                elif field == "发表年份" and re.match(r"^\d{4}$", value):
                    conditions.append(f"{current_logic} YEAR(published) = %s")
                    params.append(value)

        # 构建最终WHERE语句
        where_clause = " ".join(conditions)
        if where_clause.startswith(("AND ", "OR ")):
            where_clause = where_clause.split(" ", 1)[1]

        return (f"WHERE {where_clause}" if where_clause else ""), params

    def advanced_search(self, query: str) -> List[Dict]:
        """执行高级检索"""
        try:
            where_clause, params = self.parse_query(query)
            sql = f"SELECT * FROM arxiv_papers {where_clause}"
            with self.conn.cursor() as cursor:
                cursor.execute(sql, params)
                results = cursor.fetchall()
                self.current_query = (sql, params)
                return results
        except Exception as e:
            raise RuntimeError(f"检索失败: {str(e)}")

    def refine_search(self,
                      base_results: List[Dict],
                      categories: List[str] = None,
                      authors: List[str] = None,
                      start_date: str = None,
                      end_date: str = None) -> List[Dict]:
        """修复后的筛选方法"""
        filtered = base_results.copy()  # 防止修改原始数据

        # 分类筛选（包含子类）
        if categories:
            valid_codes = set()
            for cat in categories:
                # 解析分类并获取所有子类
                codes = self._resolve_category(cat)
                if codes:
                    valid_codes.update(codes)
                else:
                    # 直接匹配未识别的分类代码
                    valid_codes.add(cat)

            if valid_codes:
                filtered = [
                    p for p in filtered
                    if p.get('category', '') in valid_codes
                ]

        # 作者筛选（兼容不同分隔符）
        if authors:
            author_set = {a.strip().lower() for a in authors}
            filtered = [
                p for p in filtered
                if any(a.strip().lower() in author_set
                       for a in re.split(r',|，', p.get('authors', '')))
            ]

        # 日期筛选（兼容多种日期格式）
        date_format = "%Y-%m-%d"
        try:
            if start_date:
                start = datetime.strptime(start_date, date_format).date()
                filtered = [
                    p for p in filtered
                    if datetime.strptime(str(p.get('published', '')), date_format).date() >= start
                ]
            if end_date:
                end = datetime.strptime(end_date, date_format).date()
                filtered = [
                    p for p in filtered
                    if datetime.strptime(str(p.get('published', '')), date_format).date() <= end
                ]
        except ValueError:
            pass

        return filtered