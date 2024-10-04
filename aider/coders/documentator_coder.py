from .product_manager_prompts import DocumentatorPrompts
from .ask_coder import AskCoder

class ProductManagerCoder(AskCoder):
    edit_format = "documentator"
    gpt_prompts = DocumentatorPrompts()
