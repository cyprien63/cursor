import customtkinter as ctk
import os
from PIL import Image, ImageTk
import cursor_logic
import updater
import threading
import time
import shutil
from tkinter import filedialog, messagebox

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
        self.dev_mode = False

        self.setup_ui()
        self.start_startup_sequence()

    def setup_ui(self):
        # --- Header ---
        self.header = ctk.CTkFrame(self, height=80, corner_radius=0, fg_color=COLOR_SIDEBAR, border_width=1, border_color="#333")
        self.header.pack(fill="x")
        self.header.pack_propagate(False)

        title_container = ctk.CTkFrame(self.header, fg_color="transparent")
        title_container.pack(side="left", padx=30, fill="y")
        self.title_label = ctk.CTkLabel(title_container, text="Cursor Studio", font=FONT_TITLE, text_color=COLOR_TEXT_MAIN)
        self.title_label.pack(side="left", pady=10)
        self.title_label.bind("<Double-1>", self.on_title_double_click)

        self.back_btn = ctk.CTkButton(self.header, text="← Collections", width=120, height=36, 
                                     fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
                                     text_color=COLOR_ACCENT, hover_color="#333", state="disabled",
                                     command=self.show_home)
        self.back_btn.pack(side="left", padx=20)

        self.reset_btn = ctk.CTkButton(self.header, text=self.get_reset_text(), width=180, height=36,
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
        
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(pady=(20, 10))

        ctk.CTkButton(btn_frame, text="Explore", width=120, height=40, corner_radius=20,
                     fg_color=COLOR_ACCENT, hover_color="#36719F",
                     command=lambda t=theme: self.show_theme_detail(t)).pack(side="left", padx=5)
        
        if self.dev_mode:
            ctk.CTkButton(btn_frame, text="🚀 Publish", width=100, height=40, corner_radius=20,
                         fg_color="#27AE60", hover_color="#229954",
                         command=lambda t=theme: self.on_publish_theme(t)).pack(side="left", padx=5)

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
        
        # Increased height to fit dropdown
        card = ctk.CTkFrame(parent, width=170, height=220, corner_radius=12, border_width=2)
        card.grid(row=index // cols, column=index % cols, padx=10, pady=10, sticky="nsew")
        card.grid_propagate(False)

        preview_box = ctk.CTkFrame(card, fg_color="#34373C", width=60, height=60, corner_radius=10)
        preview_box.pack(pady=(10, 5))
        preview_box.pack_propagate(False)

        path = os.path.join(theme_path, filename)
        pil_img = cursor_logic.get_cursor_preview(path, size=48)
        if pil_img:
            ctk_img = ctk.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
            img_label = ctk.CTkLabel(preview_box, text="", image=ctk_img)
        else:
            img_label = ctk.CTkLabel(preview_box, text="🖱️", font=ctk.CTkFont(size=30))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        reg_key = cursor_logic.get_role_from_filename(filename, theme=self.selected_theme)
        
        ctk.CTkLabel(card, text=display_name, font=FONT_SMALL, text_color=COLOR_TEXT_MAIN, wraplength=150).pack(pady=(2, 0))
        
        # Role Selection Dropdown
        roles = ["None", "Arrow", "Help", "AppStarting", "Wait", "Crosshair", "IBeam", "NWPen", "No", "SizeNS", "SizeWE", "SizeNWSE", "SizeNESW", "SizeAll", "UpArrow", "Hand"]
        current_role = reg_key if reg_key else "None"
        
        role_dropdown = ctk.CTkComboBox(card, values=roles, width=130, height=24, font=ctk.CTkFont(size=10),
                                      command=lambda r, f=filename: self.on_role_change(f, r))
        role_dropdown.set(current_role)
        role_dropdown.pack(pady=5)
        
        ctk.CTkButton(card, text="Apply", width=80, height=26, font=ctk.CTkFont(size=11),
                       fg_color="transparent", border_width=1, border_color=COLOR_ACCENT,
                       text_color=COLOR_ACCENT, hover_color="#333",
                       command=lambda f=filename, d=role_dropdown: self.on_set_individual(f, d.get())).pack(pady=(5, 10))

    def on_role_change(self, filename, new_role):
        role = None if new_role == "None" else new_role
        cursor_logic.save_custom_mapping(self.selected_theme, filename, role)
        print(f"Saved custom mapping: {filename} -> {new_role}")

    def on_set_individual(self, filename, role):
        if role and role != "None":
            file_path = os.path.abspath(os.path.join(self.cursor_dir, self.selected_theme, filename))
            cursor_logic.set_cursor(role, file_path)
            cursor_logic.apply_cursors()
            print(f"Applied {filename} to {role}")

    def on_apply_theme(self):
        theme_path = os.path.join(self.cursor_dir, self.selected_theme)
        cursor_logic.set_theme(theme_path)

    def get_reset_text(self):
        if os.path.exists(os.path.join(self.cursor_dir, "Default")):
            return "Reset to Custom Default"
        return "Reset Windows Default"

    def on_reset(self):
        if cursor_logic.reset_to_default():
            messagebox.showinfo("Success", "Cursors have been reset successfully.")
            # Update button text in case they just added/removed 'Default' folder
            self.reset_btn.configure(text=self.get_reset_text())

    def on_title_double_click(self, event):
        self.dev_mode = not self.dev_mode
        status = "ACTIVE" if self.dev_mode else "INACTIVE"
        colors = {"ACTIVE": "#27AE60", "INACTIVE": COLOR_TEXT_MAIN}
        self.title_label.configure(text_color=colors[status])
        
        if self.dev_mode:
            messagebox.showinfo("Developer Mode", "Developer Toolkit is now ACTIVE.")
            self.show_dev_tools()
        else:
            messagebox.showinfo("Developer Mode", "Developer Mode is now INACTIVE.")
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
            ctk.CTkLabel(info, text="Developer Toolkit", font=FONT_SUBTITLE, text_color=COLOR_ACCENT).pack(anchor="w", pady=(30, 0))
            ctk.CTkLabel(info, text="Import and Publish new cursor packs to GitHub", font=FONT_NORMAL, text_color=COLOR_TEXT_ALT).pack(anchor="w")
            
            actions = ctk.CTkFrame(header, fg_color="transparent")
            actions.pack(side="right", padx=30, fill="y")
            
            ctk.CTkButton(actions, text="📥 Import New Pack", width=180, height=40, corner_radius=20,
                         fg_color="#4E9CCF", hover_color="#36719F", font=ctk.CTkFont(weight="bold"),
                         command=self.on_import_folder).pack(pady=10)
                         
            ctk.CTkButton(actions, text="🚀 Push All to GitHub", width=180, height=40, corner_radius=20,
                         fg_color="#27AE60", hover_color="#229954", font=ctk.CTkFont(weight="bold"),
                         command=self.on_push_all).pack(pady=10)
            
            # --- Theme List ---
            ctk.CTkLabel(self.scrollable_content, text="New or Modified Collections (Identified by Git)", font=FONT_NORMAL, text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=20, pady=(20, 10))
            
            staged_themes = updater.get_staged_themes(self.cursor_dir)
            
            if not staged_themes:
                ctk.CTkLabel(self.scrollable_content, text="No new or modified folders found.\nImport a folder to see it here.", font=FONT_SMALL, text_color=COLOR_TEXT_ALT).pack(pady=30)
            else:
                for theme in staged_themes:
                    item = ctk.CTkFrame(self.scrollable_content, fg_color="#242526", height=60, corner_radius=10)
                    item.pack(fill="x", padx=20, pady=5)
                    item.pack_propagate(False)
                    
                    ctk.CTkLabel(item, text=f"📁 {theme}", font=FONT_NORMAL, text_color=COLOR_TEXT_MAIN).pack(side="left", padx=20)
                    ctk.CTkLabel(item, text="Ready to Push", font=FONT_SMALL, text_color="#27AE60").pack(side="right", padx=30)
            self.hide_nav_loading()
            
            # --- Online Collections Section ---
            ctk.CTkLabel(self.scrollable_content, text="Online Collections (Manage/Delete from GitHub)", font=FONT_NORMAL, text_color=COLOR_TEXT_MAIN).pack(anchor="w", padx=20, pady=(30, 10))
            
            online_themes = updater.get_online_themes(self.cursor_dir)
            if not online_themes:
                ctk.CTkLabel(self.scrollable_content, text="No online collections found.", font=FONT_SMALL, text_color=COLOR_TEXT_ALT).pack(pady=20)
            else:
                for theme in online_themes:
                    item = ctk.CTkFrame(self.scrollable_content, fg_color="#242526", height=60, corner_radius=10)
                    item.pack(fill="x", padx=20, pady=5)
                    item.pack_propagate(False)
                    
                    ctk.CTkLabel(item, text=f"🌐 {theme}", font=FONT_NORMAL, text_color=COLOR_TEXT_MAIN).pack(side="left", padx=20)
                    
                    ctk.CTkButton(item, text="🗑️ Delete from GitHub", width=160, height=32, corner_radius=16,
                                 fg_color="#A93226", hover_color="#922B21", font=ctk.CTkFont(size=11),
                                 command=lambda t=theme: self.on_delete_remote(t)).pack(side="right", padx=20)

        self.after(0, clear_and_build)

    def on_delete_remote(self, theme):
        if not messagebox.askyesno("Confirm Deletion", f"Are you sure you want to delete '{theme}' from GitHub?\nThis will remove it for EVERYONE."):
            return
            
        self.show_nav_loading()
        theme_path = os.path.join(self.cursor_dir, theme)
        
        def task():
            success, msg = updater.delete_remote_theme(theme_path)
            self.after(0, lambda: self.finish_delete(success, msg))
            
        threading.Thread(target=task, daemon=True).start()

    def finish_delete(self, success, message):
        self.hide_nav_loading()
        if success:
            messagebox.showinfo("Deleted", message)
            self.show_dev_tools() # Refresh view
        else:
            messagebox.showerror("Error", f"Failed to delete:\n{message}")

    def on_import_folder(self):
        target_dir = filedialog.askdirectory(title="Select Cursor Folder to Import")
        if not target_dir:
            return
        
        folder_name = os.path.basename(target_dir)
        destination = os.path.join(self.cursor_dir, folder_name)
        
        if os.path.exists(destination):
            if not messagebox.askyesno("Overwrite?", f"Folder '{folder_name}' already exists. Overwrite?"):
                return
            shutil.rmtree(destination)
            
        try:
            self.show_nav_loading()
            shutil.copytree(target_dir, destination)
            messagebox.showinfo("Success", f"Imported '{folder_name}' successfully!")
            self.show_dev_tools()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import folder:\n{e}")
        finally:
            self.hide_nav_loading()

    def on_push_all(self):
        msg = filedialog.askstring("Commit Message", "Enter a description for this update:", initialvalue="Update cursor collections")
        if msg is None: return # Cancelled
        
        self.show_nav_loading()
        
        def task():
            success, res_msg = updater.push_all(msg)
            self.after(0, lambda: self.finish_publish(success, res_msg))
            
        threading.Thread(target=task, daemon=True).start()

    def finish_publish(self, success, message):
        self.hide_nav_loading()
        if success:
            messagebox.showinfo("Success", message)
        else:
            messagebox.showerror("Error", f"Failed to push theme:\n{message}")

if __name__ == "__main__":
    app = CursorApp()
    app.mainloop()
