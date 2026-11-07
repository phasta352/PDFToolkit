"""Daily Python Project - Private PDF Toolkit with Python and CustomTkinter, Day 1.

HOW IT WORKS
    1. The App class builds the window: a Merge tab and a Split tab, and
       a status line at the bottom that says what just happened.
    2. A GUI program does not run from top to bottom like a script.
       mainloop() waits for clicks, and each button calls the method you
       gave it with command=.
    3. pypdf does the PDF work. PdfWriter.append() adds all the pages of
       a file, and add_page() adds a single page.
    4. Split understands page ranges like "1-3, 5", the same way the print
       dialog of your computer does.

RUN IT
    pip install customtkinter pypdf
    python pdf_toolkit.py
"""

import os
import re
from pathlib import Path
from tkinter import filedialog, messagebox

import customtkinter as ctk
from pypdf import PdfReader, PdfWriter

ctk.set_appearance_mode("system")      # follow the light or dark mode of your computer
ctk.set_default_color_theme("blue")

PDF_FILES = [("PDF files", "*.pdf")]


def plural(n, word):
    return f"{n} {word}" if n == 1 else f"{n} {word}s"


def size_text(path):
    size = os.path.getsize(path)
    return f"{size / 1024:.0f} KB" if size < 1024 * 1024 else f"{size / 1024 / 1024:.1f} MB"


