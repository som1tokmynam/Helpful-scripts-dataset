import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
from pathlib import Path
import ttkbootstrap as bstrap
from ttkbootstrap.constants import *

try:
    # --- Tool Imports ---
    from tools.combinejsonl import combine_jsonl_files
    from tools.cleanup_text import cleanup_text_in_jsonl
    from tools.cleanasterisks import process_jsonl_file as clean_asterisks_in_jsonl
    from tools.cleanupjsonl_last_user_turn import main as remove_last_user_turn
    from tools.DeslopTool import filter_dataset as deslop_dataset
    from tools.convert_json_to_jsonl import convert_json_to_jsonl
    from tools.convert_txt_to_Json import convert_multiple_txt_to_json
    from tools.convert_unicode_to_characters import normalize_unicode_in_jsonl
    from tools.validate_dataset import validate_and_clean_jsonl
    from tools.remove_system_prompt import remove_system_prompt_from_jsonl
    from tools.convert_pretraining_json_to_jsonl import convert_pretraining_json_to_jsonl
    from tools.character_counter import count_characters_in_jsonl
    from tools.remove_standalone_names import remove_standalone_names_main
    from tools.fix_ooc_misattribution import fix_dataset_issues
    from tools.find_unused_chunks_tool import find_unused_text_chunks # <-- NEW TOOL IMPORTED
except ImportError as e:
    messagebox.showerror("Fatal Error", f"Could not import a tool script. Please ensure the 'tools' subfolder exists and contains all required scripts.\n\nError: {e}")
    sys.exit(1)


class TextRedirector:
    def __init__(self, widget):
        self.widget = widget
    def write(self, text):
        self.widget.configure(state='normal')
        self.widget.insert('end', text)
        self.widget.see('end')
        self.widget.update_idletasks()
    def flush(self):
        pass

