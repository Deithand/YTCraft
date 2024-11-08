# player.py
import sys
import os
import time
import json
import threading
import requests
from bs4 import BeautifulSoup
import customtkinter as ctk
import vlc
import yt_dlp

from settings import Settings
from gui import SearchFrame, ControlsFrame
from utils import format_time

class YouTubePlayer:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.title("YouTube Player")
        self.window.geometry(Settings.WINDOW_SIZE)
        ctk.set_appearance_mode(Settings.THEME)

        # Initialize VLC with error handling
        try:
            self.instance = vlc.Instance()
            if not self.instance:
                raise Exception("Failed to create VLC instance")
            
            self.player = self.instance.media_player_new()
            if not self.player:
                raise Exception("Failed to create media player")
        except Exception as e:
            print(f"Error initializing VLC: {e}")
            messagebox.showerror("Error", "Failed to initialize VLC player. Please check VLC installation.")
            sys.exit(1)
            
        self.is_playing = False
        self.current_url = None

        self.current_video_id = None
        self.current_title = None
        self.current_url = None
        self.is_video_fullscreen = False  # Флаг для отслеживания полноэкранного режима видео

        # Создание компонентов GUI
        self.search_frame = SearchFrame(self.window, self.search_videos)

        # Меню
        self.create_menu()

        # Фрейм с результатами поиска
        self.results_frame = ctk.CTkScrollableFrame(self.window, height=200)
        self.results_frame.pack(pady=10, padx=10, fill="x")

        # Фрейм для видео
        self.video_frame = ctk.CTkFrame(self.window)
        self.video_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Метка "Сейчас играет"
        self.now_playing = ctk.CTkLabel(self.window, text="", height=30)
        self.now_playing.pack(pady=5)

        # Панель управления
        self.controls = ControlsFrame(
            self.window,
            self.play_pause,
            self.stop,
            self.set_volume,
            self.toggle_fullscreen  # Передаём метод toggle_fullscreen
        )

        # Загрузка настроек
        self.load_settings()

        # Запуск потока обновления прогресса
        self.update_thread = threading.Thread(
            target=self.update_progress, daemon=True)
        self.update_thread.start()

    def create_menu(self):
        self.menu_frame = ctk.CTkFrame(self.window)
        self.menu_frame.pack(fill="x", pady=5, padx=5)

        # Кнопка полного экрана в меню
        self.fullscreen_button = ctk.CTkButton(
            self.menu_frame,
            text="🖥️ Fullscreen",
            width=40,
            command=self.toggle_fullscreen,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.fullscreen_button.pack(side="left", padx=5)

        # Выбор качества
        self.quality_var = ctk.StringVar(value=Settings.DEFAULT_QUALITY)
        self.quality_menu = ctk.CTkOptionMenu(
            self.menu_frame,
            values=Settings.QUALITIES,
            variable=self.quality_var,
            command=self.change_quality,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            button_color=Settings.BUTTON_HOVER_COLOR
        )
        self.quality_menu.pack(side="left", padx=5)

        # Кнопка настроек
        self.settings_button = ctk.CTkButton(
            self.menu_frame,
            text="⚙️",
            width=40,
            command=self.show_settings,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.settings_button.pack(side="right", padx=5)

        # Кнопка "О программе"
        self.about_button = ctk.CTkButton(
            self.menu_frame,
            text="ℹ️",
            width=40,
            command=self.show_about,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.about_button.pack(side="right", padx=5)

    def toggle_fullscreen(self):
        if not self.is_video_fullscreen:
            # Переключаемся в полноэкранный режим только для видео
            self.search_frame.pack_forget()
            self.menu_frame.pack_forget()
            self.controls.pack_forget()

            self.video_frame.pack(fill="both", expand=True)
            self.fullscreen_button.configure(text="⏹️ Exit Fullscreen")
            self.controls.fullscreen_button.configure(text="⏹️ Exit Fullscreen")

            self.is_video_fullscreen = True
        else:
            # Выходим из полноэкранного режима
            self.video_frame.pack_forget()

            self.search_frame.pack(pady=10, padx=10, fill="x")
            self.menu_frame.pack(fill="x", pady=5, padx=5)
            self.controls.pack()

            self.fullscreen_button.configure(text="🖥️ Fullscreen")
            self.controls.fullscreen_button.configure(text="🖥️ Fullscreen")

            self.is_video_fullscreen = False

    def change_quality(self, quality):
        """Switch video quality while playing"""
        if hasattr(self, 'available_formats') and self.current_video_id:
            # Store current position
            current_time = self.player.get_time()
            
            # Reload video with new quality
            self.load_video(self.current_video_id, self.current_title)
            
            # Restore position
            self.player.set_time(current_time)

    def show_settings(self):
        settings_window = ctk.CTkToplevel(self.window)
        settings_window.title("Settings")
        settings_window.geometry("400x300")

        # Выбор темы
        theme_frame = ctk.CTkFrame(settings_window)
        theme_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(theme_frame, text="Theme:").pack(side="left", padx=5)
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=Settings.THEMES,
            variable=ctk.StringVar(value=Settings.THEME),
            command=self.change_theme
        )
        theme_menu.pack(side="left", padx=5)

        # Качество по умолчанию
        quality_frame = ctk.CTkFrame(settings_window)
        quality_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(quality_frame, text="Default Quality:").pack(
            side="left", padx=5)
        default_quality_menu = ctk.CTkOptionMenu(
            quality_frame,
            values=Settings.QUALITIES,
            variable=ctk.StringVar(value=Settings.DEFAULT_QUALITY),
            command=self.change_default_quality
        )
        default_quality_menu.pack(side="left", padx=5)

        # Переключатель автопроигрывания
        autoplay_frame = ctk.CTkFrame(settings_window)
        autoplay_frame.pack(pady=10, padx=10, fill="x")

        ctk.CTkLabel(autoplay_frame, text="Autoplay:").pack(
            side="left", padx=5)
        self.autoplay_var = ctk.BooleanVar(value=Settings.AUTOPLAY)
        autoplay_switch = ctk.CTkSwitch(
            autoplay_frame, variable=self.autoplay_var)
        autoplay_switch.pack(side="left", padx=5)

        # Кнопка сохранения настроек
        save_button = ctk.CTkButton(
            settings_window, text="Save", command=lambda: self.save_settings_and_close(settings_window))
        save_button.pack(pady=20)

    def show_about(self):
        about_window = ctk.CTkToplevel(self.window)
        about_window.title("About")
        about_window.geometry("300x200")

        ctk.CTkLabel(
            about_window,
            text="YouTube Player",
            font=("Arial", 20, "bold")
        ).pack(pady=10)

        ctk.CTkLabel(
            about_window,
            text="Version 1.0\n\nA simple YouTube player built with Python\nusing CustomTkinter and yt-dlp"
        ).pack(pady=10)

    def change_theme(self, theme):
        Settings.THEME = theme  # Убедитесь, что THEME — это строка
        ctk.set_appearance_mode(theme)
        self.save_settings()

    def change_default_quality(self, quality):
        Settings.DEFAULT_QUALITY = quality
        self.save_settings()
        self.quality_var.set(quality)
        # Если видео воспроизводится, перезагрузить его с новым качеством
        if self.current_video_id and self.is_playing:
            current_time = self.player.get_time()
            self.load_video(self.current_video_id, self.current_title)
            self.player.set_time(current_time)

    def save_settings_and_close(self, window):
        Settings.AUTOPLAY = self.autoplay_var.get()
        self.save_settings()
        window.destroy()

    def save_settings(self):
        settings = {
            'theme': Settings.THEME,
            'default_quality': Settings.DEFAULT_QUALITY,
            'autoplay': Settings.AUTOPLAY,
            'default_volume': Settings.DEFAULT_VOLUME  # Сохраняем DEFAULT_VOLUME
        }
        with open('settings.json', 'w') as f:
            json.dump(settings, f)

    def load_settings(self):
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                settings = json.load(f)
                theme = settings.get('theme', 'System')
                if isinstance(theme, str):
                    Settings.THEME = theme
                else:
                    Settings.THEME = 'System'  # Fallback if theme is not a string
                Settings.DEFAULT_QUALITY = settings.get('default_quality', 'Auto')
                Settings.AUTOPLAY = settings.get('autoplay', False)
                if 'default_volume' in settings:
                    Settings.DEFAULT_VOLUME = settings.get('default_volume', 100)
                else:
                    Settings.DEFAULT_VOLUME = 100  # Default volume
        else:
            # Установить настройки по умолчанию
            Settings.THEME = 'System'
            Settings.DEFAULT_QUALITY = 'Auto'
            Settings.DEFAULT_VOLUME = 100
            Settings.AUTOPLAY = False

    def search_videos(self):
        query = self.search_frame.search_entry.get()
        if not query:
            return

        for widget in self.results_frame.winfo_children():
            widget.destroy()

        try:
            loading_label = ctk.CTkLabel(
                self.results_frame, text="Searching...")
            loading_label.pack()
            self.window.update()

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            response = requests.get(url, headers=headers)

            loading_label.destroy()

            if response.status_code != 200:
                raise Exception("Failed to fetch search results")

            soup = BeautifulSoup(response.text, 'html.parser')
            scripts = soup.find_all('script')

            for script in scripts:
                if 'var ytInitialData = ' in str(script):
                    data = str(script).split(
                        'var ytInitialData = ')[1].split(';</script>')[0]
                    json_data = json.loads(data)

                    items = json_data['contents']['twoColumnSearchResultsRenderer']['primaryContents'][
                        'sectionListRenderer']['contents'][0]['itemSectionRenderer']['contents']

                    for item in items:
                        if 'videoRenderer' in item:
                            video = item['videoRenderer']
                            video_id = video['videoId']
                            title = video['title']['runs'][0]['text']

                            result_button = ctk.CTkButton(
                                self.results_frame,
                                text=title,
                                command=lambda v_id=video_id, t=title: self.load_video(
                                    v_id, t),
                                height=40,
                                fg_color=Settings.BUTTON_NORMAL_COLOR,
                                hover_color=Settings.BUTTON_HOVER_COLOR
                            )
                            result_button.pack(
                                pady=5, padx=10, fill="x")
                    break

        except Exception as e:
            error_label = ctk.CTkLabel(
                self.results_frame,
                text=f"Error: {str(e)}",
                text_color="red"
            )
            error_label.pack()

    def load_video(self, video_id, title):
        try:
            default_quality = Settings.DEFAULT_QUALITY
            format_spec = 'best'

            if default_quality != "Auto":
                quality_height = default_quality[:-1]  # Remove 'p' from '720p' etc
                format_spec = f'bestvideo[height<={quality_height}]+bestaudio/best[height<={quality_height}]'

            ydl_opts = {
                'format': format_spec,
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                url = f"https://www.youtube.com/watch?v={video_id}"
                info = ydl.extract_info(url, download=False)
                
                # Get playable URL
                playback_url = None
                if 'formats' in info:
                    formats = info['formats']
                    # Filter formats by quality
                    if default_quality != "Auto":
                        try:
                            height = int(default_quality[:-1])
                            # Filter formats safely handling None values
                            suitable_formats = []
                            for f in formats:
                                format_height = f.get('height')
                                if format_height is not None and format_height <= height:
                                    if f.get('acodec') != 'none':
                                        suitable_formats.append(f)
                            
                            if suitable_formats:
                                # Get highest quality format within limit
                                selected_format = max(suitable_formats, 
                                                   key=lambda x: x.get('height', 0))
                                playback_url = selected_format['url']
                        except (ValueError, TypeError):
                            # Fallback to best if quality parsing fails
                            playback_url = formats[-1]['url']
                    else:
                        # Use best format
                        playback_url = formats[-1]['url']
                
                if not playback_url and 'url' in info:
                    # Fallback to direct URL
                    playback_url = info['url']
                    
                if not playback_url:
                    raise Exception("No playable URL found")

                # Create media
                media = self.instance.media_new(playback_url)
                self.player.set_media(media)

                # Set video window
                if os.name == 'nt':
                    self.player.set_hwnd(self.video_frame.winfo_id())
                else:
                    self.player.set_xwindow(self.video_frame.winfo_id())

                # Update state
                self.current_url = playback_url
                self.current_video_id = video_id
                self.current_title = title
                
                # Update UI
                self.now_playing.configure(text=f"Now Playing: {title}")
                
                # Start playback
                if not self.is_playing:
                    self.player.play()
                    self.is_playing = True
                    self.controls.play_button.configure(text="⏸️ Pause")

        except Exception as e:
            print(f"Error loading video: {str(e)}")
            self.now_playing.configure(text=f"Error: Could not load video")

    def download_progress_hook(self, d):
        if d['status'] == 'downloading':
            # Update progress bar if needed
            progress = (d['downloaded_bytes'] / d['total_bytes']) 
            if hasattr(self, 'download_progress'):
                self.download_progress.set(progress)
                
    def update_quality_menu(self):
        """Update quality menu with available formats"""
        if hasattr(self, 'available_formats'):
            qualities = sorted(set(
                f"{f.get('height', 0)}p" 
                for f in self.available_formats 
                if f.get('height')
            ))
            self.quality_menu.configure(values=qualities)

    def play(self):
        self.player.play()
        self.is_playing = True
        self.controls.play_button.configure(text="⏸️ Pause")

    def play_pause(self):
        if not self.current_url:
            return

        if not self.is_playing:
            self.play()
        else:
            self.player.pause()
            self.is_playing = False
            self.controls.play_button.configure(text="▶️ Play")

    def stop(self):
        if self.current_url:
            self.player.stop()
            self.is_playing = False
            self.controls.play_button.configure(text="▶️ Play")
            self.controls.progress_bar.set(0)
            self.now_playing.configure(text="")
            self.controls.current_time.configure(text="0:00")
            self.controls.total_time.configure(text="0:00")

    def set_volume(self, value):
        self.player.audio_set_volume(int(value))
        if int(value) == 0:
            self.controls.volume_label.configure(text="🔇")
        elif int(value) < 50:
            self.controls.volume_label.configure(text="🔉")
        else:
            self.controls.volume_label.configure(text="🔊")

    def update_progress(self):
        while True:
            if self.is_playing:
                try:
                    length = self.player.get_length()
                    current = self.player.get_time()
                    if length > 0:
                        self.controls.progress_bar.set(current / length)
                        self.controls.current_time.configure(
                            text=format_time(current))
                        self.controls.total_time.configure(
                            text=format_time(length))
                except:
                    pass
            time.sleep(0.1)

    def run(self):
        self.window.mainloop()