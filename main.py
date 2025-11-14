import sys
import os
import struct
import zlib
from PyQt5.QtWidgets import (QApplication, QMainWindow, QPushButton, QFileDialog, 
                             QVBoxLayout, QHBoxLayout, QWidget, QListWidget, QCheckBox,
                             QLabel, QMenu, QAction, QMessageBox, QProgressBar, QFrame, QLineEdit,
                             QDialog, QTextEdit, QScrollArea, QGroupBox, QGridLayout, QSizePolicy)
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
    all_tasks_completed = pyqtSignal(dict)  # 传递处理统计结果
    
    def __init__(self, image_paths, output_dir, keep_original_name):
        super().__init__()
        self.image_paths = image_paths
        self.output_dir = output_dir
        self.keep_original_name = keep_original_name
        self.is_running = True
        
        # 初始化PNG块处理器
        self.png_processor = PNGBlockProcessor()
        
        # 初始化统计变量
        self.processed_files = []  # 成功处理的文件列表
        self.failed_files = []     # 处理失败的文件列表
    
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
                
                # 使用新的PNG流式算法处理PNG文件
                if self.png_processor.is_png_file(image_path):
                    # 使用高效的块处理算法
                    success = self.png_processor.process_png_streaming(image_path, output_path)
                    if not success:
                        raise Exception("PNG块处理失败")
                else:
                    # 对于非PNG文件，仍然使用原来的PIL方法
                    self._process_non_png_image(image_path, output_path, filename)
                
                # 记录成功处理的文件
                self.processed_files.append(filename)
                self.task_completed.emit(f"已处理: {filename}")
            except Exception as e:
                # 记录处理失败的文件
                self.failed_files.append(filename)
                self.task_completed.emit(f"处理失败: {filename} - {str(e)}")
            
            # 更新进度
            progress = int((i + 1) / total * 100)
            self.progress_updated.emit(progress)
        
        # 准备统计结果
        stats = {
            'total_files': total,
            'successful': len(self.processed_files),
            'failed': len(self.failed_files),
            'processed_files': self.processed_files.copy(),
            'failed_files': self.failed_files.copy()
        }
        
        # 发送完成信号并传递统计数据
        self.all_tasks_completed.emit(stats)
    
    def _process_non_png_image(self, image_path: str, output_path: str, filename: str):
        """处理非PNG格式的图像文件（使用原有的PIL方法）"""
        try:
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
        except Exception as e:
            raise Exception(f"非PNG图像处理失败: {str(e)}")
    
    def stop(self):
        self.is_running = False


