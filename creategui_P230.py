import os
import sys
from datetime import datetime
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDateTime, QTimer
import pyodbc
import cx_Oracle
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QAction, QMenuBar, QComboBox, QWidgetAction, QSizePolicy
from PyQt5.QtGui import QFont, QKeySequence, QPixmap
from PyQt5.QtWidgets import QShortcut
from datetime import datetime, timedelta

def get_data_path(relative_path):
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(__file__)
    data_path = os.path.join(base_path, relative_path)
    if not os.path.exists(data_path):
        install_path = r"C:\ODM_Monitering"
        data_path = os.path.join(install_path, relative_path)
    
    return data_path

class ProductionStatusBoard(QWidget):
    def __init__(self, menu_bar):
        super().__init__()
        self.menu_bar = menu_bar
        self.current_color_value = "GREEN"  # Khởi tạo màu mặc định
        self.setWindowTitle("P2HB 3.0 PRODUCTION STATUS BOARD")
        self.setGeometry(100, 100, 1200, 400)
        self.create_ui()

        self.connect_to_database()
        self.connect_to_oracle_database()
        
        # Hiển thị hình ảnh mặc định ngay khi khởi tạo
        self.update_color_image("GREEN")
        
        self.update_data_from_db()

        self.data_update_timer = QTimer(self)
        self.data_update_timer.timeout.connect(self.update_data_from_db)
        self.data_update_timer.start(3000)

    def create_ui(self):
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_label = QLabel("P2HB 3.0 PRODUCTION STATUS BOARD")
        header_label.setFont(QFont("Arial", 24, QFont.Bold))
        header_label.setStyleSheet("color: white;")
        header_label.setAlignment(Qt.AlignLeft)

        self.time_label = QLabel()
        self.time_label.setFont(QFont("Arial", 24))
        self.time_label.setStyleSheet("color: white;")
        self.update_time()
        timer = QTimer(self)
        timer.timeout.connect(self.update_time)
        timer.start(1000)

        # Lưu trữ references để có thể cập nhật màu sắc sau
        self.header_widget = QWidget()
        self.header_label = header_label
        self.header_widget.setStyleSheet("background-color: #20D191; padding: 10px;")
        
        # Điều chỉnh layout để time không bị che khuất bởi hình ảnh
        header_layout.addWidget(header_label)
        header_layout.addStretch()  # Thêm space để đẩy time về giữa
        header_layout.addWidget(self.time_label)
        header_layout.addStretch()  # Thêm space để tránh hình ảnh che khuất
        
        self.header_widget.setLayout(header_layout)
        self.header_widget.setFixedHeight(150) 

        main_layout.addWidget(self.header_widget)

        # Tạo layout chính cho nội dung
        main_line_layout = QVBoxLayout()
        main_line_frame = QFrame()
        main_line_frame.setFixedHeight(850)
        main_line_frame.setStyleSheet("""
            background-color: white;
            border: 2px solid #E0E0E0;
            border-radius: 20px;
            padding: 20px;
        """)

        self.main_line_label = QLabel("INSP3(Calibration) LINE")
        self.main_line_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.main_line_label.setAlignment(Qt.AlignLeft)
        self.main_line_label.setFixedHeight(150)

        # Tạo layout ngang cho hình ảnh và dữ liệu
        content_layout = QHBoxLayout()
        
        # Tạo hình ảnh màu ở bên trái
        self.color_image_label = QLabel()
        self.color_image_label.setFixedSize(330, 600)  # Tỷ lệ 1:4 phù hợp với hình ảnh dài
        self.color_image_label.setStyleSheet("background-color: transparent; border: none; padding: 5px;")
        self.color_image_label.setAlignment(Qt.AlignCenter)
        self.color_image_label.setScaledContents(True)  # Bật auto scale để tránh cắt xén
        
        # Thêm hình ảnh vào layout bên trái
        content_layout.addWidget(self.color_image_label)
        
        # Tạo layout dữ liệu bên phải
        data_layout = QVBoxLayout()

        self.line_selector = QComboBox()
        self.line_selector.addItems([
            "SUB(Leak) LINE",
            "INSP3(Calibration) LINE",
            "MAIN(Charger Current) LINE",
            "INSP 4-1(S/N Writing) LINE",
            "INSP 4-2(MES Matching) LINE",
            "PACKING(Carton Box) LINE"
        ])
        self.line_selector.currentIndexChanged.connect(self.update_data_from_db)

        line_menu = self.menu_bar.addMenu("Select Line")
        line_action = QWidgetAction(self)
        line_action.setDefaultWidget(self.line_selector)
        line_menu.addAction(line_action)

        main_line_layout = QVBoxLayout()
        main_line_frame = QFrame()
        main_line_frame.setFixedHeight(850)
        main_line_frame.setStyleSheet("""
            background-color: white;
            border: 2px solid #E0E0E0;
            border-radius: 20px;
            padding: 20px;
        """)

        self.main_line_label = QLabel("INSP3(Calibration) LINE")
        self.main_line_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.main_line_label.setAlignment(Qt.AlignLeft)
        self.main_line_label.setFixedHeight(150)

        data_layout = QVBoxLayout()
        self.sections = {
            "COLOR / DESTINATION": QLabel("Loading..."),
            "PLAN": QLabel("Loading..."),
            "ACTUAL": QLabel("Loading..."),
            "GAP": QLabel("Loading..."),
            "RATE (%)": QLabel("Loading...")
        }

        for label, value_label in self.sections.items():
            section_layout = QHBoxLayout()

            section_label = QLabel(label)
            section_label.setFont(QFont("Arial", 40))
            section_label.setAlignment(Qt.AlignLeft)
            section_label.setFixedHeight(120)
            section_label.setStyleSheet("border: none;")
            
            value_label.setFont(QFont("Arial", 60, QFont.Bold))
            value_label.setAlignment(Qt.AlignRight)
            value_label.setFixedHeight(120)
            value_label.setStyleSheet("border: none;")
            
            if label == "GAP":
                value_label.setStyleSheet("color: red; border: none;")
            elif label == "RATE (%)":
                value_label.setStyleSheet("color: blue; border: none;")
            elif label == "COLOR / DESTINATION":
                # Lưu trữ reference để có thể cập nhật màu sau
                self.color_destination_label = value_label

            section_layout.addWidget(section_label)
            section_layout.addWidget(value_label)
            data_layout.addLayout(section_layout)

            if label != "RATE (%)":
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                data_layout.addWidget(line)
                data_layout.setSpacing(0)

        # Thêm layout dữ liệu vào layout ngang
        content_layout.addLayout(data_layout)
        
        # Thêm các thành phần vào layout chính
        main_line_layout.addWidget(self.main_line_label)
        main_line_layout.addLayout(content_layout)
        main_line_frame.setLayout(main_line_layout)
        main_layout.addWidget(main_line_frame)

        footer_label = QLabel("Powered by ITM Semiconductor Vietnam Company Limited - IT Team. Copyright © 2024 all rights reserved.")
        footer_label.setFont(QFont("Arial", 10))
        footer_label.setAlignment(Qt.AlignRight)
        footer_label.setStyleSheet("color: gray; padding: 10px;")
        
        main_layout.addWidget(footer_label, alignment=Qt.AlignBottom)
        self.setLayout(main_layout)

    def connect_to_database(self):
        try:
            self.conn = pyodbc.connect(
                'DRIVER={ODBC Driver 17 for SQL Server};'
                'SERVER=192.168.35.32,1433;'
                'DATABASE=ITMV_KTNG_DB;'
                'UID=ITMV_KTNG;'
                'PWD=!itm@semi!12;'
            )
        except Exception as e:
            print(f"Error connecting to SQL Server database: {e}")
            self.conn = None

    def connect_to_oracle_database(self):
        try:
            self.oracle_conn = cx_Oracle.connect(
                user="mighty",
                password="mighty",
                dsn="(DESCRIPTION=(LOAD_BALANCE=yes)(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.35.20)(PORT=1521))(ADDRESS=(PROTOCOL=TCP)(HOST=192.168.35.20)(PORT=1521))(CONNECT_DATA=(SERVICE_NAME=ITMVPACKMES)(FAILOVER_MODE=(TYPE=SELECT)(METHOD=BASIC))))"
            )
        except Exception as e:
            print(f"Error connecting to Oracle database: {e}")
            self.oracle_conn = None

    def update_data_from_db(self):
        selected_line = self.line_selector.currentText()
        self.main_line_label.setText(f"{selected_line}")

        actual_value = 0
        plan_value = 0

        today = datetime.now()
        tomorrow = today + timedelta(days=1)

        today_str = today.strftime('%Y%m%d')
        tomorrow_str = tomorrow.strftime('%Y%m%d')
        start_work_time_str = today.strftime('%Y%m%d') + '070000'
        end_work_time_str = tomorrow.strftime('%Y%m%d') + '070000'

        if self.conn:
            cursor = self.conn.cursor()
            try:
                query = None  # Khởi tạo biến query

                # Xác định truy vấn dựa trên dòng đã chọn
                if selected_line == "INSP3(Calibration) LINE":
                    query = f"""
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P2HB3_CALIBRATION_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P2HB3_CALIBRATION_HISTORY b
                            where b.mcu_id = a.mcu_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                elif selected_line == "SUB(Leak) LINE":
                    query = f""" 
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_SEAL_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_SEAL_HISTORY b
                            where b.qr_code = a.qr_code
                            and st_press_rst = 'P'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                elif selected_line == "MAIN(Charger Current) LINE":
                    query = f""" 
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P2HB3_CHARGE_INSPECTION_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P2HB3_CHARGE_INSPECTION_HISTORY b
                            where b.mcu_id = a.mcu_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                elif selected_line == "INSP 4-1(S/N Writing) LINE":
                    query = f"""
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P2HB3_SNRW_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P2HB3_SNRW_HISTORY b
                            where b.mcu_id = a.mcu_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                # Chỉ thực hiện truy vấn nếu biến query không phải là None
                if query:
                    cursor.execute(query)
                    result = cursor.fetchone()

                    if result:
                        actual_value = result[0]
                        self.sections["ACTUAL"].setText(str(actual_value))
                    else:
                        self.sections["ACTUAL"].setText("No data")
                else:
                    if selected_line == "INSP 4-2(MES Matching) LINE" or "PACKING(Carton Box) LINE":
                        query = None

            except Exception as e:
                print(f"Error fetching data: {e}")
                self.sections["ACTUAL"].setText("Error")

        if self.oracle_conn:
            oracle_cursor = self.oracle_conn.cursor()
            try:
                oracle_query = None  # Khởi tạo biến oracle_query

                # Chỉ xác định một truy vấn cho Oracle
                if selected_line == "INSP 4-2(MES Matching) LINE":
                    oracle_query = f""" 
                        SELECT COUNT(*) as prod
                        FROM ASFC_SUBLOT_INFO a
                        WHERE a.plant = 'PKTNG'
                        AND a.DEVICE_ATTACH_DATE >= '{start_work_time_str}'
                        AND a.DEVICE_ATTACH_DATE < '{end_work_time_str}'
                        AND a.DEVICE_ID IS NOT NULL
                        AND a.SUBLOT_USER_ID = 'P3'
                    """
                elif selected_line == "PACKING(Carton Box) LINE":
                    oracle_query = f""" 
                        SELECT COUNT(*) as prod
                        FROM ASFC_SUBLOT_INFO a
                        WHERE a.plant = 'PKTNG'
                        AND a.CBOX_ATTACH_DATE >= '{start_work_time_str}'
                        AND a.CBOX_ATTACH_DATE < '{end_work_time_str}'
                        AND a.CARTON_BOX_ID IS NOT NULL
                        AND a.SUBLOT_USER_ID = 'P3'
                    """

                # Chỉ thực hiện truy vấn nếu biến oracle_query không phải là None
                if oracle_query:
                    oracle_cursor.execute(oracle_query)
                    oracle_result = oracle_cursor.fetchone()

                    if oracle_result:
                        actual_value = oracle_result[0]
                        self.sections["ACTUAL"].setText(str(actual_value))
                    else:
                        self.sections["ACTUAL"].setText("No data")

                # Phần truy vấn kế hoạch
                oracle_query = f"""
                    SELECT 
                        b.DESCRIPTION AS destination, 
                        SUM(NVL(a.work_order_qty, 0)) AS plan_qty,
                        MAX(a.ITEM_CODE) AS item_code
                    FROM asfc_prod_plan_data a
                    LEFT OUTER JOIN SYS_SYSTEM_CODE_DATA b 
                        ON a.EXPAND_FIELD5 = b.CODE_NAME 
                        AND b.TABLE_NAME = 'CUSTOMER_DST'
                    WHERE 
                        a.PLANT = 'PKTNG'
                        AND a.forecast_sdate >= '{today_str}' 
                        AND a.forecast_sdate < '{tomorrow_str}'
                        AND a.status = 'Y'
                        AND a.WORK_LINE = 'D'
                    GROUP BY 
                        b.DESCRIPTION
                """
                oracle_cursor.execute(oracle_query)
                oracle_result = oracle_cursor.fetchone()

                if oracle_result:
                    destination_value = oracle_result[0]
                    plan_value = oracle_result[1]

                    device_id = oracle_result[2]
                    color_query = f"""
                                SELECT GET_SYSCODE_DESC_ONLY(PLANT,'DEVICE_COLOR' ,EXPAND_FIELD22) AS COLOR   
                                FROM ( 
                                        SELECT  A.PLANT
                                            , B.DEVICE
                                            , B.DEVICE_LTYPE
                                            , B.DEVICE_MTYPE
                                            , B.DEVICE_STYPE
                                            , B.EXPAND_FIELD20 
                                            , B.EXPAND_FIELD21 
                                            , B.EXPAND_FIELD22 
                                            , B.EXPAND_FIELD23 
                                            , GROUP_CATEGORY
                                            , GROUP_OBJECT
                                            , GROUP_VALUE             
                                        FROM ADM_GROUP_CATEGORY_DATA A
                                            , ADM_DEVICE_SPEC B
                                        WHERE A.PLANT = 'PKTNG'
                                        AND A.PLANT = B.PLANT 
                                        AND A.GROUP_TARGET = 'DEVICE'
                                        AND A.GROUP_OBJECT = '{device_id}'
                                        AND B.DEVICE = A.GROUP_OBJECT
                                    ) 
                                PIVOT (
                                        MIN(GROUP_VALUE) FOR GROUP_CATEGORY IN (
                                                                                'Device Product Code' AS Device_Product_Code
                                                                                , 'Sleeve Code' AS SLEEVE_CODE
                                                                                , 'Destination' AS DESTINATION
                                                                                , 'Ship_Type' AS SHIP_TYPE )
                                    )
                                """

                    color_result = oracle_cursor.execute(color_query).fetchone()
                    color_value = color_result[0] if color_result else "N/A"
                    
                    # Cập nhật header color dựa trên color_value
                    if color_value and color_value != "N/A":
                        self.update_header_color(color_value)
                    
                    self.sections["COLOR / DESTINATION"].setText(f"{color_value} / {destination_value}")
                    self.sections["PLAN"].setText(str(plan_value))
                else:
                    self.sections["COLOR / DESTINATION"].setText("No data")
                    self.sections["PLAN"].setText("No data")
                    # Reset về màu mặc định khi không có dữ liệu
                    self.update_header_color("GREEN")
                    # Reset màu chữ COLOR / DESTINATION về đen
                    if hasattr(self, 'color_destination_label'):
                        self.color_destination_label.setStyleSheet("color: black; border: none;")
                    # Reset hình ảnh về mặc định
                    if hasattr(self, 'color_image_label'):
                        self.color_image_label.clear()
                        self.color_image_label.setText("N/A")
                        self.color_image_label.setStyleSheet("background-color: transparent; border: none; color: gray; font-weight: bold; font-size: 16px;")

            except Exception as e:
                print(f"Error fetching Oracle data: {e}")
                self.sections["COLOR / DESTINATION"].setText("Error")
                self.sections["PLAN"].setText("Error")
                # Reset về màu mặc định khi có lỗi
                self.update_header_color("GREEN")
                # Reset màu chữ COLOR / DESTINATION về đen
                if hasattr(self, 'color_destination_label'):
                    self.color_destination_label.setStyleSheet("color: black; border: none;")
                # Reset hình ảnh về mặc định
                if hasattr(self, 'color_image_label'):
                    self.color_image_label.clear()
                    self.color_image_label.setText("ERR")
                    self.color_image_label.setStyleSheet("background-color: transparent; border: none; color: red; font-weight: bold; font-size: 16px;")

        # Update GAP and RATE(%)
        if plan_value > 0:
            gap_value = actual_value - plan_value
            rate_value = (actual_value / plan_value) * 100
            self.sections["GAP"].setText(str(gap_value))
            self.sections["RATE (%)"].setText(f"{round(rate_value)}%")
        else:
            self.sections["GAP"].setText("N/A")
            self.sections["RATE (%)"].setText("N/A")



    def update_time(self):
        current_time = QDateTime.currentDateTime()
        self.time_label.setText(current_time.toString("yyyy-MM-dd HH:mm:ss"))

    def update_header_color(self, color_value):
        """Cập nhật màu sắc header dựa trên color_value"""
        # Mapping màu sắc từ tên sang mã hex
        color_mapping = {
            'BLACK': '#000000',
            'RED': '#FF0000',
            'YELLOW': '#FFFF00',
            'GREEN': '#008000',
            'BLUE': '#0000FF',
            'WHITE': '#FFFFFF',
            'ORANGE': '#FFA500',
            'PURPLE': '#800080',
            'PINK': '#FFC0CB',
            'GRAY': '#808080',
            'GREY': '#808080',
            'BROWN': '#A52A2A',
            'CYAN': '#00FFFF',
            'MAGENTA': '#FF00FF',
            'LIME': '#00FF00',
            'NAVY': '#000080',
            'MAROON': '#800000',
            'OLIVE': '#808000',
            'TEAL': '#008080',
            'SILVER': '#C0C0C0'
        }
        
        # Lấy màu background, mặc định là màu xanh lá cây nếu không tìm thấy
        bg_color = color_mapping.get(color_value.upper(), '#20D191')
        
        # Xác định màu text dựa trên độ sáng của background
        # Những màu sáng sẽ dùng text đen, màu tối sẽ dùng text trắng
        light_colors = ['YELLOW', 'WHITE', 'ORANGE', 'PINK', 'CYAN', 'LIME', 'SILVER']
        text_color = 'black' if color_value.upper() in light_colors else 'white'
        
        # Cập nhật style của header widget
        self.header_widget.setStyleSheet(f"background-color: {bg_color}; padding: 10px;")
        
        # Cập nhật màu text của header label và time label
        self.header_label.setStyleSheet(f"color: {text_color};")
        self.time_label.setStyleSheet(f"color: {text_color};")
        
        # Cập nhật màu chữ cho COLOR / DESTINATION label
        color_hex = color_mapping.get(color_value.upper(), '#000000')
        if hasattr(self, 'color_destination_label'):
            self.color_destination_label.setStyleSheet(f"color: {color_hex}; border: none;")
        
        # Cập nhật hình ảnh màu
        self.update_color_image(color_value)
    
    def update_color_image(self, color_value):
        """Cập nhật hình ảnh màu dựa trên color_value"""
        if not hasattr(self, 'color_image_label'):
            return
            
        # Mapping tên màu sang tên file
        color_file_mapping = {
            'BLACK': 'black.png',
            'RED': 'red.png',
            'YELLOW': 'yellow.png',
            'GREEN': 'green.png',
            'BLUE': 'blue.png',
            'WHITE': 'white.png',
            'ORANGE': 'orange.png',
            'PURPLE': 'purple.png',
            'PINK': 'pink.png',
            'GRAY': 'gray.png',
            'GREY': 'gray.png',
            'BROWN': 'brown.png',
            'CYAN': 'cyan.png',
            'MAGENTA': 'magenta.png',
            'LIME': 'lime.png',
            'NAVY': 'navy.png',
            'MAROON': 'maroon.png',
            'OLIVE': 'olive.png',
            'TEAL': 'teal.png',
            'SILVER': 'silver.png'
        }
        
        # Lấy tên file ảnh
        image_filename = color_file_mapping.get(color_value.upper(), 'default.png')
        image_path = get_data_path(f"Resource/{image_filename}")
        
        # Kiểm tra file có tồn tại không
        if os.path.exists(image_path):
            pixmap = QPixmap(image_path)
            # Với setScaledContents(True), chỉ cần set pixmap trực tiếp
            # Qt sẽ tự động scale để vừa với container và giữ tỷ lệ
            self.color_image_label.setPixmap(pixmap)
        else:
            # Nếu không tìm thấy file, hiển thị text màu
            self.color_image_label.clear()
            self.color_image_label.setText(color_value)
            self.color_image_label.setStyleSheet(f"background-color: transparent; border: none; color: {color_value.lower()}; font-weight: bold; font-size: 16px;")

    def resizeEvent(self, event):
        """Cập nhật khi thay đổi kích thước cửa sổ"""
        super().resizeEvent(event)
        # Hình ảnh giờ đây được quản lý bởi layout, không cần di chuyển thủ công

