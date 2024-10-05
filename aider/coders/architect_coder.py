from .architect_prompts import ArchitectPrompts
from .ask_coder import AskCoder
from .base_coder import Coder


class ArchitectCoder(AskCoder):
    edit_format = "architect"
    gpt_prompts = ArchitectPrompts()

    def reply_completed(self):
        architect_content = self.partial_response_content

        if not self.io.confirm_ask("Edit the files?"):
            return

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
        edit_kwargs["summarize_from_coder"] = False

        editor_kwargs = dict(io=self.io, from_coder=self)
        editor_kwargs.update(edit_kwargs)

        editor_coder = Coder.create(**editor_kwargs)
        editor_coder.cur_messages = []
        editor_coder.done_messages = []

        if self.verbose:
            editor_coder.show_announcements()

        editor_content = editor_coder.run(with_message=architect_content, preproc=False)
        # Build the partial response content using delimiters
        self.partial_response_content = f"===Architect===\n{architect_content}\n===Editor===\n{editor_content}"

        self.move_back_cur_messages("I made those changes to the files.")
        self.total_cost = editor_coder.total_cost
        self.aider_commit_hashes = editor_coder.aider_commit_hashes
