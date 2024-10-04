from .product_manager_prompts import ProductManagerPrompts
from .ask_coder import AskCoder

class ProductManagerCoder(AskCoder):
    edit_format = "product_manager"
    gpt_prompts = ProductManagerPrompts()
