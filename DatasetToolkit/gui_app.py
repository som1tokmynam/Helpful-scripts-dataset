import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
import os
from pathlib import Path
import ttkbootstrap as bstrap
from ttkbootstrap.constants import *

# --- Import ALL your refactored tool functions ---
try:
    from tools.combinejsonl import combine_jsonl_files
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
        self.geometry("1100x750")
        self.minsize(900, 600)

        main_pane = ttk.PanedWindow(self, orient=HORIZONTAL)
        main_pane.pack(fill=BOTH, expand=True, padx=10, pady=(10,0))

        self.nav_frame = ttk.Frame(main_pane, padding=5)
        main_pane.add(self.nav_frame, weight=1)

        self.content_frame = ttk.Frame(main_pane, padding=10)
        main_pane.add(self.content_frame, weight=5)
        
        self.frames = {}
        
        for F in (CombineTab, AsterisksTab, TrimTurnTab, DeslopTab, ValidateTab, CharCounterTab, RemovePromptTab, TxtToJsonTab, JsonToJsonlTab, PretrainConvertTab, UnicodeTab):
            page_name = F.__name__
            frame = F(self.content_frame, self)
            self.frames[page_name] = frame
            frame.grid(row=0, column=0, sticky="nsew")
        self.content_frame.grid_rowconfigure(0, weight=1)
        self.content_frame.grid_columnconfigure(0, weight=1)

        self.add_nav_button("Combine JSONL", "CombineTab")
        self.add_nav_button("Clean Asterisks", "AsterisksTab")
        self.add_nav_button("Trim Last Turn", "TrimTurnTab")
        self.add_nav_button("Deslop Tool", "DeslopTab")
        self.add_nav_button("Validate JSONL", "ValidateTab")
        self.add_nav_button("Character Counter", "CharCounterTab")
        self.add_nav_button("Remove Sys Prompt", "RemovePromptTab")
        ttk.Separator(self.nav_frame, orient=HORIZONTAL).pack(fill=X, pady=10)
        self.add_nav_button("TXT -> JSON", "TxtToJsonTab")
        self.add_nav_button("JSON -> JSONL", "JsonToJsonlTab")
        self.add_nav_button("Pre-train Convert", "PretrainConvertTab")
        self.add_nav_button("Normalize Unicode", "UnicodeTab")

        log_frame = ttk.LabelFrame(self, text="Log Output", padding=5)
        log_frame.pack(fill=X, expand=False, padx=10, pady=10)
        
        self.log_text = tk.Text(log_frame, height=10, wrap='word', state='disabled', font=("Courier New", 9))
        self.log_text.pack(side=LEFT, fill=X, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill='y')
        self.log_text['yscrollcommand'] = scrollbar.set

        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

        self.show_frame("CombineTab")
        print("Dataset Toolkit v2.4 Loaded. All systems nominal.")

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

class BaseTab(ttk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

class CombineTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Combine JSONL Files", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Combine multiple .jsonl files from a folder into one.", bootstyle="primary").pack(fill=X, pady=10)
        in_dir_var = self.controller.create_io_widgets(self, 'folder', "Input Folder:")
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Combination", command=lambda: self.controller.execute_tool(combine_jsonl_files, "Combine JSONL", input_dir=in_dir_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)
class AsterisksTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Clean Asterisks", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Remove enclosing asterisks (e.g., *word*) from a .jsonl file.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Cleaning", command=lambda: self.controller.execute_tool(clean_asterisks_in_jsonl, "Clean Asterisks", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)
class TrimTurnTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Trim Last User Turn", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Removes the last conversation turn if it's from a user.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        options_frame = ttk.LabelFrame(self, text="Options", padding=10)
        options_frame.pack(fill=X, pady=10)
        conv_key_var, role_key_var, user_role_var = tk.StringVar(value="conversations"), tk.StringVar(value="from"), tk.StringVar(value="human")
        ttk.Label(options_frame, text="Conversation Key:").grid(row=0, column=0, sticky=W, pady=2); ttk.Entry(options_frame, textvariable=conv_key_var).grid(row=0, column=1, sticky=EW, pady=2)
        ttk.Label(options_frame, text="Role Key:").grid(row=1, column=0, sticky=W, pady=2); ttk.Entry(options_frame, textvariable=role_key_var).grid(row=1, column=1, sticky=EW, pady=2)
        ttk.Label(options_frame, text="User Role Name:").grid(row=2, column=0, sticky=W, pady=2); ttk.Entry(options_frame, textvariable=user_role_var).grid(row=2, column=1, sticky=EW, pady=2)
        options_frame.columnconfigure(1, weight=1)
        def run_trim():
            class Args:
                input_file, output_file = in_file_var.get(), out_file_var.get()
                conversation_key, role_key, user_role = conv_key_var.get(), role_key_var.get(), user_role_var.get()
            if not Args.input_file or not Args.output_file:
                messagebox.showerror("Error", "Please specify both an input and output file.")
                return
            self.controller.execute_tool(remove_last_user_turn, "Trim Last Turn", args=Args())
        ttk.Button(self, text="Run Trimming", command=run_trim, bootstyle="success").pack(pady=20)
class DeslopTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Deslop Tool", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Filter conversations containing phrases from a filter file.", bootstyle="primary").pack(fill=X, pady=10)
        
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input Dataset:", [("JSONL files", "*.jsonl")])
        out_dir_var = self.controller.create_io_widgets(self, 'folder', "Output Folder:")
        filter_file_var = self.controller.create_io_widgets(self, 'file', "Filter File:", [("Text files", "*.txt")])
        
        try:
            default_filter_path = self.controller.resource_path("f.txt")
            if os.path.exists(default_filter_path):
                filter_file_var.set(default_filter_path)
        except Exception:
            pass # Silently fail if default file is not found

        # --- NEW: UI for Threshold Options ---
        options_frame = ttk.LabelFrame(self, text="Filtering Mode", padding=10)
        options_frame.pack(fill=X, pady=10)

        use_threshold_var = tk.BooleanVar(value=False)
        
        # Create the spinbox but keep it disabled for now
        threshold_spinbox = ttk.Spinbox(options_frame, from_=0.1, to=10.0, increment=0.1, state="disabled", width=8)
        threshold_spinbox.set(1.5) # A reasonable default value
        
        def toggle_spinbox():
            if use_threshold_var.get():
                threshold_spinbox.configure(state="normal")
            else:
                threshold_spinbox.configure(state="disabled")

        threshold_check = ttk.Checkbutton(
            options_frame,
            text="Use statistical threshold filtering",
            variable=use_threshold_var,
            command=toggle_spinbox,
            bootstyle="primary"
        )
        threshold_check.pack(side=LEFT, padx=5)
        threshold_spinbox.pack(side=LEFT, padx=5)

        def run_deslop_command():
            threshold_value = None
            if use_threshold_var.get():
                try:
                    threshold_value = float(threshold_spinbox.get())
                except ValueError:
                    messagebox.showerror("Invalid Input", "Threshold must be a valid number.")
                    return
            
            self.controller.execute_tool(
                deslop_dataset, 
                "Deslop Tool", 
                dataset_file=in_file_var.get(), 
                output_dir=out_dir_var.get(), 
                filter_files=[filter_file_var.get()],
                threshold=threshold_value
            )

        run_btn = ttk.Button(self, text="Run Deslop", command=run_deslop_command, bootstyle="success")
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
class JsonToJsonlTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="JSON to JSONL", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Convert a standard .json file to a .jsonl file.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSON files", "*.json")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Conversion", command=lambda: self.controller.execute_tool(convert_json_to_jsonl, "JSON to JSONL", input_path=in_file_var.get(), output_path=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)
class UnicodeTab(BaseTab):
    def __init__(self, parent, controller):
        super().__init__(parent, controller)
        ttk.Label(self, text="Normalize Unicode", font=("-size 12 -weight bold")).pack(pady=10)
        ttk.Label(self, text="Converts Unicode escapes (e.g., \\u201c) to actual characters (“).", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.controller.create_io_widgets(self, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.controller.create_io_widgets(self, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(self, text="Run Normalization", command=lambda: self.controller.execute_tool(normalize_unicode_in_jsonl, "Normalize Unicode", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
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