from .orchestrator_prompts import OrchestratorPrompts
from .ask_coder import AskCoder
from .base_coder import Coder


class OrchestratorCoder(AskCoder):
    edit_format = "orchestrator"
    gpt_prompts = OrchestratorPrompts()

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
        
        
        # ARCHITECT
        arch_kwargs = dict()
        
        # Use the architect_model from the main_model if it exists, otherwise use the main_model itself
        architect_model = self.main_model.architect_model or self.main_model
        
        arch_kwargs["main_model"] = architect_model
        arch_kwargs["edit_format"] = self.main_model.architect_edit_format
        arch_kwargs["total_cost"] = self.total_cost

        architect_kwargs = dict(io=self.io, from_coder=self)
        architect_kwargs.update(arch_kwargs)

        architect_coder = Coder.create(**architect_kwargs)
        architect_coder.cur_messages = []
        architect_coder.done_messages = []

        if self.verbose:
            architect_coder.show_announcements()

        architect_content = architect_coder.run(with_message=product_manager_content, preproc=False)

        self.move_back_cur_messages("I made those changes to the files.")
        self.total_cost = architect_coder.total_cost
        self.aider_commit_hashes += architect_coder.aider_commit_hashes

    
        # EDITOR
        edit_kwargs = dict()
        
        # Use the editor_model from the main_model if it exists, otherwise use the main_model itself
        editor_model = self.main_model.editor_model or self.main_model
        
        edit_kwargs["main_model"] = editor_model
        edit_kwargs["edit_format"] = self.main_model.editor_edit_format
        edit_kwargs["suggest_shell_commands"] = False
        edit_kwargs["map_tokens"] = 0
        edit_kwargs["total_cost"] = self.total_cost
        edit_kwargs["cache_prompts"] = False
        edit_kwargs["num_cache_warming_pings"] = 0

        editor_kwargs = dict(io=self.io, from_coder=self)
        editor_kwargs.update(edit_kwargs)

        while True:
            editor_coder = Coder.create(**editor_kwargs)
            editor_coder.cur_messages = []
            editor_coder.done_messages = []

            if self.verbose:
                editor_coder.show_announcements()

            editor_response = editor_coder.run(with_message=architect_content, preproc=False)

            self.move_back_cur_messages("I made those changes to the files.")
            self.total_cost = editor_coder.total_cost
            self.aider_commit_hashes = editor_coder.aider_commit_hashes

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

            reviewer_response = reviewer_coder.run(with_message=editor_response, preproc=False)
            architect_content += " " + reviewer_response
            
            self.total_cost = reviewer_coder.total_cost
            self.aider_commit_hashes = reviewer_coder.aider_commit_hashes

            if "ACCEPTED" in reviewer_response:
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

        documentator_coder.run(with_message=editor_response, preproc=False)
        
        self.total_cost = documentator_coder.total_cost
        self.aider_commit_hashes = documentator_coder.aider_commit_hashes
        self.move_back_cur_messages("I documented the updated files.")