class DatasetToolkit(bstrap.Window):
    def __init__(self):
        super().__init__(themename="superhero", title="Dataset Processing Toolkit")
        self.geometry("1100x800")
        self.minsize(900, 650)

        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=10, pady=(10,0))

        self.nav_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(self.nav_frame, weight=1)

        self.content_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(self.content_frame, weight=5)
        
        self.frames = {}
        
        # --- MODIFIED: Added FindUnusedTab and sorted alphabetically for clarity ---
        extra_tool_tabs = {
            "CharCounterTab": (CharCounterTab, "Character Counter"),
            "CombineTab": (CombineTab, "Combine JSONL"),
            "FindUnusedTab": (FindUnusedTab, "Find Unused Chunks"),
            "PretrainConvertTab": (PretrainConvertTab, "Pre-train Convert"),
            "RemovePromptTab": (RemovePromptTab, "Remove Sys Prompt"),
            "TxtToJsonTab": (TxtToJsonTab, "TXT -> JSON"),
            "ValidateTab": (ValidateTab, "Validate JSONL"),
        }

        pipeline_frame = ProcessingPipelineTab(self.content_frame, self)
        self.frames["ProcessingPipelineTab"] = pipeline_frame
        pipeline_frame.grid(row=0, column=0, sticky="nsew")

        for name, (F, title) in extra_tool_tabs.items():
            frame = F(self.content_frame, self)
            self.frames[name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.add_nav_button("Processing Pipeline", "ProcessingPipelineTab")
        ttk.Separator(self.nav_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
        ttk.Label(self.nav_frame, text="Extra Tools", bootstyle="secondary").pack(fill=X, pady=(0,5))
        
        # --- MODIFIED: Loop creates buttons based on the sorted dictionary ---
        for name, (F, title) in sorted(extra_tool_tabs.items(), key=lambda item: item[1][1]):
            self.add_nav_button(title, name)
        
        log_frame = ttk.LabelFrame(self, text="Log Output", padding=5)
        log_frame.pack(fill=X, expand=False, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, wrap='word', state='disabled', font=("Courier New", 9))
        self.log_text.pack(side=LEFT, fill=X, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill='y')
        self.log_text['yscrollcommand'] = scrollbar.set

        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

        self.show_frame("ProcessingPipelineTab")
        print("Dataset Toolkit v3.4 Loaded. Added 'Find Unused Chunks' tool.")

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)
    
    def add_nav_button(self, text, page_name):
        button = ttk.Button(self.nav_frame, text=text, command=lambda: self.show_frame(page_name), bootstyle="info")
        button.pack(fill=X, pady=2)

    def show_frame(self, page_name):
        frame = self.frames[page_name]
        frame.tkraise()

    def create_io_widgets(self, parent, io_type='file', label_text="Input File:", file_types=None):
        frame = ttk.Frame(parent)
        label = ttk.Label(frame, text=label_text, width=15)
        label.pack(side=LEFT, padx=5)
        entry_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=entry_var)
        entry.pack(side=LEFT, expand=True, fill=X, padx=5)

        def select_path():
            path = ""
            if io_type == 'file': path = filedialog.askopenfilename(filetypes=file_types)
            elif io_type == 'folder': path = filedialog.askdirectory()
            elif io_type == 'save_file': path = filedialog.asksaveasfilename(filetypes=file_types, defaultextension=file_types[0][1] if file_types else None)
            if path: entry_var.set(path)

        button = ttk.Button(frame, text="Browse...", command=select_path, bootstyle="info-outline")
        button.pack(side=LEFT, padx=5)
        frame.pack(fill=X, pady=5)
        return entry_var

    def execute_tool(self, tool_function, title, **kwargs):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')
        try:
            print(f"--- Starting: {title} ---\n")
            tool_function(**kwargs)
            print(f"\n--- Finished: {title} ---")
            if title != "Character Count":
                messagebox.showinfo("Success", f"{title} completed successfully!")
        except Exception as e:
            error_message = f"An error occurred during {title}:\n\n{e}"
            print(f"\n--- ERROR: {error_message} ---")
            messagebox.showerror("Error", error_message)

    def run_pipeline(self, initial_input_file, steps_to_run, deslop_filter_file, deslop_threshold, output_prefix):
        self.log_text.configure(state='normal')
        self.log_text.delete('1.0', 'end')
        self.log_text.configure(state='disabled')

        if not initial_input_file or not Path(initial_input_file).is_file():
            messagebox.showerror("Error", "Please select a valid initial input file.")
            return

        pipeline_definition = {
            1: {"name": "Convert JSON to JSONL", "func": convert_json_to_jsonl, "args": lambda i, o: {"input_path": i, "output_path": o}},
            2: {"name": "Normalize Unicode", "func": normalize_unicode_in_jsonl, "args": lambda i, o: {"input_file": i, "output_file": o}},
            3: {"name": "Cleanup Separators", "func": cleanup_text_in_jsonl, "args": lambda i, o: {"input_file": i, "output_file": o}},
            4: {"name": "Fix OOC Issues", "func": fix_dataset_issues, "args": lambda i, o: {"input_file": i, "output_file": o}},
            5: {"name": "Remove Standalone Names", "func": remove_standalone_names_main, "args": lambda i, o: {"input_file": i, "output_file": o}},
            6: {"name": "Clean Asterisks", "func": clean_asterisks_in_jsonl, "args": lambda i, o: {"input_file": i, "output_file": o}},
            7: {"name": "Trim Last Turn", "func": remove_last_user_turn, "args": lambda i, o: type('Args', (), {'input_file': i, 'output_file': o, 'conversation_key': 'conversations', 'role_key': 'from', 'user_role': 'human'})},
            8: {"name": "Deslop Tool", "func": deslop_dataset, "args": lambda i, o: {"dataset_file": i, "output_file": o, "filter_files": [deslop_filter_file], "threshold": deslop_threshold}}
        }
        
        try:
            last_step_to_run = 0
            for i in range(8, 0, -1):
                if steps_to_run.get(i).get():
                    last_step_to_run = i
                    break
            
            p = Path(initial_input_file)
            current_input_path = str(p.resolve())
            original_filename = p.name
            input_dir = p.parent

            print(f"--- Starting Processing Pipeline for: {p.name} ---\n")
            final_output_file = ""

            for step_num in range(1, 9):
                if steps_to_run.get(step_num).get():
                    step_info = pipeline_definition[step_num]
                    step_name = step_info["name"]
                    
                    is_final_step = (step_num == last_step_to_run)
                    if is_final_step and output_prefix:
                        safe_prefix = "".join(c for c in output_prefix if c.isalnum() or c in ('_','-')).strip()
                        output_path = str(input_dir / f"{safe_prefix}{p.stem}.jsonl")
                    else:
                        output_path = str(input_dir / f"{p.stem}_step{step_num}.jsonl")
                    
                    final_output_file = output_path

                    print(f"--- Running Step {step_num}: {step_name} ---")
                    print(f"Input: {Path(current_input_path).name}")
                    print(f"Output: {Path(output_path).name}")
                    
                    if step_num == 7:
                        args_obj = step_info["args"](current_input_path, output_path)
                        remove_last_user_turn(args=args_obj)
                    else:
                        if step_num == 8 and (not deslop_filter_file or not Path(deslop_filter_file).exists()):
                            raise ValueError("Deslop filter file is not specified or does not exist.")
                        kwargs = step_info["args"](current_input_path, output_path)
                        step_info["func"](**kwargs)
                    
                    print(f"--- Step {step_num} Complete ---\n")
                    current_input_path = output_path
                else:
                    print(f"--- Skipping Step {step_num}: {pipeline_definition[step_num]['name']} ---\n")
            
            print(f"--- Pipeline Finished ---")
            if final_output_file:
                 print(f"Final output file: {final_output_file}")
                 messagebox.showinfo("Success", f"Pipeline completed successfully!\n\nFinal output: {Path(final_output_file).name}")
            else:
                 messagebox.showinfo("Finished", "Pipeline finished, but no steps were selected to run.")

        except Exception as e:
            error_message = f"An error occurred during the pipeline:\n\n{e}"
            print(f"\n--- PIPELINE FAILED: {error_message} ---")
            messagebox.showerror("Pipeline Error", error_message)

