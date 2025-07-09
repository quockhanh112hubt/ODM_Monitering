import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import font as tkFont
import os
import shutil
import zipfile
import ctypes
import sys
import winreg
import winshell
from win32com.client import Dispatch
from PIL import Image, ImageTk
import subprocess
import time
import threading
import pythoncom

# Đường dẫn tới thư mục chứa các file chương trình
PROGRAM_DIRECTORY = "C:\\ODM_Monitering"
MAIN_EXECUTABLE = os.path.join(PROGRAM_DIRECTORY, "main.exe")
ODBC17_EXECUTABLE = os.path.join(PROGRAM_DIRECTORY, "ODBC17.msi")

def copy_files(src, dst, progress_var, step):
    try:
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)
        progress_var.set(progress_var.get() + step)
    except Exception as e:
        print(f"Lỗi khi sao chép tệp: {e}")

def extract_zip(zip_path, extract_to, progress_var, step):
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print("Giải nén thành công.")
        progress_var.set(progress_var.get() + step)
    except Exception as e:
        print(f"Lỗi khi giải nén: {e}")

def add_to_path(system_path, progress_var, step):
    try:
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            0, winreg.KEY_ALL_ACCESS
        )
        value, _ = winreg.QueryValueEx(key, "Path")
        if system_path not in value:
            new_value = value + ";" + system_path
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_value)
            winreg.CloseKey(key)
            ctypes.windll.user32.SendMessageW(0xFFFF, 0x1A, 0, "Environment")
            print(f"Đã thêm {system_path} vào PATH.")
        else:
            print(f"{system_path} đã tồn tại trong PATH.")
        progress_var.set(progress_var.get() + step)
    except Exception as e:
        print(f"Lỗi khi thêm vào PATH: {e}")

def create_shortcut(target_path, icon_path, shortcut_path, program_dir, progress_var, step):
    try:
        pythoncom.CoInitialize()
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(shortcut_path)
        shortcut.Targetpath = target_path
        shortcut.IconLocation = icon_path
        shortcut.WorkingDirectory = program_dir
        shortcut.save()
        pythoncom.CoUninitialize()
        print("Đã tạo shortcut.")
        progress_var.set(progress_var.get() + step)
    except Exception as e:
        print(f"Lỗi khi tạo shortcut: {e}")

def main(progress_var):
    program_dir = "C:\\ODM_Monitering"
    if getattr(sys, 'frozen', False):
        current_dir = sys._MEIPASS
    else:
        current_dir = os.path.dirname(os.path.abspath(__file__))

    zip_file = os.path.join(current_dir, "file.zip")
    instant_client_path = os.path.join(program_dir, "instantclient", "instantclient_23_4")
    icon_path = os.path.join(program_dir, "Resource", "Icon.ico")

    os.makedirs(program_dir, exist_ok=True)

    if zip_file.endswith(".zip"):
        extract_zip(zip_file, program_dir, progress_var, 25)
    else:
        copy_files(zip_file, program_dir, progress_var, 25)

    set_full_permissions(program_dir)
    add_to_path(instant_client_path, progress_var, 25)

    target_path = r"C:\ODM_Monitering\Main.exe"
    shortcut_path = os.path.join(winshell.desktop(), "ODM_Monitering.lnk")
    create_shortcut(target_path, icon_path, shortcut_path, program_dir, progress_var, 25)

    try:
        process = subprocess.Popen(['msiexec', '/i', ODBC17_EXECUTABLE])
        print(f"Đã khởi chạy chương trình cài đặt, PID: {process.pid}")
    except Exception as e:
        print(f"Lỗi khi khởi chạy ODBC17.msi: {e}")

    progress_var.set(100)
    # messagebox.showinfo("Thông báo", "Chương trình đã cài đặt hoàn tất.")
    close_window(root)
    cancel()