def create_gui_P230(create_login_ui, create_gui_P1, create_gui_P4, create_gui_P140):
    class MainWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Main Window")
            self.setGeometry(100, 100, 1200, 800)

            self.fullscreen_shortcut = QShortcut(QKeySequence("F11"), self)
            self.fullscreen_shortcut.activated.connect(self.toggle_fullscreen)

            self.is_fullscreen = True

            # Menubar
            menubar = QMenuBar(self)
            self.setMenuBar(menubar)

            file_menu = menubar.addMenu("Menu")

            # Menu actions
            switch_to_P1_action = QAction("Chuyển sang ECIGA-P1", self)
            switch_to_P1_action.triggered.connect(self.switch_to_P1)

            switch_to_P4_action = QAction("Chuyển sang ECIGA-P4", self)
            switch_to_P4_action.triggered.connect(self.switch_to_P4)

            switch_to_P140_action = QAction("Chuyển sang ECIGA-P140", self)
            switch_to_P140_action.triggered.connect(self.switch_to_P140)

            logout_action = QAction("Đăng xuất", self)
            logout_action.triggered.connect(self.logout)

            file_menu.addAction(switch_to_P1_action)
            file_menu.addAction(switch_to_P4_action)
            file_menu.addAction(switch_to_P140_action)
            file_menu.addAction(logout_action)

            self.ui = ProductionStatusBoard(menubar)
            self.setCentralWidget(self.ui)

            self.showFullScreen()

        def toggle_fullscreen(self):
            if self.is_fullscreen:
                self.showNormal()
            else:
                self.showFullScreen()
            self.is_fullscreen = not self.is_fullscreen

        def logout(self):
            global qt_window
            self.close()
            qt_window = create_login_ui()
            if qt_window: qt_window.show()

        def switch_to_P1(self):
            global qt_window
            self.close()
            qt_window = create_gui_P1(create_login_ui, create_gui_P230, create_gui_P4, create_gui_P140)()
            qt_window.show()

        def switch_to_P4(self):
            global qt_window
            self.close()
            qt_window = create_gui_P4(create_login_ui, create_gui_P1, create_gui_P230, create_gui_P140)()
            qt_window.show()

        def switch_to_P140(self):
            global qt_window
            self.close()
            qt_window = create_gui_P140(create_login_ui, create_gui_P1, create_gui_P4, create_gui_P230)()
            qt_window.show()

    return MainWindow