def parse_pages(text, total):
    """Turn "1-3, 5" into the page indexes [0, 1, 2, 4].
    People count pages from 1, but pypdf counts them from 0."""
    pages = []
    for part in text.replace(" ", "").split(","):
        if not part:
            continue
        if not re.fullmatch(r"\d+(-\d+)?", part):     # a number, or two numbers with a dash
            raise ValueError(f'"{part}" is not a page number. Use numbers, like 1-3, 5')
        if "-" in part:
            first, last = int(part.split("-")[0]), int(part.split("-")[1])
            if first > last:
                raise ValueError(f"Write {part} from the lower page to the higher one, like {last}-{first}")
            numbers = range(first, last + 1)
        else:
            numbers = [int(part)]
        for n in numbers:
            if not 1 <= n <= total:
                raise ValueError(f"Page {n} does not exist. This PDF has {plural(total, 'page')}.")
            pages.append(n - 1)
    if not pages:
        raise ValueError("Type the pages you want, for example 1-3, 5")
    return pages


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("PDF Toolkit")
        self.geometry("780x560")
        self.minsize(660, 480)
        self.files = []            # the PDFs to merge, in order: {"path", "pages"}
        self.selected = None       # index of the selected row in the merge list
        self.split_path = None     # the PDF chosen in the Split tab

        self.tabs = ctk.CTkTabview(self, segmented_button_font=ctk.CTkFont(size=15, weight="bold"))
        self.tabs.pack(fill="both", expand=True, padx=16, pady=(6, 0))
        self.build_merge_tab(self.tabs.add("Merge"))
        self.build_split_tab(self.tabs.add("Split"))

        self.status = ctk.CTkLabel(self, text="Your files never leave this computer.", anchor="w", text_color="gray")
        self.status.pack(fill="x", padx=24, pady=(2, 10))

    # ------------------------------------------------------------ Merge tab
    def build_merge_tab(self, tab):
        title(tab, "Merge PDFs", "Add files, put them in order, and save them as one PDF.")
        buttons = ctk.CTkFrame(tab, fg_color="transparent")
        buttons.pack(fill="x", padx=8, pady=(12, 8))
        ctk.CTkButton(buttons, text="Add PDFs", width=110, command=self.choose_files).pack(side="left")
        for text, command in [("Move up", lambda: self.move(-1)), ("Move down", lambda: self.move(1)), ("Remove", self.remove)]:
            ctk.CTkButton(buttons, text=text, width=100, fg_color="transparent", border_width=1,
                          text_color=("gray10", "gray90"), command=command).pack(side="left", padx=(8, 0))

        self.file_list = ctk.CTkScrollableFrame(tab)
        self.file_list.pack(fill="both", expand=True, padx=8)

        bottom = ctk.CTkFrame(tab, fg_color="transparent")
        bottom.pack(fill="x", padx=8, pady=(10, 4))
        self.total = ctk.CTkLabel(bottom, text="No files yet")
        self.total.pack(side="left")
        ctk.CTkButton(bottom, text="Merge and save", width=160, height=36, command=self.merge).pack(side="right")

    def choose_files(self):
        paths = filedialog.askopenfilenames(title="Choose PDFs", filetypes=PDF_FILES)
        self.add_files(paths)

    def add_files(self, paths):
        for path in paths:
            try:
                reader = PdfReader(path)
                if reader.is_encrypted:
                    messagebox.showerror("PDF Toolkit", f"{Path(path).name} has a password, so it cannot be merged.")
                    continue
                self.files.append({"path": Path(path), "pages": len(reader.pages)})
            except Exception as error:             # a damaged file, or not a PDF at all
                messagebox.showerror("PDF Toolkit", f"Could not open {Path(path).name}:\n{error}")
        self.show_files()

    def show_files(self):
        """Draw one row for each file. The selected row gets a blue background."""
        for row in self.file_list.winfo_children():
            row.destroy()
        for i, f in enumerate(self.files):
            color = ("#dbeafe", "#1e3a5f") if i == self.selected else "transparent"
            row = ctk.CTkFrame(self.file_list, fg_color=color, corner_radius=6)
            row.pack(fill="x", pady=1)
            cells = [(f"{i + 1}.", 30), (f["path"].name, 340), (plural(f["pages"], "page"), 90), (size_text(f["path"]), 80)]
            for column, (text, width) in enumerate(cells):
                label = ctk.CTkLabel(row, text=text, width=width, anchor="w")
                label.grid(row=0, column=column, padx=6, pady=4)
                label.bind("<Button-1>", lambda event, i=i: self.select(i))
            row.bind("<Button-1>", lambda event, i=i: self.select(i))
        pages = sum(f["pages"] for f in self.files)
        self.total.configure(text=f"{plural(len(self.files), 'file')}, {plural(pages, 'page')}" if self.files else "No files yet")

    def select(self, i):
        self.selected = i
        self.show_files()

    def move(self, step):
        """Swap the selected file with the one above (step -1) or below (step 1)."""
        if self.selected is None:
            return
        j = self.selected + step
        if 0 <= j < len(self.files):
            self.files[self.selected], self.files[j] = self.files[j], self.files[self.selected]
            self.selected = j
            self.show_files()

    def remove(self):
        if self.selected is not None:
            self.files.pop(self.selected)
            self.selected = None
            self.show_files()

    def merge(self):
        if len(self.files) < 2:
            messagebox.showinfo("PDF Toolkit", "Add at least two PDFs to merge.")
            return
        target = filedialog.asksaveasfilename(title="Save the merged PDF", initialfile="merged.pdf",
                                              defaultextension=".pdf", filetypes=PDF_FILES)
        if target:
            self.merge_to(target)

    def merge_to(self, target):
        writer = PdfWriter()
        for f in self.files:
            writer.append(f["path"])          # all the pages of this file, in order
        writer.write(target)
        pages = sum(f["pages"] for f in self.files)
        self.status.configure(text=f"Saved {Path(target).name}: {plural(pages, 'page')} from {plural(len(self.files), 'file')}.")

    # ------------------------------------------------------------ Split tab
    def build_split_tab(self, tab):
        title(tab, "Split a PDF", "Keep only the pages you need, or save every page as its own file.")
        row = ctk.CTkFrame(tab, fg_color="transparent")
        row.pack(fill="x", padx=8, pady=(12, 8))
        ctk.CTkButton(row, text="Choose PDF", width=110, command=self.choose_split_file).pack(side="left")
        self.split_label = ctk.CTkLabel(row, text="No file chosen", text_color="gray")
        self.split_label.pack(side="left", padx=12)

        ctk.CTkLabel(tab, text="Pages to keep").pack(anchor="w", padx=8, pady=(14, 4))
        self.pages_entry = ctk.CTkEntry(tab, width=320, placeholder_text="For example: 1-3, 5")
        self.pages_entry.pack(anchor="w", padx=8)

        self.mode = ctk.StringVar(value="one")
        ctk.CTkRadioButton(tab, text="Save these pages as one new PDF", variable=self.mode, value="one").pack(anchor="w", padx=8, pady=(16, 6))
        ctk.CTkRadioButton(tab, text="Save each page as its own PDF", variable=self.mode, value="each").pack(anchor="w", padx=8)
        ctk.CTkButton(tab, text="Split and save", width=160, height=36, command=self.split).pack(anchor="e", padx=8, pady=(24, 4), side="bottom")

    def choose_split_file(self):
        path = filedialog.askopenfilename(title="Choose a PDF", filetypes=PDF_FILES)
        if path:
            self.load_split_file(path)

    def load_split_file(self, path):
        self.split_path = Path(path)
        pages = len(PdfReader(path).pages)
        self.split_label.configure(text=f"{self.split_path.name}  ({plural(pages, 'page')})", text_color=("gray10", "gray90"))

    def split(self):
        if self.split_path is None:
            messagebox.showinfo("PDF Toolkit", "Choose a PDF first.")
            return
        reader = PdfReader(self.split_path)
        text = self.pages_entry.get()
        if not text.strip() and self.mode.get() == "each":
            text = f"1-{len(reader.pages)}"            # no pages typed: every page becomes a file
        try:
            pages = parse_pages(text, len(reader.pages))
        except ValueError as error:
            messagebox.showerror("PDF Toolkit", str(error))
            return
        if self.mode.get() == "one":
            target = filedialog.asksaveasfilename(title="Save the new PDF", initialfile=f"{self.split_path.stem}_pages.pdf",
                                                  defaultextension=".pdf", filetypes=PDF_FILES)
            if target:
                self.save_pages(reader, pages, target)
        else:
            folder = filedialog.askdirectory(title="Choose a folder for the pages")
            if folder:
                self.save_each_page(reader, pages, folder)

    def save_pages(self, reader, pages, target):
        writer = PdfWriter()
        for i in pages:
            writer.add_page(reader.pages[i])
        writer.write(target)
        self.status.configure(text=f"Saved {Path(target).name} with {plural(len(pages), 'page')}.")

    def save_each_page(self, reader, pages, folder):
        for i in pages:
            writer = PdfWriter()
            writer.add_page(reader.pages[i])
            writer.write(Path(folder) / f"{self.split_path.stem}_page_{i + 1}.pdf")
        self.status.configure(text=f"Saved {plural(len(pages), 'file')} in {Path(folder).name}.")


def title(tab, text, subtitle):
    """The big title and the grey line under it, at the top of each tab."""
    ctk.CTkLabel(tab, text=text, font=ctk.CTkFont(size=22, weight="bold")).pack(anchor="w", padx=8, pady=(4, 0))
    ctk.CTkLabel(tab, text=subtitle, text_color="gray").pack(anchor="w", padx=8)


if __name__ == "__main__":
    app = App()
    app.mainloop()          # wait for clicks until the window is closed