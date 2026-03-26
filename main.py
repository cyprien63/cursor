import customtkinter as ctk
import os
from PIL import Image, ImageTk
import cursor_logic
import updater
import threading
import time

# --- Visual Constants ---
COLOR_BG = "#1A1A1D"
COLOR_SIDEBAR = "#242526"
COLOR_CARD = "#2C2F33"
COLOR_ACCENT = "#4E9CCF"
COLOR_TEXT_MAIN = "#E4E6EB"
COLOR_TEXT_ALT = "#B0B3B8"
FONT_TITLE = ("Inter", 24, "bold")
FONT_SUBTITLE = ("Inter", 18, "bold")
FONT_NORMAL = ("Inter", 13)
FONT_SMALL = ("Inter", 11)

class CursorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cursor Studio - Premium Edition")
        self.geometry("1100x800")
        self.configure(fg_color=COLOR_BG)
        ctk.set_appearance_mode("dark")

        # Configuration
        self.cursor_dir = "curseur"
        self.themes = []
        self.current_view = "startup"
        self.preview_images = {}

        self.setup_ui()
        self.start_startup_sequence()

    def setup_ui(self):
        # --- Header ---
        self.header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=COLOR_SIDEBAR, border_width=1, border_color="#333")
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        title_container.pack(side="left", padx=30, fill="y")
        ctk.CTkLabel(title_container, text="Cursor Studio", font=FONT_TITLE, text_color=COLOR_TEXT_MAIN).pack(side="left", pady=10)

        self.back_btn = ctk.CTkButton(self.header, text="← Collections", width=120, height=36, 
                                     fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
                                     text_color=COLOR_ACCENT, hover_color="#333", state="disabled",
                                     command=self.show_home)
        self.back_btn.pack(side="left", padx=20)

        self.reset_btn = ctk.CTkButton(self.header, text="Reset Windows Default", width=180, height=36,
                                      fg_color="#A93226", hover_color="#922B21", font=ctk.CTkFont(weight="bold"),
                                      command=self.on_reset)
        self.reset_btn.pack(side="right", padx=30)

        # --- Progress Bar ---
        self.progress_bar = ctk.CTkProgressBar(self, height=4, corner_radius=0, fg_color=COLOR_BG, progress_color=COLOR_ACCENT)
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        # --- Main Container ---
        self.view_container = ctk.CTkFrame(self, fg_color="transparent")
        self.view_container.pack(fill="both", expand=True, padx=30, pady=(10, 20))

        # Main Scrollable Content (Always exists from now on)
        self.scrollable_content = ctk.CTkScrollableFrame(self.view_container, fg_color="transparent")
        self.scrollable_content.pack(fill="both", expand=True)

        # --- Startup Overlay (Only for initial boot) ---
        self.startup_overlay = ctk.CTkFrame(self, fg_color=COLOR_BG)
        self.startup_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        self.loading_label = ctk.CTkLabel(self.startup_overlay, text="Initializing Studio", font=FONT_TITLE, text_color=COLOR_TEXT_MAIN)
        self.loading_label.place(relx=0.5, rely=0.45, anchor="center")
        
        self.loading_sublabel = ctk.CTkLabel(self.startup_overlay, text="Checking for updates and preparing assets...", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT)
        self.loading_sublabel.place(relx=0.5, rely=0.52, anchor="center")
        
        self.startup_progress = ctk.CTkProgressBar(self.startup_overlay, width=400, height=8, progress_color=COLOR_ACCENT)
        self.startup_progress.place(relx=0.5, rely=0.6, anchor="center")
        self.startup_progress.start()

    def start_startup_sequence(self):
        def task():
            try:
                updater.update_repository()
                time.sleep(1)
                self.themes = self.get_themes()
                self.after(0, self.finish_startup)
            except Exception as e:
                print(f"Startup error: {e}")
                self.after(0, self.finish_startup)
        
        threading.Thread(target=task, daemon=True).start()

    def finish_startup(self):
        self.startup_overlay.destroy()
        self.current_view = "home"
        self.show_home()

    def show_nav_loading(self):
        self.progress_bar.set(0)
        self.progress_bar.start()

    def hide_nav_loading(self):
        self.progress_bar.stop()
        self.progress_bar.set(1)
        self.after(500, lambda: self.progress_bar.set(0))

    def get_themes(self):
        if not os.path.exists(self.cursor_dir):
            return []
        return [d for d in os.listdir(self.cursor_dir) if os.path.isdir(os.path.join(self.cursor_dir, d))]

    def show_home(self):
        self.current_view = "home"
        self.selected_theme = None
        self.back_btn.configure(state="disabled")
        self.show_nav_loading()

        def build_task():
            def clear_and_build():
                # Safety: clear carefully
                for widget in self.scrollable_content.winfo_children():
                    widget.destroy()

                section_title = ctk.CTkLabel(self.scrollable_content, text="Available Collections", font=FONT_SUBTITLE, text_color=COLOR_TEXT_MAIN)
                section_title.pack(anchor="w", padx=10, pady=(10, 20))

                if not self.themes:
                    ctk.CTkLabel(self.scrollable_content, text="No cursor packs found in 'curseur/' folder.\nMake sure you have folders inside 'curseur/'.", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(pady=50)
                else:
                    theme_grid = ctk.CTkFrame(self.scrollable_content, fg_color="transparent")
                    theme_grid.pack(fill="both", expand=True)
                    cols = 3
                    for i, theme in enumerate(self.themes):
                        self.build_theme_card(theme_grid, theme, i, cols)
                
                self.hide_nav_loading()
            
            self.after(0, clear_and_build)

        threading.Thread(target=build_task, daemon=True).start()

    def build_theme_card(self, parent, theme, index, cols):
        card = ctk.CTkFrame(parent, width=320, height=240, corner_radius=18, fg_color=COLOR_CARD, border_width=1, border_color="#3E4147")
        card.grid(row=index // cols, column=index % cols, padx=15, pady=15, sticky="nsew")
        card.grid_propagate(False)

        icon_frame = ctk.CTkFrame(card, fg_color="#3E4147", width=100, height=100, corner_radius=50)
        icon_frame.pack(pady=(30, 15))
        icon_frame.pack_propagate(False)

        theme_path = os.path.join(self.cursor_dir, theme)
        preview_img = self.get_theme_preview(theme_path)
        
        if preview_img:
            img_label = ctk.CTkLabel(icon_frame, text="", image=preview_img)
        else:
            img_label = ctk.CTkLabel(icon_frame, text="✨", font=ctk.CTkFont(size=40))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(card, text=theme, font=ctk.CTkFont(size=18, weight="bold"), text_color=COLOR_TEXT_MAIN).pack()
        ctk.CTkButton(card, text="Explore Pack", width=180, height=40, corner_radius=20,
                     fg_color=COLOR_ACCENT, hover_color="#36719F",
                     command=lambda t=theme: self.show_theme_detail(t)).pack(pady=(20, 10))

    def get_theme_preview(self, theme_path):
        if theme_path in self.preview_images:
            return self.preview_images[theme_path]
        try:
            files = [f for f in os.listdir(theme_path) if f.endswith((".ani", ".cur"))]
            if not files: return None
            path = os.path.join(theme_path, files[0])
            pil_img = cursor_logic.get_cursor_preview(path, size=64)
            if pil_img:
                ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(64, 64))
                self.preview_images[theme_path] = ctk_img
                return ctk_img
        except: pass
        return None

    def show_theme_detail(self, theme):
        self.current_view = "theme_detail"
        self.selected_theme = theme
        self.back_btn.configure(state="normal")
        self.show_nav_loading()

        def build_task():
            def clear_and_build():
                for widget in self.scrollable_content.winfo_children():
                    widget.destroy()

                header_area = ctk.CTkFrame(self.scrollable_content, fg_color="#2C3E50", corner_radius=15, height=120)
                header_area.pack(fill="x", padx=10, pady=(10, 30))
                header_area.pack_propagate(False)

                info_box = ctk.CTkFrame(header_area, fg_color="transparent")
                info_box.pack(side="left", padx=30, fill="y")
                ctk.CTkLabel(info_box, text=theme, font=FONT_SUBTITLE, text_color="white").pack(anchor="w", pady=(25, 0))
                ctk.CTkLabel(info_box, text=f"Custom cursor collection", font=FONT_NORMAL, text_color="#BDC3C7").pack(anchor="w")

                ctk.CTkButton(header_area, text="Install Complete Theme", width=220, height=45, corner_radius=22,
                             fg_color="#27AE60", hover_color="#229954", font=ctk.CTkFont(weight="bold"),
                             command=self.on_apply_theme).pack(side="right", padx=30)

                cursor_grid = ctk.CTkFrame(self.scrollable_content, fg_color="transparent")
                cursor_grid.pack(fill="both", expand=True)

                theme_path = os.path.join(self.cursor_dir, theme)
                files = sorted(os.listdir(theme_path))
                curs_files = [f for f in files if f.endswith((".ani", ".cur"))]
                
                cols = 5
                for i, filename in enumerate(curs_files):
                    self.build_cursor_card(cursor_grid, theme_path, filename, i, cols)
                
                self.hide_nav_loading()

            self.after(0, clear_and_build)

        threading.Thread(target=build_task, daemon=True).start()

    def build_cursor_card(self, parent, theme_path, filename, index, cols):
        base_name = os.path.splitext(filename)[0]
        display_name = base_name.split(" ", 1)[1] if " " in base_name else base_name
        
        card = ctk.CTkFrame(parent, width=170, height=190, corner_radius=12, border_width=2)
        card.grid(row=index // cols, column=index % cols, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        preview_box = ctk.CTkFrame(card, fg_color="#34373C", width=60, height=60, corner_radius=10)
        preview_box.pack(pady=(15, 5))
        preview_box.pack_propagate(False)

        path = os.path.join(theme_path, filename)
        pil_img = cursor_logic.get_cursor_preview(path, size=48)
        if pil_img:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
            img_label = ctk.CTkLabel(preview_box, text="", image=ctk_img)
        else:
            img_label = ctk.CTkLabel(preview_box, text="🖱️", font=ctk.CTkFont(size=30))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        reg_key = cursor_logic.get_role_from_filename(filename)
        role_display = reg_key if reg_key else "Unknown"

        ctk.CTkLabel(card, text=display_name, font=FONT_SMALL, text_color=COLOR_TEXT_MAIN, wraplength=150).pack(pady=(2, 0))
        ctk.CTkLabel(card, text=f"Role: {role_display}", font=ctk.CTkFont(size=10), text_color=COLOR_TEXT_ALT).pack()
        
        ctk.CTkButton(card, text="Apply", width=80, height=26, font=ctk.CTkFont(size=11),
                       fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
                       text_color=COLOR_ACCENT, hover_color="#333",
                       command=lambda f=filename: self.on_set_individual(f)).pack(pady=10)

    def on_set_individual(self, filename):
        reg_key = cursor_logic.get_role_from_filename(filename)
        if reg_key:
            file_path = os.path.abspath(os.path.join(self.cursor_dir, self.selected_theme, filename))
            cursor_logic.set_cursor(reg_key, file_path)
            cursor_logic.apply_cursors()
            print(f"Applied {filename} to {reg_key}")

    def on_apply_theme(self):
        theme_path = os.path.join(self.cursor_dir, self.selected_theme)
        cursor_logic.set_theme(theme_path)

    def on_reset(self):
        cursor_logic.reset_to_default()

if __name__ == "__main__":
    app = CursorApp()
    app.mainloop()
