import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import sys
from pathlib import Path
import ttkbootstrap as bstrap
from ttkbootstrap.constants import *

# --- Import ALL your refactored tool functions ---
# Make sure your scripts are in a 'tools' subfolder with an __init__.py file
try:
    from tools.combinejsonl import combine_jsonl_files
    from tools.cleanasterisks import process_jsonl_file as clean_asterisks_in_jsonl
    from tools.cleanupjsonl_last_user_turn import main as remove_last_user_turn
    from tools.DeslopTool import filter_dataset as deslop_dataset
    from tools.convert_json_to_jsonl import convert_json_to_jsonl
    from tools.convert_txt_to_Json import convert_multiple_txt_to_json
    from tools.convert_unicode_to_characters import normalize_unicode_in_jsonl
    from tools.validate_dataset import validate_and_clean_jsonl
    # --- NEW IMPORT (Token Counter REMOVED) ---
    from tools.remove_system_prompt import remove_system_prompt_from_jsonl
except ImportError as e:
    messagebox.showerror("Fatal Error", f"Could not import a tool script. Please ensure the 'tools' subfolder exists and contains all required scripts.\n\nError: {e}")
    sys.exit(1)


# A helper class to redirect print statements to the GUI's log window
class TextRedirector:
    def __init__(self, widget):
        self.widget = widget

    def write(self, text):
        self.widget.configure(state='normal')
        self.widget.insert('end', text)
        self.widget.see('end') # Auto-scroll
        self.widget.configure(state='disabled')
        self.widget.update_idletasks() # Force GUI update

    def flush(self):
        pass

