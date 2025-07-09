import os
import sys
from datetime import datetime
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QDateTime, QTimer
import pyodbc
import cx_Oracle
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout, QFrame, QMainWindow, QAction, QMenuBar, QComboBox, QWidgetAction, QSizePolicy
from PyQt5.QtGui import QFont, QKeySequence
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
        self.setWindowTitle("P4 PRODUCTION STATUS BOARD")
        self.setGeometry(100, 100, 1200, 400)
        self.create_ui()

        self.connect_to_database()
        self.connect_to_oracle_database()
        self.update_data_from_db()

        self.data_update_timer = QTimer(self)
        self.data_update_timer.timeout.connect(self.update_data_from_db)
        self.data_update_timer.start(3000)

    def create_ui(self):
        main_layout = QVBoxLayout()
        header_layout = QHBoxLayout()
        header_label = QLabel("P4 PRODUCTION STATUS BOARD")
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

        #header
        header_widget = QWidget()
        header_widget.setStyleSheet("background-color: #20D191; padding: 10px;")
        header_layout.addWidget(header_label)
        header_layout.addWidget(self.time_label, alignment=Qt.AlignRight)
        header_widget.setLayout(header_layout)
        header_widget.setFixedHeight(150) 

        main_layout.addWidget(header_widget)

        self.line_selector = QComboBox()
        self.line_selector.addItems([
            "SUB1(Heater Resi) LINE",
            "SUB2(Leak Test) LINE",
            "MAIN1(Charge Insp) LINE",
            "MAIN2(Calibration) LINE",
            "FINAL(Final Test) LINE",
            "FINAL(MES Matching) LINE"
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

        self.main_line_label = QLabel("SUB1(Heater Resi) LINE")
        self.main_line_label.setFont(QFont("Arial", 48, QFont.Bold))
        self.main_line_label.setAlignment(Qt.AlignLeft)
        self.main_line_label.setFixedHeight(150)

        data_layout = QVBoxLayout()
        self.sections = {
            "DESTINATION": QLabel("Loading..."),
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
            # section_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            value_label.setFont(QFont("Arial", 60, QFont.Bold))
            value_label.setAlignment(Qt.AlignRight)
            value_label.setFixedHeight(120)
            value_label.setStyleSheet("border: none;")
            # value_label.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

            if label == "GAP":
                value_label.setStyleSheet("color: red; border: none;")
            elif label == "RATE (%)":
                value_label.setStyleSheet("color: blue; border: none;")

            section_layout.addWidget(section_label)
            section_layout.addWidget(value_label)
            data_layout.addLayout(section_layout)

            if label != "RATE (%)":
                line = QFrame()
                line.setFrameShape(QFrame.HLine)
                line.setFrameShadow(QFrame.Sunken)
                data_layout.addWidget(line)
                data_layout.setSpacing(0)

        main_line_layout.addWidget(self.main_line_label)
        main_line_layout.addLayout(data_layout)
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
                if selected_line == "SUB2(Leak Test) LINE":
                    query = f"""
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P4_LEAK_COVER_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P4_LEAK_COVER_HISTORY b
                            where b.heater_id = a.heater_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                elif selected_line == "SUB1(Heater Resi) LINE":
                    query = f""" 
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P4_RESISTANCE_TEST_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P4_RESISTANCE_TEST_HISTORY b
                            where b.heater_id = a.heater_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                elif selected_line == "MAIN1(Charge Insp) LINE":
                    query = f""" 
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P4_CHARGE_INSPECTION_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P4_CHARGE_INSPECTION_HISTORY b
                            where b.mcu_id = a.mcu_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """
                elif selected_line == "MAIN2(Calibration) LINE":
                    query = f"""
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P4_CALIBRATION_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P4_CALIBRATION_HISTORY b
                            where b.mcu_id = a.mcu_id
                            and total_judgment = 'PASS'
                            and work_time >= '{start_work_time_str}'
                            and work_time < '{end_work_time_str}'
                        )
                    """

                elif selected_line == "FINAL(Final Test) LINE":
                    query = f"""
                        select count(*) as prod
                        from ITMV_KTNG_DB.dbo.AFA_P4_FINAL_TEST_HISTORY a
                        where row_id in (
                            select max(row_id)
                            from ITMV_KTNG_DB.dbo.AFA_P4_FINAL_TEST_HISTORY b
                            where b.device_id = a.device_id
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
                    if selected_line == "FINAL(MES Matching) LINE":
                        query = None

            except Exception as e:
                print(f"Error fetching data: {e}")
                self.sections["ACTUAL"].setText("Error")

        if self.oracle_conn:
            oracle_cursor = self.oracle_conn.cursor()
            try:
                oracle_query = None  # Khởi tạo biến oracle_query

                # Chỉ xác định một truy vấn cho Oracle
                if selected_line == "FINAL(MES Matching) LINE":
                    oracle_query = f""" 
                        SELECT COUNT(*) as prod
                        FROM ASFC_SUBLOT_INFO a
                        WHERE a.plant = 'PKTNG'
                        AND a.DEVICE_ATTACH_DATE >= '{start_work_time_str}'
                        AND a.DEVICE_ATTACH_DATE < '{end_work_time_str}'
                        AND a.DEVICE_ID IS NOT NULL
                        AND a.SUBLOT_USER_ID = 'P4'
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
                    select b.DESCRIPTION as destination, sum(nvl(a.work_order_qty, 0)) as plan_qty
                    from asfc_prod_plan_data a
                    LEFT OUTER JOIN SYS_SYSTEM_CODE_DATA b 
                    ON a.EXPAND_FIELD5 = b.CODE_NAME AND TABLE_NAME = 'CUSTOMER_DST'
                    WHERE a.PLANT = 'PKTNG'
                    AND forecast_sdate >= '{today_str}' 
                    AND forecast_sdate < '{tomorrow_str}'
                    AND status = 'Y'
                    AND WORK_LINE = 'C'
                    GROUP BY b.DESCRIPTION
                """
                oracle_cursor.execute(oracle_query)
                oracle_result = oracle_cursor.fetchone()

                if oracle_result:
                    destination_value = oracle_result[0]
                    plan_value = oracle_result[1]
                    self.sections["DESTINATION"].setText(destination_value)
                    self.sections["PLAN"].setText(str(plan_value))
                else:
                    self.sections["DESTINATION"].setText("No data")
                    self.sections["PLAN"].setText("No data")

            except Exception as e:
                print(f"Error fetching Oracle data: {e}")
                self.sections["DESTINATION"].setText("Error")
                self.sections["PLAN"].setText("Error")

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


def create_gui_P4(create_login_ui, create_gui_P1, create_gui_P230, create_gui_P140):
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

            switch_to_P1_action = QAction("Chuyển sang ECIGA-P1", self)
            switch_to_P1_action.triggered.connect(self.switch_to_P1)

            switch_to_P230_action = QAction("Chuyển sang ECIGA-P2 3.0", self)
            switch_to_P230_action.triggered.connect(self.switch_to_P230)

            switch_to_P140_action = QAction("Chuyển sang ECIGA-P140", self)
            switch_to_P140_action.triggered.connect(self.switch_to_P140)

            logout_action = QAction("Đăng xuất", self)
            logout_action.triggered.connect(self.logout)

            file_menu.addAction(switch_to_P1_action)
            file_menu.addAction(switch_to_P230_action)
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

        def switch_to_P230(self):
            global qt_window
            self.close()
            qt_window = create_gui_P230(create_login_ui, create_gui_P1, create_gui_P4, create_gui_P140)()
            qt_window.show()

        def switch_to_P140(self):
            global qt_window
            self.close()
            qt_window = create_gui_P140(create_login_ui, create_gui_P1, create_gui_P4, create_gui_P230)()
            qt_window.show()

    return MainWindow


