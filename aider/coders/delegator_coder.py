import re

from .delegator_prompts import DelegatorPrompts
from .ask_coder import AskCoder
from .base_coder import Coder


class DelegatorCoder(AskCoder):
    edit_format = "delegator"
    gpt_prompts = DelegatorPrompts()
    architect_marker = "===Architect==="
    editor_marker = "===Editor==="

    def reply_completed(self):
        content = self.partial_response_content

        if not self.io.confirm_ask("Start planning and building project?"):
            return
        
        # PRODUCT MANAGER
        pm_kwargs = dict()
        
        # Use the product_manager_model from the main_model if it exists, otherwise use the main_model itself
        product_manager_model = self.main_model.product_manager_model or self.main_model
        
        pm_kwargs["main_model"] = product_manager_model
        pm_kwargs["edit_format"] = self.main_model.product_manager_edit_format
        pm_kwargs["total_cost"] = self.total_cost

        product_manager_kwargs = dict(io=self.io, from_coder=self)
        product_manager_kwargs.update(pm_kwargs)

        product_manager_coder = Coder.create(**product_manager_kwargs)
        product_manager_coder.cur_messages = []
        product_manager_coder.done_messages = []

        if self.verbose:
            product_manager_coder.show_announcements()

        product_manager_content = product_manager_coder.run(with_message=content, preproc=False)
        
        # Unique to Product Manager Coder
        self.io.save_project_specification(product_manager_content)

        self.move_back_cur_messages("I updated the project's plan.")
        self.total_cost = product_manager_coder.total_cost
        self.aider_commit_hashes += product_manager_coder.aider_commit_hashes

        if not self.io.confirm_ask("Edit the files?"):
            return
        
        
        # ARCHITECT / EDITOR
        arch_kwargs = dict()
        
        # Use the architect_model from the main_model if it exists, otherwise use the main_model itself
        architect_model = self.main_model.architect_model or self.main_model
        
        arch_kwargs["main_model"] = architect_model
        arch_kwargs["edit_format"] = self.main_model.architect_edit_format
        arch_kwargs["total_cost"] = self.total_cost

        architect_kwargs = dict(io=self.io, from_coder=self)
        architect_kwargs.update(arch_kwargs)

        while True:
            architect_coder = Coder.create(**architect_kwargs)
            architect_coder.cur_messages = []
            architect_coder.done_messages = []

            if self.verbose:
                architect_coder.show_announcements()

            architect_editor_content = architect_coder.run(with_message=product_manager_content, preproc=False)
            # Extract the Architect content
            start_architect = architect_editor_content.find(self.architect_marker) + len(self.architect_marker)
            end_architect = architect_editor_content.find(self.editor_marker)
            architect_content = architect_editor_content[start_architect:end_architect].strip()

            # Extract the Editor content
            start_editor = end_architect + len(self.editor_marker)
            editor_content = architect_editor_content[start_editor:].strip()

            self.total_cost = architect_coder.total_cost
            self.aider_commit_hashes += architect_coder.aider_commit_hashes

            # REVIEWER
            review_kwargs = dict()
        
            # Use the editor_model from the main_model if it exists, otherwise use the main_model itself
            reviewer_model = self.main_model.reviewer_model or self.main_model
            
            review_kwargs["main_model"] = reviewer_model
            review_kwargs["edit_format"] = self.main_model.reviewer_edit_format
            review_kwargs["suggest_shell_commands"] = False
            review_kwargs["map_tokens"] = 0
            review_kwargs["total_cost"] = self.total_cost
            review_kwargs["cache_prompts"] = False
            review_kwargs["num_cache_warming_pings"] = 0

            reviewer_kwargs = dict(io=self.io, from_coder=self)
            reviewer_kwargs.update(review_kwargs)

            reviewer_coder = Coder.create(**reviewer_kwargs)
            reviewer_coder.cur_messages = []
            reviewer_coder.done_messages = []

            if self.verbose:
                reviewer_coder.show_announcements()

            reviewer_content = reviewer_coder.run(with_message=editor_content, preproc=False)
            architect_content += " " + reviewer_content
            
            self.total_cost = reviewer_coder.total_cost
            self.aider_commit_hashes = reviewer_coder.aider_commit_hashes

            if "ACCEPTED" in reviewer_content:
                self.move_back_cur_messages("I reviewed those changes to the files and they look good.")
                break
            else:
                self.move_back_cur_messages("I reviewed those changes to the files and they need additional edits.")

        
        # DOCUMENTATOR
        document_kwargs = dict()
    
        # Use the editor_model from the main_model if it exists, otherwise use the main_model itself
        documentator_model = self.main_model.reviewer_model or self.main_model
        
        document_kwargs["main_model"] = documentator_model
        document_kwargs["edit_format"] = self.main_model.documentator_edit_format
        document_kwargs["suggest_shell_commands"] = False
        document_kwargs["map_tokens"] = 0
        document_kwargs["total_cost"] = self.total_cost
        document_kwargs["cache_prompts"] = False
        document_kwargs["num_cache_warming_pings"] = 0

        documentator_kwargs = dict(io=self.io, from_coder=self)
        documentator_kwargs.update(document_kwargs)

        documentator_coder = Coder.create(**documentator_kwargs)
        documentator_coder.cur_messages = []
        documentator_coder.done_messages = []

        if self.verbose:
            documentator_coder.show_announcements()

        documentator_coder.run(with_message=architect_content, preproc=False)
        
        self.total_cost = documentator_coder.total_cost
        self.aider_commit_hashes = documentator_coder.aider_commit_hashes
        self.move_back_cur_messages("I documented the updated files.")