class BaseTab(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

class ProcessingPipelineTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        
        ttk.Label(self, text="Dataset Processing Pipeline", font=("-size 14 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Run a sequence of tools on a dataset. Each step creates a new file.", bootstyle="primary", wraplength=500).pack(fill=X, pady=10)

        self.in_file_var = self.controller.create_io_widgets(self, 'file', "Initial Input File:", [("JSON files", "*.json"), ("JSONL files", "*.jsonl")])

        steps_frame = ttk.LabelFrame(self, text="Processing Steps", padding=15)
        steps_frame.pack(fill=X, pady=10, padx=5)

        self.steps_vars = {}
        steps_info = [
            "Step 1: Convert JSON to JSONL",
            "Step 2: Normalize Unicode Characters",
            "Step 3: Cleanup Separators (---, **)",
            "Step 4: Fix OOC Misattribution",
            "Step 5: Remove Standalone Names/Roles",
            "Step 6: Clean Enclosing Asterisks",
            "Step 7: Trim Last User Turn",
            "Step 8: Deslop Tool (Filter Content)"
        ]

        for i, text in enumerate(steps_info, 1):
            var = tk.BooleanVar(value=True)
            self.steps_vars[i] = var
            chk = ttk.Checkbutton(steps_frame, text=text, variable=var, bootstyle="primary")
            chk.pack(anchor=W, padx=10, pady=3)

        deslop_frame = ttk.LabelFrame(self, text="Step 8: Deslop Options", padding=10)
        deslop_frame.pack(fill=X, pady=10, padx=5)
        
        self.filter_file_var = self.controller.create_io_widgets(deslop_frame, 'file', "Filter File:", [("Text files", "*.txt")])
        try:
            default_filter_path = self.controller.resource_path("f.txt")
            if os.path.exists(default_filter_path):
                self.filter_file_var.set(default_filter_path)
        except Exception:
            pass 

        threshold_frame = ttk.Frame(deslop_frame)
        threshold_frame.pack(fill=X, pady=5)
        self.use_threshold_var = tk.BooleanVar(value=False)
        self.threshold_spinbox = ttk.Spinbox(threshold_frame, from_=0.1, to=10.0, increment=0.1, state="disabled", width=8)
        self.threshold_spinbox.set(1.5)
        
        def toggle_spinbox():
            self.threshold_spinbox.configure(state="normal" if self.use_threshold_var.get() else "disabled")

        threshold_check = ttk.Checkbutton(threshold_frame, text="Use statistical threshold filtering", variable=self.use_threshold_var, command=toggle_spinbox, bootstyle="info")
        threshold_check.pack(side=LEFT, padx=5)
        self.threshold_spinbox.pack(side=LEFT, padx=5)

        prefix_frame = ttk.LabelFrame(self, text="Final Output Naming", padding=10)
        prefix_frame.pack(fill=X, pady=(10,5), padx=5)
        ttk.Label(prefix_frame, text="Prefix for final file:").pack(side=LEFT, padx=(5,10))
        self.prefix_var = tk.StringVar(value="cleaned_")
        ttk.Entry(prefix_frame, textvariable=self.prefix_var).pack(side=LEFT, fill=X, expand=True, padx=5)
        
        run_btn = ttk.Button(self, text="Run Processing Pipeline", command=self.run, bootstyle="success-lg")
        run_btn.pack(pady=20, ipady=10)

    def run(self):
        threshold_value = None
        if self.use_threshold_var.get():
            try:
                threshold_value = float(self.threshold_spinbox.get())
            except ValueError:
                messagebox.showerror("Invalid Input", "Threshold must be a valid number.")
                return
        
        self.controller.run_pipeline(
            initial_input_file=self.in_file_var.get(),
            steps_to_run=self.steps_vars,
            deslop_filter_file=self.filter_file_var.get(),
            deslop_threshold=threshold_value,
            output_prefix=self.prefix_var.get()
        )

# --- NEW: The tab class for the "Find Unused Chunks" tool ---
class FindUnusedTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Find Unused Chunks", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Compares a master JSON list to a resulting JSON file to find and save unused text chunks.", 
                  wraplength=550, bootstyle="primary").pack(fill=X, pady=10)
        
        master_file_var = self.controller.create_io_widgets(self, 'file', "Master File:", [("JSON files", "*.json")])
        resulting_file_var = self.controller.create_io_widgets(self, 'file', "Resulting File:", [("JSON files", "*.json")])
        output_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSON files", "*.json")])
        
        run_btn = ttk.Button(self, text="Find Unused Chunks", 
                             command=lambda: self.controller.execute_tool(
                                 find_unused_text_chunks, 
                                 "Find Unused Chunks", 
                                 master_file=master_file_var.get(), 
                                 resulting_file=resulting_file_var.get(), 
                                 output_file=output_file_var.get()
                             ), bootstyle="success")
        run_btn.pack(pady=20)


class CombineTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Combine JSONL Files", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Combine multiple .jsonl files from a folder into one.", bootstyle="primary").pack(fill=X, pady=10)
        in_dir_var = self.controller.create_io_widgets(self, 'folder', "Input Folder:")
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Combination", command=lambda: self.controller.execute_tool(combine_jsonl_files, "Combine JSONL", input_dir=in_dir_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

class TxtToJsonTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="TXT to JSON", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Convert all .txt files in a folder to a single .json file.", bootstyle="primary").pack(fill=X, pady=10)
        in_dir_var = self.controller.create_io_widgets(self, 'folder', "Input Folder:")
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSON files", "*.json")])
        run_btn = ttk.Button(self, text="Run Conversion", command=lambda: self.controller.execute_tool(convert_multiple_txt_to_json, "TXT to JSON", input_directory=in_dir_var.get(), output_file_path=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

class ValidateTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Validate JSONL", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Validates each line is a valid {'text': '...'} JSON object.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Validation", command=lambda: self.controller.execute_tool(validate_and_clean_jsonl, "Validate JSONL", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

class RemovePromptTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Remove System Prompt", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Removes the first turn of a conversation if it's a system prompt.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        options_frame = ttk.LabelFrame(self, text="Options", padding=10)
        options_frame.pack(fill=X, pady=10)
        system_role_var = tk.StringVar(value="system")
        ttk.Label(options_frame, text="System Role Name:").pack(side=LEFT, padx=5)
        ttk.Entry(options_frame, textvariable=system_role_var).pack(side=LEFT, fill=X, expand=True, padx=5)
        run_btn = ttk.Button(self, text="Run Removal", command=lambda: self.controller.execute_tool(remove_system_prompt_from_jsonl, "Remove System Prompt", input_file=in_file_var.get(), output_file=out_file_var.get(), system_role=system_role_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

class PretrainConvertTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Convert for Pre-training", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Converts nested {'text': {'text': ...}} to simple {'text': ...} JSONL.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSON files", "*.json")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Conversion", command=lambda: self.controller.execute_tool(convert_pretraining_json_to_jsonl, "Pre-training Conversion", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

class CharCounterTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Character Counter", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Analyze character count statistics for a JSONL dataset.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSON/JSONL files", "*.json*"), ("All files", "*.*")])
        run_btn = ttk.Button(self, text="Run Analysis", command=lambda: self.controller.execute_tool(count_characters_in_jsonl, "Character Count", input_file=in_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)


if __name__ == '__main__':
    app = DatasetToolkit()
    app.mainloop()