def set_full_permissions(path):
    try:
        command = f'icacls "{path}" /grant Everyone:(OI)(CI)F /T'
        subprocess.run(command, shell=True, check=True)
        print(f"Đã thiết lập quyền truy cập đầy đủ cho thư mục: {path}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("Lỗi", f"Lỗi khi thiết lập quyền truy cập: {e}")

def start_installation():
    submit_button.place_forget()  # Ẩn nút "Setup" sau khi nhấn
    progress_var = tk.DoubleVar()
    progress_bar = ttk.Progressbar(root, orient="horizontal", length=770, mode="determinate", variable=progress_var)
    progress_bar.place(x=15, y=300)
    progress_var.set(0)

    root.update()

    install_thread = threading.Thread(target=main, args=(progress_var,))
    install_thread.start()

def restart_program(root):
    try:
        if os.path.exists(MAIN_EXECUTABLE):
            process = subprocess.Popen([MAIN_EXECUTABLE])
            print(f"Đã khởi chạy lại chương trình, PID: {process.pid}")
            close_window(root)  # Đóng cửa sổ cập nhật trước khi thoát chương trình hiện tại
            time.sleep(1)
            sys.exit()
        else:
            print(f"Không tìm thấy tệp {MAIN_EXECUTABLE}")
            messagebox.showerror("Lỗi", f"Không tìm thấy tệp {MAIN_EXECUTABLE}")
    except Exception as e:
        print(f"Lỗi khi khởi động lại chương trình: {e}")
        messagebox.showerror("Lỗi", f"Lỗi khi khởi động lại chương trình: {e}")

def get_data_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)

    # Kiểm tra xem đường dẫn này có tồn tại không
    data_path = os.path.join(base_path, relative_path)
    if not os.path.exists(data_path):
        # Nếu không tồn tại, sử dụng đường dẫn cài đặt chương trình
        install_path = r"C:\ODM_Monitering"
        data_path = os.path.join(install_path, relative_path)
    
    return data_path

def cancel():
    sys.exit()

def close_window(root):
    root.destroy()

class Ui_InextendChecker:
    
    def __init__(self, root):
        self.root = root
        self.is_running = False
        root.title(f"ODM_Monitering setup")
        root.geometry("800x400")
        root.configure(bg='#888888')
        root.resizable(False, False)

        lbl_bg = tk.Label(root, text="")
        lbl_bg.place(x=10, y=10, width=780, height=315)

        image_path = get_data_path('Logo/logo.png')
        image = Image.open(image_path)
        image = image.resize((180, 100), Image.LANCZOS)
        photo = ImageTk.PhotoImage(image)
        lbl_Logo = tk.Label(root, image=photo, anchor='nw')
        lbl_Logo.image = photo
        lbl_Logo.place(x=15, y=15, width=190, height=121)

        lbl_Name1 = tk.Label(root, text="ODM_Monitering", font=("Arial", 22, "bold italic"))
        lbl_Name1.place(x=210, y=40, width=290, height=25)
        lbl_Name = tk.Label(root, text="SETUP", font=("Arial", 22, "bold italic"))
        lbl_Name.place(x=350, y=70, width=240, height=25)

        lbl_detail = tk.Label(root, text="Trình cài đặt ODM_Monitering lên máy tính của bạn.", font=("Arial", 12, "bold"), anchor='w')
        lbl_detail.place(x=210, y=150, width=440, height=25)
        lbl_detail1 = tk.Label(root, text="- Nhấn <Setup> để tiến hành cài đặt.", font=("Arial", 10), anchor='w')
        lbl_detail1.place(x=300, y=200, width=240, height=25)
        lbl_detail1 = tk.Label(root, text="- Nhấn <Cancel> để huỷ và thoát khỏi trình cài đặt.", font=("Arial", 10), anchor='w')
        lbl_detail1.place(x=300, y=250, width=340, height=25)

        global submit_button
        submit_button = ttk.Button(root, text="Setup", command=start_installation)
        submit_button.place(x=570, y=350, width=100, height=30)
        cancel_button = ttk.Button(root, text="Cancel", command=cancel)
        cancel_button.place(x=690, y=350, width=100, height=30)

def create_gui():
    global root
    root = tk.Tk()
    ui = Ui_InextendChecker(root)
    root.mainloop()

if __name__ == "__main__":
    if ctypes.windll.shell32.IsUserAnAdmin():
        create_gui()
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)
