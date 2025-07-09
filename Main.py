import urllib.request
import subprocess
import os
import configparser
import sys
import cx_Oracle
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
from tkinter import messagebox
from creategui_P230 import create_gui_P230
from creategui_P4 import create_gui_P4
from creategui_P1 import create_gui_P1
from creategui_P140 import create_gui_P140
from utils import get_current_version
import qrcode
from PIL import Image, ImageTk
import PyQt5.QtWidgets

PROGRAM_DIRECTORY = "C:\\ODM_Monitering"
UPDATE_SCRIPT_EXECUTABLE = os.path.join(PROGRAM_DIRECTORY, "update_script.exe")

#FTP Server
FTP_BASE_URL = "ftp://update:update@192.168.110.12/KhanhDQ/Update_Program/ODM_Monitering/"
VERSION_URL = FTP_BASE_URL + "version.txt"

app_qt = None
qt_window = None

def save_login_info(username, password):
    config = configparser.ConfigParser()
    config['LOGIN'] = {'username': username, 'password': password}
    with open('login_info.ini', 'w') as configfile:
        config.write(configfile)

def load_login_info():
    config = configparser.ConfigParser()
    config.read('login_info.ini')
    if 'LOGIN' in config:
        return config['LOGIN']['username'], config['LOGIN']['password']
    return None, None


def create_qr_code(data, file_path):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=7,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    img.save(file_path)

def forgot_password():
    # Tạo QR code
    contact_info = "https://zalo.me/0944187335"
    qr_code_path = "contact_info_qr.png"
    create_qr_code(contact_info, qr_code_path)

    # Tạo cửa sổ thông báo
    popup = tk.Toplevel()
    popup.title("Forgot Password")
    popup.geometry("450x450")
    popup.resizable(False, False)

    # Hiển thị thông báo
    message = tk.Label(popup, text="Hãy liên hệ Khánh IT để reset mật khẩu của bạn!\n", font=("Arial Bold", 12), wraplength=280, justify="center")
    message.pack(pady=10)

    # Hiển thị QR code
    qr_image = Image.open(qr_code_path)
    qr_photo = ImageTk.PhotoImage(qr_image)
    qr_label = tk.Label(popup, image=qr_photo)
    qr_label.image = qr_photo  # Lưu tham chiếu để tránh bị garbage collected
    qr_label.pack(pady=10)

    # Nút đóng cửa sổ
    close_button = tk.Button(popup, text="CLOSE", command=popup.destroy, bg='#00796b', fg='#CCFFFF', font=("Arial", 12))
    close_button.place(relx=0.5, y=350, anchor='center', width=120, height=30)

    popup.mainloop()


def connect_to_oracle():
    connection = cx_Oracle.connect(
        user="mighty",
        password="mighty",
        dsn="(DESCRIPTION=(LOAD_BALANCE=yes)(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.35.20)(PORT=1521))(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.35.20)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=ITMVPACKMES)(FAILOVER_MODE=(TYPE=SELECT)(METHOD=BASIC))))"
    )
    return connection

def login():
    global app_qt, qt_window
    username = entry_username.get()
    password = entry_password.get()
    selected_option = option_var.get()
    remember_me_checked = remember_me_var.get()

    connection = connect_to_oracle()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM USER_DATA WHERE USERNAME = :1 AND PASSWORD = :2", (username, password))
    user = cursor.fetchone()
    connection.close()

    if user:
        if remember_me_checked:
            save_login_info(username, password)
        else:
            save_login_info("", "")
        root.destroy()
        
        # Khởi tạo QApplication nếu chưa có
        if app_qt is None:
            app_qt = PyQt5.QtWidgets.QApplication(sys.argv)
        # Chọn giao diện
        if selected_option == "ECIGA-P1":
            MainWindow = create_gui_P1(create_login_ui, create_gui_P230, create_gui_P4, create_gui_P140)
        elif selected_option == "ECIGA-P2 3.0":
            MainWindow = create_gui_P230(create_login_ui, create_gui_P1, create_gui_P4, create_gui_P140)
        elif selected_option == "ECIGA-P4":
            MainWindow = create_gui_P4(create_login_ui, create_gui_P1, create_gui_P230, create_gui_P140)
        elif selected_option == "ECIGA-P140":
            MainWindow = create_gui_P140(create_login_ui, create_gui_P1, create_gui_P230, create_gui_P4)
        elif selected_option == "ECIGA-P6(Coming Soon)":
            Plant_Comming_Soon()
            return
        qt_window = MainWindow()
        qt_window.show()
        if app_qt is not None:
            app_qt.exec_()
    else:
        messagebox.showerror("Thông báo", "Sai tên đăng nhập hoặc mật khẩu.")

def Plant_Comming_Soon():
    messagebox.showinfo("Thông báo", "Plant đang trong quá trình phát triển!")
    create_login_ui()

def get_latest_version():
    try:
        with urllib.request.urlopen(VERSION_URL) as response:
            latest_version = response.read().decode('utf-8').strip()
        return latest_version
    except Exception as e:
        print(f"Không thể lấy phiên bản mới nhất: {e}")
        return None

