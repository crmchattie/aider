from .architect_prompts import ArchitectPrompts
from .ask_coder import AskCoder

class ArchitectCoder(AskCoder):
    edit_format = "architect"
    gpt_prompts = ArchitectPrompts()
