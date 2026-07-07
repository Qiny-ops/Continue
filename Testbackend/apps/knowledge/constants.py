"""
知识库模块 - 常量定义
"""

# 知识库类型
class KnowledgeBaseType:
    DOCUMENT = 'document'
    WEB = 'web'
    MIXED = 'mixed'

    CHOICES = [
        (DOCUMENT, '文档类型'),
        (WEB, '网页类型'),
        (MIXED, '混合类型'),
    ]


# 知识文档类型
class KnowledgeFileType:
    PDF = 'pdf'
    DOCX = 'docx'
    XLSX = 'xlsx'
    PPTX = 'pptx'
    TXT = 'txt'
    MD = 'md'
    HTML = 'html'
    URL = 'url'
    MANUAL = 'manual'

    CHOICES = [
        (PDF, 'PDF'),
        (DOCX, 'Word'),
        (XLSX, 'Excel'),
        (PPTX, 'PowerPoint'),
        (TXT, '文本'),
        (MD, 'Markdown'),
        (HTML, '网页'),
        (URL, 'URL链接'),
        (MANUAL, '手动创建'),
    ]


# 知识迁移模式
class KnowledgeMoveMode:
    REUSE_VECTORS = 'reuse_vectors'
    RE_EMBED = 're_embed'

    CHOICES = [
        (REUSE_VECTORS, '复用向量'),
        (RE_EMBED, '重新嵌入'),
    ]


# 知识状态
class KnowledgeStatus:
    PENDING = 'pending'
    PROCESSING = 'processing'
    COMPLETED = 'completed'
    FAILED = 'failed'

    CHOICES = [
        (PENDING, '待处理'),
        (PROCESSING, '处理中'),
        (COMPLETED, '已完成'),
        (FAILED, '处理失败'),
    ]


# API 请求超时时间（秒）
API_TIMEOUT = 30

# 文件上传最大大小（字节）
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB

# 支持的文件扩展名
SUPPORTED_FILE_EXTENSIONS = [
    '.pdf', '.docx', '.xlsx', '.pptx',
    '.txt', '.md', '.html', '.htm'
]

# 每页默认知识数量
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