def check_for_updates():
    current_version = get_current_version()
    latest_version = get_latest_version()
    
    if latest_version and latest_version > current_version:
        initiate_update()

def initiate_update():
    print("Đang chuẩn bị cập nhật và khởi động lại chương trình...")
    process = subprocess.Popen([UPDATE_SCRIPT_EXECUTABLE])
    print(f"Đã khởi chạy {UPDATE_SCRIPT_EXECUTABLE}, PID: {process.pid}")
    sys.exit()

def cancel():
    root.destroy
    sys.exit()

def create_login_ui():
    global root, entry_username, entry_password, option_var, remember_me_var

    root = tk.Tk()
    root.title(f"ODM Monitoring Dashboard Version {get_current_version()}")
    root.geometry("800x550")
    root.configure(bg='#00a99d')
    root.resizable(False, False)

    # Tải ảnh nền
    background_image = Image.open("Resource/background.jpg")
    background_photo = ImageTk.PhotoImage(background_image)
    canvas = tk.Canvas(root, width=400, height=450)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=background_photo, anchor="nw")

    # Frame chính giữa
    frame = tk.Frame(root, bg='#003366', bd=0)
    frame.place(relx=0.5, rely=0.5, anchor='center', width=350, height=400)

    # Icon người dùng
    user_name = tk.Label(frame, bg='#003366', text="ODM Monitoring", fg='#66CCFF', font=("Arial Black", 18))
    user_name.place(relx=0.5, y=15, anchor='center')
    user_icon = tk.Label(frame, bg='#003366', text="ITM Semiconductor Vietnam", fg='#66CCFF', font=("Cascadia Mono SemiBold", 9))
    user_icon.place(relx=0.5, y=40, anchor='center')

    # Tiêu đề đăng nhập
    title = tk.Label(frame, text="LOGIN", fg='#66CCFF', bg='#003366', font=("Arial Black", 16))
    title.place(relx=0.5, y=80, anchor='center')

    # Tên đăng nhập
    username_frame = tk.Frame(frame, bg='#e0f7fa', bd=1, relief='solid')
    username_frame.place(relx=0.5, y=120, anchor='center', width=300, height=40)
    user_icon_label = tk.Label(username_frame, text="👤", bg='#e0f7fa', font=("Arial", 18))
    user_icon_label.place(x=10, y=5, width=30, height=30)
    entry_username = tk.Entry(username_frame, bd=0, bg='#e0f7fa', font=("Arial", 12))
    entry_username.place(x=50, y=5, width=240, height=30)

    # Mật khẩu
    password_frame = tk.Frame(frame, bg='#e0f7fa', bd=1, relief='solid')
    password_frame.place(relx=0.5, y=170, anchor='center', width=300, height=40)
    pass_icon_label = tk.Label(password_frame, text="🔒", bg='#e0f7fa', font=("Arial", 18))
    pass_icon_label.place(x=10, y=5, width=30, height=30)
    entry_password = tk.Entry(password_frame, show="*", bd=0, bg='#e0f7fa', font=("Arial", 12))
    entry_password.place(x=50, y=5, width=240, height=30)

    # Tạo combobox cho các lựa chọn
    option_var = tk.StringVar()
    option_frame = tk.Frame(frame, bg='#e0f7fa', bd=1, relief='solid')
    option_frame.place(relx=0.5, y=220, anchor='center', width=300, height=40)
    combo = ttk.Combobox(option_frame, textvariable=option_var, font=("Arial", 12), state="readonly")
    combo['values'] = ("ECIGA-P1", "ECIGA-P2 3.0", "ECIGA-P4", "ECIGA-P140", "ECIGA-P6(Coming Soon)")
    combo.place(relx=0.5, rely=0.5, anchor='center', width=240, height=30)
    combo.current(1)

    # Nút đăng nhập
    login_button = tk.Button(frame, text="LOGIN", command=login, bg='#00796b', fg='#003366', font=("Arial", 14))
    login_button.place(relx=0.5, y=270, anchor='center', width=150, height=40)
    root.bind('<Return>', lambda event: login())

    # Các tùy chọn bổ sung (ví dụ như ghi nhớ đăng nhập, quên mật khẩu)
    additional_options = tk.Frame(frame, bg='#CCFFFF')
    additional_options.place(relx=0.5, y=360, anchor='center', width=300, height=40)

    # Remember me
    remember_me_var = tk.BooleanVar()
    remember_me = tk.Checkbutton(additional_options, text="Remember me", variable=remember_me_var, bg='#CCFFFF')
    remember_me.pack(side="left", padx=10)

    # Forgot password
    forgot_password_label = tk.Label(additional_options, text="Forgot password?", fg='#00796b', bg='#CCFFFF', cursor="hand2")
    forgot_password_label.pack(side="right", padx=10)
    forgot_password_label.bind("<Button-1>", lambda e: forgot_password())

    # Load saved login info
    saved_username, saved_password = load_login_info()
    if saved_username and saved_password:
        entry_username.insert(0, saved_username)
        entry_password.insert(0, saved_password)
        remember_me_var.set(True)

    root.mainloop()


if __name__ == "__main__":
    check_for_updates()
    create_login_ui()

