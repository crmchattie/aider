from .base_coder import Coder
from .reviewer_prompts import ReviewerPrompts

class ReviewerCoder(Coder):
    edit_format = "reviewer"
    gpt_prompts = ReviewerPrompts()