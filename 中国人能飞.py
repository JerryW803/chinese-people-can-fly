import ctypes
import math
from pathlib import Path
import tkinter as tk
from tkinter import messagebox


WINDOW_WIDTH = 950
WINDOW_HEIGHT = 600
FLAG_X = 80
FLAG_Y = 55
FLAG_WIDTH = 750
FLAG_HEIGHT = 500
GRID_COLUMNS = 38
GRID_ROWS = 24
MUSIC_PATH = Path(r"E:\IDM Download\IDM Download\M500002cIvGy0MziEL.mp3")
MCI_ALIAS = "flag_music"

winmm = ctypes.WinDLL("winmm")
mci_send_string = winmm.mciSendStringW
mci_send_string.argtypes = (
    ctypes.c_wchar_p,
    ctypes.c_wchar_p,
    ctypes.c_uint,
    ctypes.c_void_p,
)
mci_send_string.restype = ctypes.c_uint
mci_get_error_string = winmm.mciGetErrorStringW
mci_get_error_string.argtypes = (
    ctypes.c_uint,
    ctypes.c_wchar_p,
    ctypes.c_uint,
)
mci_get_error_string.restype = ctypes.c_int


class WavingFlag:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.canvas = tk.Canvas(
            root,
            width=WINDOW_WIDTH,
            height=WINDOW_HEIGHT,
            bg="#f5f5f5",
            highlightthickness=0,
        )
        self.canvas.pack()
        self.music_button = tk.Button(
            root,
            text="播放音乐（中国人能飞）",
            command=self.play_music,
            font=("Microsoft YaHei", 12),
        )
        self.music_button.pack(pady=8)
        self.pause_button = tk.Button(
            root,
            text="暂停播放（中国人不想飞）",
            command=self.pause_music,
            font=("Microsoft YaHei", 12),
        )
        self.pause_button.pack(pady=4)
        self.music_open = False
        self.music_paused = False
        self.phase = 0.0
        self.animate()

    def send_mci_command(self, command: str) -> bool:
        error_code = mci_send_string(command, None, 0, None)
        if error_code == 0:
            return True

        error_text = ctypes.create_unicode_buffer(256)
        if mci_get_error_string(error_code, error_text, len(error_text)):
            message = error_text.value
        else:
            message = f"MCI 错误代码：{error_code}"
        messagebox.showerror("音乐播放失败", message, parent=self.root)
        return False

    def play_music(self) -> None:
        if not MUSIC_PATH.is_file():
            messagebox.showerror(
                "音乐播放失败",
                f"找不到 MP3 文件：\n{MUSIC_PATH}",
                parent=self.root,
            )
            return

        if not self.music_open:
            if not self.send_mci_command(
                f'open "{MUSIC_PATH}" type mpegvideo alias {MCI_ALIAS}'
            ):
                return
            self.music_open = True

        if self.music_paused:
            if self.send_mci_command(f"resume {MCI_ALIAS}"):
                self.music_paused = False
        else:
            self.send_mci_command(f"play {MCI_ALIAS} from 0")

    def pause_music(self) -> None:
        if self.music_open and not self.music_paused:
            if self.send_mci_command(f"pause {MCI_ALIAS}"):
                self.music_paused = True

    def close_music(self) -> None:
        if self.music_open:
            self.send_mci_command(f"close {MCI_ALIAS}")
            self.music_open = False
            self.music_paused = False

    def wave_y(self, x: float, y: float) -> float:
        progress = x / FLAG_WIDTH
        amplitude = 23 * progress
        return y + amplitude * math.sin(2 * math.pi * progress * 1.35 - self.phase)

    def draw_fabric(self) -> None:
        for column in range(GRID_COLUMNS):
            x0 = FLAG_WIDTH * column / GRID_COLUMNS
            x1 = FLAG_WIDTH * (column + 1) / GRID_COLUMNS
            for row in range(GRID_ROWS):
                y0 = FLAG_HEIGHT * row / GRID_ROWS
                y1 = FLAG_HEIGHT * (row + 1) / GRID_ROWS
                points = (
                    (x0, y0),
                    (x1, y0),
                    (x1, y1),
                    (x0, y1),
                )
                canvas_points = []
                for x, y in points:
                    canvas_points.extend(
                        (FLAG_X + x, FLAG_Y + self.wave_y(x, y))
                    )

                progress = (x0 + x1) / (2 * FLAG_WIDTH)
                slope = math.cos(
                    2 * math.pi * progress * 1.35 - self.phase
                )
                brightness = max(0.78, min(1.0, 0.9 + 0.1 * slope))
                red = int(205 + 35 * brightness)
                green = int(0 + 15 * (1 - brightness))
                blue = int(0 + 12 * (1 - brightness))
                color = f"#{red:02x}{green:02x}{blue:02x}"
                self.canvas.create_polygon(
                    canvas_points,
                    fill=color,
                    outline=color,
                )

    def draw_star(
        self, center_x: float, center_y: float, radius: float, angle: float
    ) -> None:
        points = []
        for index in range(10):
            point_radius = radius if index % 2 == 0 else radius * 0.382
            point_angle = angle - math.pi / 2 + index * math.pi / 5
            x = center_x + point_radius * math.cos(point_angle)
            y = center_y + point_radius * math.sin(point_angle)
            points.extend((FLAG_X + x, FLAG_Y + self.wave_y(x, y)))
        self.canvas.create_polygon(
            points,
            fill="#ffde00",
            outline="#ffde00",
        )

    def draw_stars(self) -> None:
        large_x = FLAG_WIDTH * 5 / 30
        large_y = FLAG_HEIGHT * 5 / 20
        self.draw_star(large_x, large_y, FLAG_HEIGHT * 3 / 20, 0)

        for grid_x, grid_y in ((10, 2), (12, 4), (12, 7), (10, 9)):
            center_x = FLAG_WIDTH * grid_x / 30
            center_y = FLAG_HEIGHT * grid_y / 20
            angle = math.atan2(large_y - center_y, large_x - center_x)
            self.draw_star(
                center_x,
                center_y,
                FLAG_HEIGHT / 20,
                angle + math.pi / 2,
            )

    def animate(self) -> None:
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            48, 35, 57, FLAG_Y + FLAG_HEIGHT + 15,
            fill="#686868",
            outline="#686868",
        )
        self.draw_fabric()
        self.draw_stars()
        self.phase += 0.12
        self.root.after(40, self.animate)


if __name__ == "__main__":
    window = tk.Tk()
    window.title("中国人能飞：")
    window.resizable(False, False)
    flag = WavingFlag(window)
    window.protocol("WM_DELETE_WINDOW", lambda: (flag.close_music(), window.destroy()))
    window.mainloop()