# --- Main Application Class ---
class DatasetToolkit(bstrap.Window):
    def __init__(self):
        super().__init__(themename="superhero", title="Dataset Processing Toolkit")
        self.geometry("800x650") # Reverted to original size
        self.minsize(700, 550)

        container = ttk.Frame(self, padding=10)
        container.pack(fill=BOTH, expand=True)

        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill=BOTH, expand=True, pady=(0, 10))

        # --- Create ALL the tabs ---
        self.create_combine_tab()
        self.create_clean_asterisks_tab()
        self.create_remove_last_turn_tab()
        self.create_deslop_tab()
        self.create_txt_to_json_tab()
        self.create_json_to_jsonl_tab()
        self.create_unicode_normalize_tab()
        self.create_validate_tab()
        # --- NEW TAB (Token Counter REMOVED) ---
        self.create_remove_system_prompt_tab()


        # Log window
        log_frame = ttk.LabelFrame(container, text="Log Output", padding=5)
        log_frame.pack(fill=BOTH, expand=True)
        
        self.log_text = tk.Text(log_frame, height=10, wrap='word', state='disabled', font=("Courier New", 9))
        self.log_text.pack(side=LEFT, fill=BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(log_frame, orient='vertical', command=self.log_text.yview)
        scrollbar.pack(side=RIGHT, fill='y')
        self.log_text['yscrollcommand'] = scrollbar.set

        sys.stdout = TextRedirector(self.log_text)
        sys.stderr = TextRedirector(self.log_text)

        print("Dataset Toolkit v1.1 Loaded. Select a tool to begin.")

    def create_io_widgets(self, parent, io_type='file', label_text="Input File:", file_types=None):
        frame = ttk.Frame(parent)
        label = ttk.Label(frame, text=label_text, width=15)
        label.pack(side=LEFT, padx=5)

        entry_var = tk.StringVar()
        entry = ttk.Entry(frame, textvariable=entry_var)
        entry.pack(side=LEFT, expand=True, fill=X, padx=5)

        def select_path():
            path = ""
            if io_type == 'file':
                path = filedialog.askopenfilename(filetypes=file_types)
            elif io_type == 'folder':
                path = filedialog.askdirectory()
            elif io_type == 'save_file':
                path = filedialog.asksaveasfilename(filetypes=file_types, defaultextension=file_types[0][1] if file_types else None)
            if path:
                entry_var.set(path)

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
            messagebox.showinfo("Success", f"{title} completed successfully!")
        except Exception as e:
            error_message = f"An error occurred during {title}:\n\n{e}"
            print(f"\n--- ERROR: {error_message} ---")
            messagebox.showerror("Error", error_message)

    # --- TAB Implementations ---

    def create_combine_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Combine JSONL")
        ttk.Label(tab, text="Combine multiple .jsonl files from a folder into one.", bootstyle="primary").pack(fill=X, pady=10)
        in_dir_var = self.create_io_widgets(tab, 'folder', "Input Folder:")
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(tab, text="Run Combination", command=lambda: self.execute_tool(combine_jsonl_files, "Combine JSONL", input_dir=in_dir_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

    def create_clean_asterisks_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Clean Asterisks")
        ttk.Label(tab, text="Remove enclosing asterisks (e.g., *word*) from a .jsonl file.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.create_io_widgets(tab, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(tab, text="Run Cleaning", command=lambda: self.execute_tool(clean_asterisks_in_jsonl, "Clean Asterisks", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)
        
    def create_remove_last_turn_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Trim Last Turn")
        ttk.Label(tab, text="Removes the last conversation turn if it's from a user.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.create_io_widgets(tab, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        
        options_frame = ttk.LabelFrame(tab, text="Options", padding=10)
        options_frame.pack(fill=X, pady=10)
        
        conv_key, role_key, user_role = tk.StringVar(value="conversations"), tk.StringVar(value="from"), tk.StringVar(value="human")
        
        ttk.Label(options_frame, text="Conversation Key:").grid(row=0, column=0, sticky=W, pady=2); ttk.Entry(options_frame, textvariable=conv_key).grid(row=0, column=1, sticky=EW, pady=2)
        ttk.Label(options_frame, text="Role Key:").grid(row=1, column=0, sticky=W, pady=2); ttk.Entry(options_frame, textvariable=role_key).grid(row=1, column=1, sticky=EW, pady=2)
        ttk.Label(options_frame, text="User Role Name:").grid(row=2, column=0, sticky=W, pady=2); ttk.Entry(options_frame, textvariable=user_role).grid(row=2, column=1, sticky=EW, pady=2)
        options_frame.columnconfigure(1, weight=1)

        def run_trim():
            class Args:
                input_file, output_file = in_file_var.get(), out_file_var.get()
                conversation_key, role_key, user_role = conv_key.get(), role_key.get(), user_role.get()
            self.execute_tool(remove_last_user_turn, "Trim Last Turn", args=Args())
        ttk.Button(tab, text="Run Trimming", command=run_trim, bootstyle="success").pack(pady=20)

    def create_deslop_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Deslop Tool")
        ttk.Label(tab, text="Filter conversations based on a list of 'slop' phrases.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.create_io_widgets(tab, 'file', "Input Dataset:", [("JSONL files", "*.jsonl")])
        out_dir_var = self.create_io_widgets(tab, 'folder', "Output Folder:")
        filter_files_var = self.create_io_widgets(tab, 'file', "Filter File:", [("Text files", "*.txt")])
        run_btn = ttk.Button(tab, text="Run Deslop", command=lambda: self.execute_tool(deslop_dataset, "Deslop Tool", dataset_file=in_file_var.get(), output_dir=out_dir_var.get(), filter_files=[filter_files_var.get()]), bootstyle="success")
        run_btn.pack(pady=20)

    def create_txt_to_json_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="TXT to JSON")
        ttk.Label(tab, text="Convert all .txt files in a folder to a single .json file.", bootstyle="primary").pack(fill=X, pady=10)
        in_dir_var = self.create_io_widgets(tab, 'folder', "Input Folder:")
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSON files", "*.json")])
        run_btn = ttk.Button(tab, text="Run Conversion", command=lambda: self.execute_tool(convert_multiple_txt_to_json, "TXT to JSON", input_directory=in_dir_var.get(), output_file_path=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

    def create_json_to_jsonl_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="JSON to JSONL")
        ttk.Label(tab, text="Convert a standard .json file to a .jsonl file.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.create_io_widgets(tab, 'file', "Input File:", [("JSON files", "*.json")])
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(tab, text="Run Conversion", command=lambda: self.execute_tool(convert_json_to_jsonl, "JSON to JSONL", input_path=in_file_var.get(), output_path=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)
        
    def create_unicode_normalize_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Normalize Unicode")
        ttk.Label(tab, text="Converts Unicode escapes (e.g., \\u201c) to actual characters (“).", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.create_io_widgets(tab, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(tab, text="Run Normalization", command=lambda: self.execute_tool(normalize_unicode_in_jsonl, "Normalize Unicode", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

    def create_validate_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Validate JSONL")
        ttk.Label(tab, text="Validates each line is a valid {'text': '...'} JSON object.", bootstyle="primary").pack(fill=X, pady=10)
        in_file_var = self.create_io_widgets(tab, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])
        run_btn = ttk.Button(tab, text="Run Validation", command=lambda: self.execute_tool(validate_and_clean_jsonl, "Validate JSONL", input_file=in_file_var.get(), output_file=out_file_var.get()), bootstyle="success")
        run_btn.pack(pady=20)

    # --- NEW TAB IMPLEMENTATION ---

    def create_remove_system_prompt_tab(self):
        tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(tab, text="Remove Sys Prompt")
        ttk.Label(tab, text="Removes the first message in a conversation if it's a system prompt.", bootstyle="primary").pack(fill=X, pady=10)
        
        in_file_var = self.create_io_widgets(tab, 'file', "Input File:", [("JSONL files", "*.jsonl")])
        out_file_var = self.create_io_widgets(tab, 'save_file', "Output File:", [("JSONL files", "*.jsonl")])

        options_frame = ttk.LabelFrame(tab, text="Options", padding=10)
        options_frame.pack(fill=X, pady=10)
        
        system_role_var = tk.StringVar(value="system")
        
        ttk.Label(options_frame, text="System Role Name:").grid(row=0, column=0, sticky=W, pady=2)
        ttk.Entry(options_frame, textvariable=system_role_var).grid(row=0, column=1, sticky=EW, pady=2)
        options_frame.columnconfigure(1, weight=1)

        run_btn = ttk.Button(tab, text="Run Removal", 
                             command=lambda: self.execute_tool(
                                 remove_system_prompt_from_jsonl, 
                                 "Remove System Prompt",
                                 input_file=in_file_var.get(),
                                 output_file=out_file_var.get(),
                                 system_role=system_role_var.get()
                             ), 
                             bootstyle="success")
        run_btn.pack(pady=20)


if __name__ == '__main__':
    app = DatasetToolkit()
    app.mainloop()