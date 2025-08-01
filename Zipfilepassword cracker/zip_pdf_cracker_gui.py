import os
import threading
import zipfile
import PyPDF2
import tkinter as tk
from tkinter import filedialog, messagebox, ttk, BooleanVar
from tkinterdnd2 import TkinterDnD, DND_FILES

class CrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("ZIP & PDF Password Cracker")
        self.root.geometry("600x400")
        self.root.configure(bg="#f0f0f0")
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.drop_file)

        self.selected_files = []
        self.passwords = []
        self.stop_flag = False
        self.paused = False
        self.threads = []
        self.auto_open = BooleanVar(value=True)

        self.create_widgets()

    def create_widgets(self):
        tk.Label(self.root, text="Drag & drop files or click 'Select Files'", bg="#f0f0f0").pack(pady=5)

        self.file_listbox = tk.Listbox(self.root, selectmode=tk.MULTIPLE, width=80)
        self.file_listbox.pack(pady=5)

        tk.Button(self.root, text="Select Files", command=self.select_files).pack()

        tk.Label(self.root, text="Select Wordlist", bg="#f0f0f0").pack(pady=5)
        self.wordlist_entry = tk.Entry(self.root, width=60)
        self.wordlist_entry.pack()
        tk.Button(self.root, text="Browse Wordlist", command=self.browse_wordlist).pack()

        tk.Checkbutton(self.root, text="Auto-open on success", variable=self.auto_open, bg="#f0f0f0").pack(pady=5)

        self.progress = ttk.Progressbar(self.root, length=400, mode='determinate')
        self.progress.pack(pady=10)

        control_frame = tk.Frame(self.root, bg="#f0f0f0")
        control_frame.pack(pady=5)

        self.start_btn = tk.Button(control_frame, text="Start", command=self.start_cracking)
        self.start_btn.grid(row=0, column=0, padx=5)

        self.pause_btn = tk.Button(control_frame, text="Pause", command=self.toggle_pause, state="disabled")
        self.pause_btn.grid(row=0, column=1, padx=5)

        self.reset_btn = tk.Button(control_frame, text="Reset", command=self.reset)
        self.reset_btn.grid(row=0, column=2, padx=5)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("ZIP & PDF files", "*.zip *.pdf")])
        self.add_files(files)

    def drop_file(self, event):
        files = self.root.tk.splitlist(event.data)
        self.add_files(files)

    def add_files(self, files):
        for file in files:
            if file not in self.selected_files and file.lower().endswith(('.zip', '.pdf')):
                self.selected_files.append(file)
                self.file_listbox.insert(tk.END, file)

    def browse_wordlist(self):
        path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if path:
            self.wordlist_entry.delete(0, tk.END)
            self.wordlist_entry.insert(0, path)

    def load_passwords(self):
        path = self.wordlist_entry.get()
        if not os.path.isfile(path):
            messagebox.showerror("Error", "Wordlist file not found.")
            return False
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            self.passwords = [line.strip() for line in f]
        return True

    def start_cracking(self):
        if not self.selected_files:
            messagebox.showerror("Error", "No files selected.")
            return
        if not self.load_passwords():
            return

        self.stop_flag = False
        self.paused = False
        self.pause_btn.config(state="normal")
        self.progress.config(value=0, maximum=len(self.selected_files))

        for file in self.selected_files:
            t = threading.Thread(target=self.crack_file, args=(file,))
            self.threads.append(t)
            t.start()

    def toggle_pause(self):
        self.paused = not self.paused
        self.pause_btn.config(text="Resume" if self.paused else "Pause")

    def reset(self):
        self.stop_flag = True
        self.paused = False
        self.threads.clear()
        self.file_listbox.delete(0, tk.END)
        self.selected_files.clear()
        self.progress.config(value=0)
        self.pause_btn.config(state="disabled", text="Pause")

    def crack_file(self, filepath):
        for pwd in self.passwords:
            if self.stop_flag:
                break
            while self.paused:
                threading.Event().wait(0.2)

            try:
                if filepath.lower().endswith('.zip'):
                    with zipfile.ZipFile(filepath) as zf:
                        zf.extractall(pwd=bytes(pwd, 'utf-8'))
                elif filepath.lower().endswith('.pdf'):
                    with open(filepath, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        if reader.is_encrypted and not reader.decrypt(pwd):
                            continue
                self.success_popup(filepath, pwd)
                if self.auto_open.get():
                    os.startfile(filepath)
                break
            except Exception:
                continue
        self.progress.step(1)

    def success_popup(self, file, pwd):
        messagebox.showinfo("Success", f"Password for {os.path.basename(file)}: {pwd}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = CrackerGUI(root)
    root.mainloop()
