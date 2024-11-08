# gui.py

import customtkinter as ctk
from settings import Settings

class SearchFrame(ctk.CTkFrame):
    def __init__(self, master, search_callback):
        super().__init__(master)
        self.pack(pady=10, padx=10, fill="x")

        # Поле ввода поиска
        self.search_entry = ctk.CTkEntry(
            self, 
            placeholder_text="Введите название видео",
            width=400
        )
        self.search_entry.pack(side="left", padx=(0, 10))

        # Кнопка поиска
        self.search_button = ctk.CTkButton(
            self,
            text="🔍 Поиск",
            command=search_callback,
            width=100,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.search_button.pack(side="left")


class ControlsFrame(ctk.CTkFrame):
    def __init__(self, master, play_pause_callback, stop_callback, set_volume_callback, toggle_fullscreen_callback):
        super().__init__(master)
        self.pack(pady=10, padx=10, fill="x")

        # Полоска прогресса
        self.progress_bar = ctk.CTkProgressBar(self)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        self.progress_bar.set(0)

        # Кнопки управления
        self.play_button = ctk.CTkButton(
            self,
            text="▶️ Play",
            command=play_pause_callback,
            width=100,
            height=35,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.play_button.pack(side="left", padx=5)

        self.stop_button = ctk.CTkButton(
            self,
            text="⏹️ Stop",
            command=stop_callback,
            width=100,
            height=35,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.stop_button.pack(side="left", padx=5)

        # Кнопка полноэкранного режима
        self.fullscreen_button = ctk.CTkButton(
            self,
            text="🖥️ Fullscreen",
            command=toggle_fullscreen_callback,
            width=150,
            height=35,
            fg_color=Settings.BUTTON_NORMAL_COLOR,
            hover_color=Settings.BUTTON_HOVER_COLOR
        )
        self.fullscreen_button.pack(side="left", padx=5)

        # Контейнер для регулировки громкости
        self.volume_frame = ctk.CTkFrame(self)
        self.volume_frame.pack(side="right", padx=5)

        self.volume_label = ctk.CTkLabel(self.volume_frame, text="🔊")
        self.volume_label.pack(side="left", padx=5)

        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=100,
            command=set_volume_callback,
            width=100
        )
        self.volume_slider.pack(side="right", padx=5)
        self.volume_slider.set(Settings.DEFAULT_VOLUME)  # Устанавливаем начальное значение громкости

        # Метки текущего и общего времени
        self.current_time = ctk.CTkLabel(self, text="0:00")
        self.current_time.pack(side="left", padx=5)

        self.total_time = ctk.CTkLabel(self, text="0:00")
        self.total_time.pack(side="right", padx=5)