# 处理结果统计对话框
class ProcessingResultsDialog(QDialog):
    """处理结果统计对话框"""
    
    def __init__(self, parent, stats):
        super().__init__(parent)
        self.stats = stats
        self.init_ui()
    
    def init_ui(self):
        self.setWindowTitle("处理结果统计")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        
        # 创建布局
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("📊 处理结果统计")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 统计概览
        overview_group = QGroupBox("📈 统计概览")
        overview_layout = QGridLayout()
        
        # 总文件数
        overview_layout.addWidget(QLabel("总文件数:"), 0, 0)
        total_label = QLabel(str(self.stats['total_files']))
        total_label.setStyleSheet("font-weight: bold; color: blue;")
        overview_layout.addWidget(total_label, 0, 1)
        
        # 成功处理数
        overview_layout.addWidget(QLabel("成功处理:"), 1, 0)
        success_label = QLabel(str(self.stats['successful']))
        success_label.setStyleSheet("font-weight: bold; color: green;")
        overview_layout.addWidget(success_label, 1, 1)
        
        # 失败数
        overview_layout.addWidget(QLabel("处理失败:"), 2, 0)
        failed_label = QLabel(str(self.stats['failed']))
        failed_label.setStyleSheet("font-weight: bold; color: red;")
        overview_layout.addWidget(failed_label, 2, 1)
        
        # 成功率
        if self.stats['total_files'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_files']) * 100
            overview_layout.addWidget(QLabel("成功率:"), 3, 0)
            rate_label = QLabel(f"{success_rate:.1f}%")
            rate_label.setStyleSheet("font-weight: bold; color: purple;")
            overview_layout.addWidget(rate_label, 3, 1)
        
        overview_group.setLayout(overview_layout)
        layout.addWidget(overview_group)
        
        # 成功文件列表
        if self.stats['processed_files']:
            success_group = QGroupBox(f"✅ 成功处理的文件 ({len(self.stats['processed_files'])})")
            success_layout = QVBoxLayout()
            
            # 使用滚动区域来显示成功文件列表
            success_scroll = QScrollArea()
            success_scroll.setWidgetResizable(True)
            success_scroll.setMaximumHeight(200)  # 增加高度限制
            
            success_text = QTextEdit()
            success_text.setReadOnly(True)
            success_text.setWordWrapMode(True)  # 启用文本换行
            success_text.setPlainText('\n'.join(self.stats['processed_files']))
            success_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8f9fa;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Courier New', monospace;
                    font-size: 9pt;
                }
            """)
            
            success_scroll.setWidget(success_text)
            success_layout.addWidget(success_scroll)
            
            success_group.setLayout(success_layout)
            layout.addWidget(success_group)
        
        # 失败文件列表
        if self.stats['failed_files']:
            failed_group = QGroupBox(f"❌ 处理失败的文件 ({len(self.stats['failed_files'])})")
            failed_layout = QVBoxLayout()
            
            # 使用滚动区域来显示失败文件列表
            failed_scroll = QScrollArea()
            failed_scroll.setWidgetResizable(True)
            failed_scroll.setMaximumHeight(200)  # 增加高度限制
            
            failed_text = QTextEdit()
            failed_text.setReadOnly(True)
            failed_text.setWordWrapMode(True)  # 启用文本换行
            failed_text.setPlainText('\n'.join(self.stats['failed_files']))
            failed_text.setStyleSheet("""
                QTextEdit {
                    background-color: #fff5f5;
                    border: 1px solid #fed7d7;
                    border-radius: 4px;
                    padding: 8px;
                    font-family: 'Courier New', monospace;
                    font-size: 9pt;
                }
            """)
            
            failed_scroll.setWidget(failed_text)
            failed_layout.addWidget(failed_scroll)
            
            failed_group.setLayout(failed_layout)
            layout.addWidget(failed_group)
        
        # 按钮
        button_layout = QHBoxLayout()
        
        ok_btn = QPushButton("确定")
        ok_btn.clicked.connect(self.accept)
        ok_btn.setDefault(True)
        button_layout.addWidget(ok_btn)
        
        # 复制按钮
        copy_btn = QPushButton("复制结果")
        copy_btn.clicked.connect(self.copy_results)
        button_layout.addWidget(copy_btn)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def copy_results(self):
        """复制统计结果到剪贴板"""
        result_text = f"处理结果统计\n"
        result_text += f"==================\n"
        result_text += f"总文件数: {self.stats['total_files']}\n"
        result_text += f"成功处理: {self.stats['successful']}\n"
        result_text += f"处理失败: {self.stats['failed']}\n"
        
        if self.stats['total_files'] > 0:
            success_rate = (self.stats['successful'] / self.stats['total_files']) * 100
            result_text += f"成功率: {success_rate:.1f}%\n"
        
        if self.stats['processed_files']:
            result_text += f"\n成功处理的文件:\n"
            for file in self.stats['processed_files']:
                result_text += f"  ✓ {file}\n"
        
        if self.stats['failed_files']:
            result_text += f"\n处理失败的文件:\n"
            for file in self.stats['failed_files']:
                result_text += f"  ✗ {file}\n"
        
        # 复制到剪贴板
        clipboard = QApplication.clipboard()
        clipboard.setText(result_text)
        
        QMessageBox.information(self, "已复制", "统计结果已复制到剪贴板！")


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
    
    def on_all_tasks_completed(self, stats):
        # 重新启用按钮
        self.execute_btn.setEnabled(True)
        self.import_btn.setEnabled(True)
        self.output_btn.setEnabled(True)
        
        # 显示统计结果对话框
        results_dialog = ProcessingResultsDialog(self, stats)
        results_dialog.exec_()
        
        # 重置进度条
        self.progress_bar.setValue(0)


# PNG块处理器 - 基于流的元数据去除算法
class PNGBlockProcessor:
    """高效PNG元数据去除器 - 基于块的流式处理算法"""
    
    # PNG文件签名 (8字节)
    PNG_SIGNATURE = b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A'
    
    # 关键块 (Critical Chunks) - 必须保留
    CRITICAL_CHUNKS = {'IHDR', 'PLTE', 'IDAT', 'IEND'}
    
    # 安全辅助块白名单 - 对图像显示重要但不包含工作流
    SAFE_ANCILLARY_CHUNKS = {
        'sRGB',   # sRGB颜色空间
        'gAMA',   # Gamma校正
        'iCCP',   # ICC颜色配置文件
        'pHYs',   # 物理像素尺寸
        'cHRM',   # 色度信息
        'bKGD',   # 背景色
        'hIST',   # 直方图
        'tRNS',   # 透明度信息
    }
    
    # 需要丢弃的块类型（包含工作流元数据）
    METADATA_CHUNKS = {
        'tEXt', 'zTXt', 'iTXt',  # 文本元数据
        'eXIf',                   # EXIF数据
        'tIME',                   # 最后修改时间
    }
    
    def __init__(self):
        pass
    
    def process_png_streaming(self, input_path: str, output_path: str) -> bool:
        """
        流式处理PNG文件 - 只重组文件结构，完全不碰图像数据
        
        Args:
            input_path: 输入PNG文件路径
            output_path: 输出PNG文件路径
            
        Returns:
            bool: 处理是否成功
        """
        try:
            with open(input_path, 'rb') as input_file, \
                 open(output_path, 'wb') as output_file:
                
                # 1. 验证并写入PNG签名
                signature = input_file.read(8)
                if signature != self.PNG_SIGNATURE:
                    raise ValueError("不是有效的PNG文件")
                output_file.write(signature)
                
                # 2. 流式处理所有数据块
                chunks_processed = 0
                chunks_skipped = 0
                
                while True:
                    # 读取块头信息 (8字节: 长度4字节 + 类型4字节)
                    chunk_header = input_file.read(8)
                    if len(chunk_header) != 8:
                        break
                    
                    chunk_length, chunk_type = struct.unpack('>I4s', chunk_header)
                    
                    # 读取块数据
                    chunk_data = input_file.read(chunk_length)
                    if len(chunk_data) != chunk_length:
                        raise ValueError(f"块数据不完整: {chunk_type}")
                    
                    # 读取CRC校验
                    chunk_crc = input_file.read(4)
                    if len(chunk_crc) != 4:
                        raise ValueError(f"CRC校验不完整: {chunk_type}")
                    
                    # 3. 决策逻辑：保留或丢弃块
                    chunk_type_str = chunk_type.decode('ascii')
                    
                    # 关键块必须保留
                    is_critical = chunk_type_str in self.CRITICAL_CHUNKS
                    
                    # 安全辅助块可以保留
                    is_safe_ancillary = chunk_type_str in self.SAFE_ANCILLARY_CHUNKS
                    
                    # 需要丢弃的元数据块
                    is_metadata = chunk_type_str in self.METADATA_CHUNKS
                    
                    # 4. 写入决策
                    if is_critical or is_safe_ancillary:
                        # 这是"好"块，原封不动写回
                        output_file.write(chunk_header)
                        output_file.write(chunk_data)
                        output_file.write(chunk_crc)
                        chunks_processed += 1
                    elif is_metadata:
                        # 这是"坏"块（包含工作流），直接跳过
                        chunks_skipped += 1
                    else:
                        # 未知的辅助块，默认保留以确保兼容性
                        output_file.write(chunk_header)
                        output_file.write(chunk_data)
                        output_file.write(chunk_crc)
                        chunks_processed += 1
                        print(f"警告: 保留未知类型的块: {chunk_type_str}")
                    
                    # 5. 检查是否到达文件末尾
                    if chunk_type_str == 'IEND':
                        break
                
                print(f"处理完成: 保留{chunks_processed}个块，跳过{chunks_skipped}个元数据块")
                return True
                
        except Exception as e:
            print(f"PNG处理失败: {str(e)}")
            return False
    
    def is_png_file(self, file_path: str) -> bool:
        """检查文件是否为PNG格式"""
        try:
            with open(file_path, 'rb') as f:
                signature = f.read(8)
                return signature == self.PNG_SIGNATURE
        except:
            return False
    
    def get_file_info(self, file_path: str) -> dict:
        """获取PNG文件的基本信息"""
        try:
            with open(file_path, 'rb') as f:
                # 跳过PNG签名
                f.seek(8)
                
                # 读取IHDR块
                chunk_header = f.read(8)
                if len(chunk_header) != 8:
                    return {}
                
                chunk_length, chunk_type = struct.unpack('>I4s', chunk_header)
                
                if chunk_type.decode('ascii') != 'IHDR':
                    return {}
                
                # IHDR块长度固定为13字节
                ihdr_data = f.read(13)
                if len(ihdr_data) != 13:
                    return {}
                
                # 解析IHDR数据
                width, height, bit_depth, color_type, compression_method, \
                filter_method, interlace_method = struct.unpack('>IIBBBBB', ihdr_data)
                
                return {
                    'width': width,
                    'height': height,
                    'bit_depth': bit_depth,
                    'color_type': color_type,
                    'is_png': True
                }
        except Exception as e:
            print(f"获取文件信息失败: {str(e)}")
            return {'is_png': False}


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # 设置应用程序图标（桌面图标和窗口图标）
    set_application_icon(app, "logo.ico")
    
    window = MainWindow()
    # 确保窗口也使用相同的图标
    window.setWindowIcon(QIcon(get_icon_path("logo.ico")))
    window.show()
    sys.exit(app.exec_())