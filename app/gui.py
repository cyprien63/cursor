import customtkinter as ctk
import os
import sys
from PIL import Image, ImageTk
from . import logic
from . import updater
import threading
import time
import shutil
from tkinter import filedialog, messagebox, simpledialog

def get_base_folder():
    """Returns the base folder for assets. Works for both script and EXE."""
    if getattr(sys, 'frozen', False):
        exe_path = os.path.dirname(sys.executable)
        # If we are in dist/, the root is parent
        if os.path.basename(exe_path).lower() == "dist":
            return os.path.dirname(exe_path)
        return exe_path
    # In script mode, we are in app/, so base is parent
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Visual Constants (Premium Dark Theme) ---
COLOR_BG = "#0F0F12"
COLOR_SIDEBAR = "#18181B"
COLOR_CARD = "#1C1C1E"
COLOR_CARD_HOVER = "#252529"
COLOR_ACCENT = "#3F8CFF"
COLOR_TEXT_MAIN = "#FFFFFF"
COLOR_TEXT_ALT = "#A1A1AA"
COLOR_BORDER = "#27272A"
COLOR_SUCCESS = "#32D74B"
COLOR_DANGER = "#FF453A"

FONT_TITLE = ("Inter", 28, "bold")
FONT_SUBTITLE = ("Inter", 20, "bold")
FONT_NORMAL = ("Inter", 14)
FONT_BOLD = ("Inter", 14, "bold")
FONT_SMALL = ("Inter", 12)

# --- Versioning ---
APP_VERSION = "1.1.0"

class CursorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title(f"Cursor Studio v{APP_VERSION} - Premium Edition")
        self.geometry("1100x800")
        self.configure(fg_color=COLOR_BG)
        ctk.set_appearance_mode("dark")

        # Configuration
        base = get_base_folder()
        os.chdir(base) # CRITICAL: Ensure we are at the root for relative paths and Git
        
        self.cursor_dir = os.path.join(base, "curseur")
        self.repo_url = "https://github.com/cyprien63/cursor.git"
        
        if not os.path.exists(self.cursor_dir):
            os.makedirs(self.cursor_dir)

        self.themes = []
        self.current_view = "startup"
        self.preview_images = {}
        self.dev_mode = False

        self.setup_ui()
        self.start_startup_sequence()

    def setup_ui(self):
        # --- Header ---
        self.header = ctk.CTkFrame(self, height=90, corner_radius=0, fg_color=COLOR_SIDEBAR, border_width=1, border_color=COLOR_BORDER)
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        title_container.pack(side="left", padx=40, fill="y")
        self.title_label = ctk.CTkLabel(title_container, text="Cursor Studio", font=FONT_TITLE, text_color=COLOR_TEXT_MAIN)
        self.title_label.pack(side="left", pady=10)
        self.title_label.bind("<Double-1>", self.on_title_double_click)

        self.back_btn = ctk.CTkButton(self.header, text="← Collections", width=140, height=40, corner_radius=12,
                                     fg_color="transparent", border_width=1.5, border_color=COLOR_ACCENT,
                                     text_color=COLOR_ACCENT, hover_color="#2A2A2D", state="disabled",
                                     font=FONT_BOLD,
                                     command=self.show_home)
        self.back_btn.pack(side="left", padx=20)

        self.reset_btn = ctk.CTkButton(self.header, text=self.get_reset_text(), width=220, height=40, corner_radius=12,
                                      fg_color=COLOR_DANGER, hover_color="#C0392B", font=FONT_BOLD,
                                      command=self.on_reset)
        self.reset_btn.pack(side="right", padx=40)

        self.update_btn = ctk.CTkButton(self.header, text="Mettre à jour", width=140, height=40, corner_radius=12,
                                       fg_color="transparent", border_width=1.5, border_color=COLOR_ACCENT,
                                       text_color=COLOR_ACCENT, hover_color="#2A2A2D",
                                       font=FONT_BOLD,
                                       command=self.force_update)
        self.update_btn.pack(side="right", padx=10)

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
        
        # Glow Effect Background for text
        self.loading_label = ctk.CTkLabel(self.startup_overlay, text="Cursor Studio", font=FONT_TITLE, text_color=COLOR_ACCENT)
        self.loading_label.place(relx=0.5, rely=0.42, anchor="center")
        
        self.loading_sublabel = ctk.CTkLabel(self.startup_overlay, text="Initialisation du système...", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT)
        self.loading_sublabel.place(relx=0.5, rely=0.48, anchor="center")
        
        # Styled Progress Bar with "Glow" (Using a background frame as shadow)
        progress_container = ctk.CTkFrame(self.startup_overlay, fg_color="#1A1A1D", width=410, height=20, corner_radius=10)
        progress_container.place(relx=0.5, rely=0.58, anchor="center")
        
        self.startup_progress = ctk.CTkProgressBar(progress_container, width=400, height=10, corner_radius=5, 
                                                   progress_color=COLOR_ACCENT, fg_color="#1A1A1D")
        self.startup_progress.place(relx=0.5, rely=0.5, anchor="center")
        self.startup_progress.set(0)

    def start_startup_sequence(self):
        def task():
            try:
                # Step 0: App Update Check
                self.update_startup_status(0.05, "Recherche de mises à jour...")
                latest_v = updater.get_latest_version(self.repo_url)
                if latest_v and latest_v != APP_VERSION:
                    if messagebox.askyesno("Mise à jour disponible", 
                        f"Une nouvelle version ({latest_v}) est disponible.\n\n"
                        f"Voulez-vous mettre à jour Cursor Studio maintenant ?"):
                        self.update_startup_status(0.05, "Téléchargement du logiciel...")
                        success, msg = updater.apply_app_update(self.repo_url)
                        if success:
                            messagebox.showinfo("Mise à jour", msg)
                            self.after(0, sys.exit)
                            return
                        else:
                            self.after(0, lambda m=msg: messagebox.showerror("Erreur", m))

                # Step 1: Check and Download Packs
                self.update_startup_status(0.1, "Vérification des packs...")
                
                has_themes = self.get_themes() != []
                
                if not has_themes:
                    update_success = False
                    # Only try Git if we are in a Git repo
                    if updater.is_git_installed() and os.path.exists(os.path.join(get_base_folder(), ".git")):
                        self.update_startup_status(0.3, "Restauration des packs (Git)...")
                        update_success = updater.update_repository()
                    
                    if not update_success:
                        self.update_startup_status(0.3, "Téléchargement des packs (GitHub)...")
                        success, msg = updater.download_zip_from_github(self.repo_url, self.cursor_dir)
                        if not success:
                            self.after(0, lambda m=msg: messagebox.showerror("Erreur", 
                                f"Impossible de télécharger les packs de curseurs.\nLog: {m}"))
                else:
                    # Optional: check for updates if it's a git repo
                    base_f = get_base_folder()
                    if updater.is_git_installed() and os.path.exists(os.path.join(base_f, ".git")):
                        self.update_startup_status(0.3, "Vérification des mises à jour...")
                        updater.update_repository()
                
                # Step 2: Pip Upgrade
                self.update_startup_status(0.6, "Optimisation de l'environnement...")
                updater.upgrade_pip()
                
                # Step 3: Finalize
                self.update_startup_status(0.9, "Chargement des thèmes...")
                self.themes = self.get_themes()
                time.sleep(0.5)
                
                self.update_startup_status(1.0, "Prêt !")
                time.sleep(0.3)
                self.after(0, self.finish_startup)
            except Exception as e:
                print(f"Startup error: {e}")
                self.after(0, self.finish_startup)
        
        threading.Thread(target=task, daemon=True).start()

    def update_startup_status(self, value, message):
        """Simplifies the progress update to prevent UI lag while still looking good."""
        self.after(0, lambda v=value, m=message: (self.startup_progress.set(v), self.loading_sublabel.configure(text=m)))

    def finish_startup(self):
        # Quick fade-out effect by reducing window alpha if possible, or just destroy
        # For a more "pro" look, we just destroy it and show home
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
        # Exclude hidden or non-theme folders
        return [d for d in os.listdir(self.cursor_dir) 
                if os.path.isdir(os.path.join(self.cursor_dir, d)) 
                and not d.startswith(".") 
                and d not in ["__pycache__", "venv", "app"]]

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

                section_title = ctk.CTkLabel(self.scrollable_content, text="Collections Disponibles", font=FONT_SUBTITLE, text_color=COLOR_ACCENT)
                section_title.pack(anchor="w", padx=20, pady=(20, 30))

                if not self.themes:
                    ctk.CTkLabel(self.scrollable_content, text="Aucun pack de curseurs trouvé dans le dossier 'curseur/'.\nAssurez-vous d'avoir des dossiers à l'intérieur.", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(pady=50)
                else:
                    theme_grid = ctk.CTkFrame(self.scrollable_content, fg_color="transparent")
                    theme_grid.pack(fill="both", expand=True, padx=10)
                    cols = 3
                    for i, theme in enumerate(self.themes):
                        self.build_theme_card(theme_grid, theme, i, cols)
                
                self.hide_nav_loading()
            
            self.after(0, clear_and_build)

        threading.Thread(target=build_task, daemon=True).start()

    def build_theme_card(self, parent, theme, index, cols):
        card = ctk.CTkFrame(parent, width=320, height=280, corner_radius=24, fg_color=COLOR_CARD, border_width=1.5, border_color=COLOR_BORDER)
        card.grid(row=index // cols, column=index % cols, padx=20, pady=20, sticky="nsew")
        card.grid_propagate(False)

        # Hover Effect
        def on_enter(e): card.configure(border_color=COLOR_ACCENT, fg_color=COLOR_CARD_HOVER)
        def on_leave(e): card.configure(border_color=COLOR_BORDER, fg_color=COLOR_CARD)
        card.bind("<Enter>", on_enter)
        card.bind("<Leave>", on_leave)

        icon_frame = ctk.CTkFrame(card, fg_color=COLOR_SIDEBAR, width=120, height=120, corner_radius=60)
        icon_frame.pack(pady=(30, 20))
        icon_frame.pack_propagate(False)

        theme_path = os.path.join(self.cursor_dir, theme)
        preview_img = self.get_theme_preview(theme_path)
        
        if preview_img:
            img_label = ctk.CTkLabel(icon_frame, text="", image=preview_img)
        else:
            img_label = ctk.CTkLabel(icon_frame, text="✨", font=ctk.CTkFont(size=50))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        label = ctk.CTkLabel(card, text=theme, font=FONT_SUBTITLE, text_color=COLOR_TEXT_MAIN, wraplength=280)
        label.pack(padx=20)
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(side="bottom", pady=25)

        ctk.CTkButton(btn_frame, text="Explorer", width=140, height=45, corner_radius=22,
                     fg_color=COLOR_ACCENT, hover_color="#2979FF", font=FONT_BOLD,
                     command=lambda t=theme: self.show_theme_detail(t)).pack(side="left", padx=5)
        
        if self.dev_mode:
            ctk.CTkButton(btn_frame, text="🚀 Publier", width=120, height=45, corner_radius=22,
                         fg_color=COLOR_SUCCESS, hover_color="#27AE60", font=FONT_BOLD,
                         command=lambda t=theme: self.on_publish_theme(t)).pack(side="left", padx=5)

    def get_theme_preview(self, theme_path):
        if theme_path in self.preview_images:
            return self.preview_images[theme_path]
        try:
            files = [f for f in os.listdir(theme_path) if f.endswith((".ani", ".cur"))]
            if not files: return None
            path = os.path.join(theme_path, files[0])
            pil_img = logic.get_cursor_preview(path, size=64)
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

                header_area = ctk.CTkFrame(self.scrollable_content, fg_color=COLOR_CARD, corner_radius=24, height=140, border_width=1.5, border_color=COLOR_BORDER)
                header_area.pack(fill="x", padx=10, pady=(10, 40))
                header_area.pack_propagate(False)

                info_box = ctk.CTkFrame(header_area, fg_color="transparent")
                info_box.pack(side="left", padx=40, fill="y")
                ctk.CTkLabel(info_box, text=theme, font=FONT_TITLE, text_color=COLOR_TEXT_MAIN).pack(anchor="w", pady=(35, 0))
                ctk.CTkLabel(info_box, text="Collection de curseurs personnalisés", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(anchor="w")

                ctk.CTkButton(header_area, text="Installer le Thème Complet", width=260, height=50, corner_radius=25,
                             fg_color=COLOR_SUCCESS, hover_color="#27AE60", font=FONT_BOLD,
                             command=self.on_apply_theme).pack(side="right", padx=40)

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
        
        card = ctk.CTkFrame(parent, width=180, height=240, corner_radius=20, border_width=1.5, border_color=COLOR_BORDER, fg_color=COLOR_CARD)
        card.grid(row=index // cols, column=index % cols, padx=12, pady=12, sticky="nsew")
        card.grid_propagate(False)

        preview_box = ctk.CTkFrame(card, fg_color=COLOR_SIDEBAR, width=70, height=70, corner_radius=15)
        preview_box.pack(pady=(15, 8))
        preview_box.pack_propagate(False)

        path = os.path.join(theme_path, filename)
        pil_img = logic.get_cursor_preview(path, size=48)
        if pil_img:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
            img_label = ctk.CTkLabel(preview_box, text="", image=ctk_img)
        else:
            img_label = ctk.CTkLabel(preview_box, text="🖱️", font=ctk.CTkFont(size=30))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        reg_key = logic.get_role_from_filename(filename, theme=self.selected_theme)
        
        ctk.CTkLabel(card, text=display_name, font=FONT_SMALL, text_color=COLOR_TEXT_MAIN, wraplength=150).pack(pady=(2, 0))
        
        # Role Selection Dropdown (French)
        roles_fr = list(logic.ROLES_FR.values())
        current_role_en = reg_key if reg_key else "None"
        current_role_fr = logic.ROLES_FR.get(current_role_en, "Aucun")
        
        role_dropdown = ctk.CTkComboBox(card, values=roles_fr, width=130, height=24, font=ctk.CTkFont(size=10),
                                      command=lambda r, f=filename: self.on_role_change(f, r))
        role_dropdown.set(current_role_fr)
        role_dropdown.pack(pady=5)
        
        ctk.CTkButton(card, text="Appliquer", width=80, height=26, font=ctk.CTkFont(size=11),
                       fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
                       text_color=COLOR_ACCENT, hover_color="#333",
                       command=lambda f=filename, d=role_dropdown: self.on_set_individual(f, d.get())).pack(pady=(5, 10))

    def on_role_change(self, filename, new_role_fr):
        new_role_en = logic.FR_TO_ROLES.get(new_role_fr, "None")
        role = None if new_role_en == "None" else new_role_en
        logic.save_custom_mapping(self.selected_theme, filename, role)
        print(f"Saved custom mapping: {filename} -> {new_role_en} ({new_role_fr})")

    def on_set_individual(self, filename, role_fr):
        role_en = logic.FR_TO_ROLES.get(role_fr, "None")
        if role_en and role_en != "None":
            file_path = os.path.abspath(os.path.join(self.cursor_dir, self.selected_theme, filename))
            logic.set_cursor(role_en, file_path)
            logic.apply_cursors()
            print(f"Applied {filename} to {role_en}")

    def on_apply_theme(self):
        theme_path = os.path.join(self.cursor_dir, self.selected_theme)
        logic.set_theme(theme_path)

    def get_reset_text(self):
        if os.path.exists(os.path.join(self.cursor_dir, "Default")):
            return "Défaut Personnalisé"
        return "Défaut Windows"

    def on_reset(self):
        if logic.reset_to_default():
            messagebox.showinfo("Succès", "Les curseurs ont été réinitialisés avec succès.")
            self.reset_btn.configure(text=self.get_reset_text())

    def on_title_double_click(self, event):
        """Dev Tools: Force Download + Toggle Dev Mode."""
        if messagebox.askyesno("Outils Développeur", "Voulez-vous forcer un téléchargement complet (Debug Mode) ?"):
            self.show_nav_loading()
            def task():
                print("--- START DEBUG DOWNLOAD ---")
                success, msg = updater.download_zip_from_github(self.repo_url, self.cursor_dir)
                print(f"Result: {success}, Message: {msg}")
                self.themes = self.get_themes()
                self.after(0, self.show_home)
                self.after(0, lambda: messagebox.showinfo("Débug", f"Résultat: {success}\nLog: {msg}\nPacks trouvés: {len(self.themes)}"))
            threading.Thread(target=task, daemon=True).start()
            return
            
        self.dev_mode = not self.dev_mode
        status = "ACTIF" if self.dev_mode else "INACTIF"
        colors = {"ACTIF": COLOR_SUCCESS, "INACTIF": COLOR_TEXT_MAIN}
        self.title_label.configure(text_color=colors[status])
        
        if self.dev_mode:
            messagebox.showinfo("Mode Développeur", "Le Toolkit Développeur est maintenant ACTIF.")
            self.show_dev_tools()
        else:
            messagebox.showinfo("Mode Développeur", "Le Mode Développeur est maintenant INACTIF.")
            self.show_home()

    def show_dev_tools(self):
        self.current_view = "dev_tools"
        self.show_nav_loading()
        
        def clear_and_build():
            for widget in self.scrollable_content.winfo_children():
                widget.destroy()

            # --- Dev Header ---
            header = ctk.CTkFrame(self.scrollable_content, fg_color="#2C2F33", corner_radius=15, height=150)
            header.pack(fill="x", padx=10, pady=10)
            header.pack_propagate(False)
            
            info = ctk.CTkFrame(header, fg_color="transparent")
            info.pack(side="left", padx=30, fill="y")
            ctk.CTkLabel(info, text="Toolkit Développeur", font=FONT_SUBTITLE, text_color=COLOR_ACCENT).pack(anchor="w", pady=(30, 0))
            ctk.CTkLabel(info, text="Importer et Publier de nouveaux packs sur GitHub", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(anchor="w")
            
            actions = ctk.CTkFrame(header, fg_color="transparent")
            actions.pack(side="right", padx=30, fill="y")
            
            ctk.CTkButton(actions, text="📥 Importer un Pack", width=200, height=45, corner_radius=22,
                         fg_color=COLOR_ACCENT, hover_color="#2979FF", font=FONT_BOLD,
                         command=self.on_import_folder).pack(pady=10)
                         
            ctk.CTkButton(actions, text="🚀 Tout Pousser sur GitHub", width=200, height=45, corner_radius=22,
                         fg_color=COLOR_SUCCESS, hover_color="#27AE60", font=FONT_BOLD,
                         command=self.on_push_all).pack(pady=10)
            
            # --- Theme List ---
            ctk.CTkLabel(self.scrollable_content, text="Collections Nouvelles ou Modifiées (Git)", font=FONT_BOLD, text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 10))
            
            staged_themes = updater.get_staged_themes()
            
            if not staged_themes:
                ctk.CTkLabel(self.scrollable_content, text="Aucun dossier nouveau ou modifié trouvé.\nImportez un dossier pour le voir ici.", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(pady=30)
            else:
                for theme in staged_themes:
                    item = ctk.CTkFrame(self.scrollable_content, fg_color=COLOR_SIDEBAR, height=70, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
                    item.pack(fill="x", padx=20, pady=8)
                    item.pack_propagate(False)
                    
                    ctk.CTkLabel(item, text=f"📁 {theme}", font=FONT_BOLD, text_color=COLOR_TEXT_MAIN).pack(side="left", padx=25)
                    ctk.CTkLabel(item, text="Prêt à être poussé", font=FONT_SMALL, text_color=COLOR_SUCCESS).pack(side="right", padx=30)
            self.hide_nav_loading()
            
            # --- Online Collections Section ---
            ctk.CTkLabel(self.scrollable_content, text="Collections en Ligne (Gérer/Supprimer de GitHub)", font=FONT_BOLD, text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=20, pady=(40, 10))
            
            online_themes = updater.get_online_themes()
            if not online_themes:
                ctk.CTkLabel(self.scrollable_content, text="Aucune collection en ligne trouvée.", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(pady=20)
            else:
                for theme in online_themes:
                    item = ctk.CTkFrame(self.scrollable_content, fg_color=COLOR_SIDEBAR, height=70, corner_radius=15, border_width=1, border_color=COLOR_BORDER)
                    item.pack(fill="x", padx=20, pady=8)
                    item.pack_propagate(False)
                    
                    ctk.CTkLabel(item, text=f"🌐 {theme}", font=FONT_BOLD, text_color=COLOR_TEXT_MAIN).pack(side="left", padx=25)
                    
                    ctk.CTkButton(item, text="🗑️ Supprimer de GitHub", width=180, height=35, corner_radius=17,
                                 fg_color=COLOR_DANGER, hover_color="#C0392B", font=FONT_SMALL,
                                 command=lambda t=theme: self.on_delete_remote(t)).pack(side="right", padx=25)

        self.after(0, clear_and_build)

    def on_delete_remote(self, theme):
        if not messagebox.askyesno("Confirmer Suppression", f"Êtes-vous sûr de vouloir supprimer '{theme}' de GitHub ?\nCela le retirera pour TOUT LE MONDE."):
            return
            
        self.show_nav_loading()
        theme_path = os.path.join(self.cursor_dir, theme)
        
        def task():
            # Ensure theme_path is relative to the repo root for Git
            rel_theme_path = os.path.relpath(theme_path, get_base_folder())
            success, msg = updater.delete_remote_theme(rel_theme_path)
            self.after(0, lambda: self.finish_delete(success, msg))
        
        threading.Thread(target=task, daemon=True).start()

    def finish_delete(self, success, message):
        self.hide_nav_loading()
        if success:
            messagebox.showinfo("Supprimé", "La collection a été supprimée avec succès.")
            self.show_dev_tools() # Refresh view
        else:
            messagebox.showerror("Erreur", f"Échec de la suppression :\n{message}")

    def on_import_folder(self):
        target_dir = filedialog.askdirectory(title="Sélectionnez le dossier de curseurs à importer")
        if not target_dir:
            return
        
        folder_name = os.path.basename(target_dir)
        destination = os.path.join(self.cursor_dir, folder_name)
        
        if os.path.exists(destination):
            if not messagebox.askyesno("Écraser ?", f"Le dossier '{folder_name}' existe déjà. Voulez-vous l'écraser ?"):
                return
            shutil.rmtree(destination)
            
        try:
            self.show_nav_loading()
            shutil.copytree(target_dir, destination)
            messagebox.showinfo("Succès", f"'{folder_name}' a été importé avec succès !")
            self.show_dev_tools()
        except Exception as e:
            messagebox.showerror("Erreur", f"Échec de l'importation :\n{e}")
        finally:
            self.hide_nav_loading()

    def on_push_all(self):
        msg = simpledialog.askstring("Message de Commit", "Entrez une description pour cette mise à jour :", initialvalue="Mise à jour des collections")
        if msg is None: return # Cancelled
        
        self.show_nav_loading()
        
        def task():
            success, res_msg = updater.push_all(msg)
            self.after(0, lambda: self.finish_publish(success, res_msg))
            
        threading.Thread(target=task, daemon=True).start()

    def finish_publish(self, success, message):
        self.hide_nav_loading()
        if success:
            messagebox.showinfo("Succès", "Mise à jour publiée avec succès sur GitHub !")
        else:
            messagebox.showerror("Erreur", f"Échec de la publication :\n{message}")

    def force_update(self):
        """Manually trigger a pack update (ZIP or Git)."""
        if messagebox.askyesno("Mise à jour", "Voulez-vous forcer la vérification des packs de curseurs ?"):
            self.show_nav_loading()
            def update_task():
                update_success = False
                base_f = get_base_folder()
                if updater.is_git_installed() and os.path.exists(os.path.join(base_f, ".git")):
                    update_success = updater.update_repository()
                
                if not update_success:
                    success, msg = updater.download_zip_from_github(self.repo_url, self.cursor_dir)
                    if not success:
                        self.after(0, lambda m=msg: messagebox.showerror("Erreur", f"Échec du téléchargement : {m}"))
                
                self.themes = self.get_themes()
                self.after(0, self.show_home)
                self.after(0, lambda: messagebox.showinfo("Succès", "Vérification des packs terminée !"))
            
            threading.Thread(target=update_task, daemon=True).start()

