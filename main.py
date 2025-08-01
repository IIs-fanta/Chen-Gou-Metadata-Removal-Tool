import sys
import os
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QCheckBox,
                             QLabel, QMenu, QAction, QMessageBox, QProgressBar, QFrame, QLineEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QIcon, QDragEnterEvent, QDropEvent, QColor, QPalette, QFont
from PIL import Image
import piexif
import shutil
import time

# 获取图标文件的绝对路径
def get_icon_path(icon_name):
    # 获取当前脚本所在目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 尝试多种路径
    possible_paths = [
        os.path.join(current_dir, icon_name),  # 当前目录
        icon_name,  # 相对路径
        os.path.join(os.getcwd(), icon_name),  # 工作目录
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    # 如果都找不到，返回原始名称
    return icon_name

def set_application_icon(app, icon_name):
    """设置应用程序图标"""
    icon_path = get_icon_path(icon_name)
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))
        print(f"成功设置应用程序图标: {icon_path}")
    else:
        print(f"警告: 找不到图标文件 {icon_path}")

class ImageProcessor(QThread):
    progress_updated = pyqtSignal(int)
    task_completed = pyqtSignal(str)
    all_tasks_completed = pyqtSignal()
    
    def __init__(self, image_paths, output_dir, keep_original_name):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.keep_original_name = keep_original_name
        self.is_running = True
        
    def run(self):
        total = len(self.image_paths)
        for i, image_path in enumerate(self.image_paths):
            if not self.is_running:
                break
                
            try:
                # 获取原始文件名
                filename = os.path.basename(image_path)
                
                # 如果不保留原始文件名，则使用时间戳命名
                if not self.keep_original_name:
                    name, ext = os.path.splitext(filename)
                    filename = f"{int(time.time())}_{i}{ext}"
                
                output_path = os.path.join(self.output_dir, filename)
                
                # 打开图片
                img = Image.open(image_path)
                
                # 保存图片，但不包含元数据
                img_format = img.format
                if img_format == 'JPEG':
                    # 对于JPEG，我们可以使用piexif来删除所有元数据
                    img_without_exif = Image.new(img.mode, img.size)
                    img_without_exif.putdata(list(img.getdata()))
                    img_without_exif.save(output_path, format=img_format, quality=100)
                else:
                    # 对于其他格式，直接保存而不添加元数据
                    img_without_exif = Image.new(img.mode, img.size)
                    img_without_exif.putdata(list(img.getdata()))
                    img_without_exif.save(output_path, format=img_format)
                
                self.task_completed.emit(f"已处理: {filename}")
            except Exception as e:
                self.task_completed.emit(f"处理失败: {filename} - {str(e)}")
            
            # 更新进度
            progress = int((i + 1) / total * 100)
            self.progress_updated.emit(progress)
        
        self.all_tasks_completed.emit()
    
    def stop(self):
        self.is_running = False


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("陈狗元数据去除")
        self.setMinimumSize(600, 500)
        
        # 设置窗口图标
        self.setWindowIcon(QIcon(get_icon_path("logo.ico")))
        
        # 存储任务队列
        self.image_paths = []
        self.output_dir = ""
        self.processor = None
        
        self.init_ui()
        
    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("陈狗元数据去除工具")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title_label)
        
        # 副标题
        subtitle_label = QLabel("一键清除图片元数据")
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(subtitle_label)
        
        # 顶部区域 - 导入和输出选择
        top_layout = QHBoxLayout()
        
        # 导入按钮
        self.import_btn = QPushButton("导入图片")
        self.import_btn.clicked.connect(self.import_images)
        top_layout.addWidget(self.import_btn)
        
        # 输出文件夹选择按钮
        self.output_btn = QPushButton("选择输出文件夹")
        self.output_btn.clicked.connect(self.select_output_dir)
        top_layout.addWidget(self.output_btn)
        
        main_layout.addLayout(top_layout)
        
        # 输出文件夹地址输入区域
        output_input_layout = QHBoxLayout()
        
        # 输出文件夹地址标签
        output_label = QLabel("输出文件夹地址:")
        output_input_layout.addWidget(output_label)
        
        # 输出文件夹地址输入框
        self.output_path_input = QLineEdit()
        self.output_path_input.setPlaceholderText("请输入或选择输出文件夹地址")
        self.output_path_input.textChanged.connect(self.on_output_path_changed)
        output_input_layout.addWidget(self.output_path_input, 1)  # 1表示拉伸因子
        
        # 浏览按钮
        self.browse_btn = QPushButton("浏览")
        self.browse_btn.clicked.connect(self.select_output_dir)
        output_input_layout.addWidget(self.browse_btn)
        
        main_layout.addLayout(output_input_layout)
        
        # 输出文件夹路径显示（保留用于显示当前选择的路径）
        self.output_label = QLabel("未选择输出文件夹")
        main_layout.addWidget(self.output_label)
        
        # 保留原文件名选项
        self.keep_name_cb = QCheckBox("保留原始文件名")
        self.keep_name_cb.setChecked(True)
        main_layout.addWidget(self.keep_name_cb)
        
        # 创建拖放提示区域
        self.drop_area = QFrame()
        self.drop_area.setFrameShape(QFrame.StyledPanel)
        self.drop_area.setFrameShadow(QFrame.Sunken)
        self.drop_area.setMinimumHeight(100)
        self.drop_area.setAutoFillBackground(True)
        
        # 添加拖放提示标签
        drop_layout = QVBoxLayout(self.drop_area)
        drop_label = QLabel("拖放图片到这里")
        drop_font = QFont()
        drop_font.setPointSize(12)
        drop_font.setBold(True)
        drop_label.setFont(drop_font)
        drop_label.setAlignment(Qt.AlignCenter)
        drop_layout.addWidget(drop_label)
        
        main_layout.addWidget(self.drop_area)
        
        # 任务队列标签
        queue_label = QLabel("任务队列 (右键可清空):")
        main_layout.addWidget(queue_label)
        
        # 任务队列列表
        self.task_list = QListWidget()
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_context_menu)
        # 不需要在列表上设置接受拖放，因为我们在主窗口上设置了
        # self.task_list.setAcceptDrops(True)
        self.task_list.setDragEnabled(True)
        main_layout.addWidget(self.task_list)
        
        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)
        
        # 执行按钮
        self.execute_btn = QPushButton("执行")
        self.execute_btn.setIcon(QIcon(get_icon_path("logo.ico")))
        self.execute_btn.clicked.connect(self.execute_tasks)
        main_layout.addWidget(self.execute_btn)
        
        # 设置中央窗口部件
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)
        
        # 启用拖放
        self.setAcceptDrops(True)
    
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
    
    def dragLeaveEvent(self, event):
        pass
    
    def dropEvent(self, event: QDropEvent):
        files = [url.toLocalFile() for url in event.mimeData().urls()]
        self.add_images_to_queue(files)
    
    def import_images(self):
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "选择图片",
            "",
            "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.tiff)"
        )
        
        if files:
            self.add_images_to_queue(files)
    
    def add_images_to_queue(self, files):
        for file_path in files:
            # 检查是否是支持的图片格式
            _, ext = os.path.splitext(file_path)
            if ext.lower() in [".jpg", ".jpeg", ".png", ".bmp", ".gif", ".tiff"]:
                # 检查是否已经在队列中
                if file_path not in self.image_paths:
                    self.image_paths.append(file_path)
                    self.task_list.addItem(os.path.basename(file_path))
    
    def select_output_dir(self):
        dir_path = QFileDialog.getExistingDirectory(
            self,
            "选择输出文件夹",
            ""
        )
        
        if dir_path:
            self.output_dir = dir_path
            self.output_path_input.setText(dir_path)
            self.output_label.setText(f"输出到: {dir_path}")
    
    def on_output_path_changed(self, text):
        self.output_dir = text
    
    def show_context_menu(self, position):
        context_menu = QMenu()
        clear_action = QAction("清空队列", self)
        clear_action.triggered.connect(self.clear_queue)
        context_menu.addAction(clear_action)
        
        remove_action = QAction("移除选中项", self)
        remove_action.triggered.connect(self.remove_selected)
        context_menu.addAction(remove_action)
        
        context_menu.exec_(self.task_list.mapToGlobal(position))
    
    def clear_queue(self):
        self.image_paths = []
        self.task_list.clear()
    
    def remove_selected(self):
        selected_items = self.task_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            row = self.task_list.row(item)
            self.task_list.takeItem(row)
            del self.image_paths[row]
    
    def execute_tasks(self):
        if not self.image_paths:
            QMessageBox.warning(self, "警告", "任务队列为空！")
            return
            
        if not self.output_dir:
            QMessageBox.warning(self, "警告", "请先选择输出文件夹！")
            return
        
        # 禁用按钮，防止重复执行
        self.execute_btn.setEnabled(False)
        self.import_btn.setEnabled(False)
        self.output_btn.setEnabled(False)
        
        # 创建并启动处理线程
        self.processor = ImageProcessor(
            self.image_paths,
            self.output_dir,
            self.keep_name_cb.isChecked()
        )
        
        # 连接信号
        self.processor.progress_updated.connect(self.update_progress)
        self.processor.task_completed.connect(self.update_task_status)
        self.processor.all_tasks_completed.connect(self.on_all_tasks_completed)
        
        # 启动线程
        self.processor.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_task_status(self, message):
        self.statusBar().showMessage(message, 3000)  # 显示3秒
    
    def on_all_tasks_completed(self):
        # 重新启用按钮
        self.execute_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        
        # 显示完成消息
        QMessageBox.information(self, "完成", "所有任务已完成！")
        
        # 重置进度条
        self.progress_bar.setValue(0)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序图标（桌面图标和窗口图标）
    set_application_icon(app, "logo.ico")
    
    window = MainWindow()
    # 确保窗口也使用相同的图标
    window.setWindowIcon(QIcon(get_icon_path("logo.ico")))
    window.show()
    sys.exit(app.exec_())