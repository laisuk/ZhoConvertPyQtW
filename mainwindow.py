# This Python file uses the following encoding: utf-8
import os
import re
import sys

from PySide6.QtCore import Qt, SIGNAL, QObject
from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtWidgets import QFileDialog, QMessageBox
from opencc import OpenCC  # pip install opencc-python-reimplemented

# Important:
# You need to run the following command to generate the ui_form.py file
#     pyside6-uic form.ui -o ui_form.py, or
#     pyside2-uic form.ui -o ui_form.py
from ui_form import Ui_MainWindow


class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)

        self.ui.tabWidget.setCurrentIndex(0)
        self.ui.btnCopy.clicked.connect(self.btn_copy_click)
        self.ui.btnPaste.clicked.connect(self.btn_paste_click)
        self.ui.btnOpenFile.clicked.connect(self.btn_openfile_click)
        self.ui.btnSaveAs.clicked.connect(self.btn_savefile_click)
        self.ui.btnProcess.clicked.connect(self.btn_process_click)
        self.ui.btnExit.clicked.connect(btn_exit_click)
        self.ui.btnClearTbSource.clicked.connect(self.btn_clear_tb_source_clicked)
        self.ui.btnClearTbDestination.clicked.connect(self.btn_clear_tb_destination_clicked)
        QObject.connect(self.ui.tbSource, SIGNAL("textChanged()"), self.update_char_count)
        QObject.connect(self.ui.rbStd, SIGNAL("clicked()"), self.std_hk_select)
        QObject.connect(self.ui.rbHK, SIGNAL("clicked()"), self.std_hk_select)
        QObject.connect(self.ui.rbZhTw, SIGNAL("clicked()"), self.zhtw_select)
        QObject.connect(self.ui.tbSource, SIGNAL("clicked()"), self.zhtw_select)
        QObject.connect(self.ui.btnDetect, SIGNAL("clicked()"), self.detect_source_text_info)
        QObject.connect(self.ui.tabWidget, SIGNAL("currentChanged(int)"), self.tab_bar_changed)
        QObject.connect(self.ui.cbZhTw, SIGNAL("clicked(bool)"), self.cbzhtw_clicked)
        self.ui.btnAdd.clicked.connect(self.btn_add_clicked)
        self.ui.btnRemove.clicked.connect(self.btn_remove_clicked)
        self.ui.btnClear.clicked.connect(self.btn_clear_clicked)
        self.ui.btnPreview.clicked.connect(self.btn_preview_clicked)
        self.ui.btnPreviewClear.clicked.connect(self.btn_preview_clear_clicked)
        self.ui.btnOutDir.clicked.connect(self.btn_out_directory_clicked)
        # self.ui.tabWidget.currentChanged.connect(self.tab_bar_changed)
        self.ui.actionAbout.triggered.connect(self.action_about_triggered)
        self.ui.actionExit.triggered.connect(btn_exit_click)

    def action_about_triggered(self):
        QMessageBox.about(self, "About", "Zho Converter version 1.0 (c) 2024 Bryan Lai")

    def tab_bar_changed(self, index: int) -> None:
        match index:
            case 0:
                self.ui.btnOpenFile.setEnabled(True)
                self.ui.lblFilename.setEnabled(True)
                self.ui.btnSaveAs.setEnabled(True)
            case 1:
                self.ui.btnOpenFile.setEnabled(False)
                self.ui.lblFilename.setEnabled(False)
                self.ui.btnSaveAs.setEnabled(False)

    def update_char_count(self):
        self.ui.lblCharCount.setText(f"[ {len(self.ui.tbSource.document().toPlainText()):,} chars ]")

    def detect_source_text_info(self):
        text = self.ui.tbSource.toPlainText()
        if text:
            strip_text = re.sub(r'[\WA-Za-z0-9_]', "", text)
            test_text = strip_text if len(strip_text) < 50 else strip_text[0:50]
            self.update_source_code(check_text_code(test_text))
            self.ui.lblFilename.setText(os.path.basename(self.ui.tbSource.content_filename))
        if self.ui.tbSource.content_filename:
            self.statusBar().showMessage(f"File: {self.ui.tbSource.content_filename}")

    def std_hk_select(self):
        self.ui.cbZhTw.setCheckState(Qt.CheckState.Unchecked)

    def zhtw_select(self):
        self.ui.cbZhTw.setCheckState(Qt.CheckState.Checked)

    def cbzhtw_clicked(self, status: bool) -> None:
        if status:
            self.ui.rbZhTw.setChecked(True)

    def btn_paste_click(self):
        if not QApplication.clipboard().text():
            return
        self.ui.tbSource.clear()
        self.ui.tbSource.paste()
        self.ui.tbSource.content_filename = ""
        self.detect_source_text_info()
        self.ui.statusbar.showMessage("Clipboard contents pasted to source box")

    def btn_copy_click(self):
        text = self.ui.tbDestination.toPlainText()
        if not text:
            return None
        QApplication.clipboard().setText(text)
        self.ui.statusbar.showMessage("Contents copied to clipboard")

    def btn_openfile_click(self):
        filename = QFileDialog.getOpenFileName(
            self,
            "Open Text File",
            ".",
            "Text Files (*.txt);;"
            "Subtitle Files (*.srt *.vtt *.ass *.ttml2 *.xml));;"
            "XML Files (*.xml *.ttml2);;"
            "All Files (*.*)")
        if not filename[0]:
            return

        with open(filename[0], "r", encoding="utf-8") as f:
            contents = f.read()

        self.ui.tbSource.document().setPlainText(contents)
        self.ui.tbSource.content_filename = filename[0]
        self.detect_source_text_info()
        self.ui.statusbar.showMessage(f"File: {filename[0]}")

    def btn_process_click(self):
        config = "s2tw"
        self.ui.tbDestination.clear()
        if self.ui.rbS2t.isChecked():
            if self.ui.rbHK.isChecked():
                config = "s2hk"
            elif self.ui.rbStd.isChecked():
                config = "s2t"
            else:
                config = "s2twp" if self.ui.cbZhTw.isChecked() else "s2tw"
        elif self.ui.rbT2s.isChecked():
            if self.ui.rbHK.isChecked():
                config = "hk2s"
            elif self.ui.rbStd.isChecked():
                config = "t2s"
            else:
                config = "tw2sp" if self.ui.cbZhTw.isChecked() else "tw2s"

        converter = OpenCC(config)

        if self.ui.tabWidget.currentIndex() == 0:
            if not self.ui.tbSource.document().toPlainText():
                self.ui.statusbar.showMessage("Nothing to convert: Empty content.")
                return
            input_text = self.ui.tbSource.document().toPlainText()
            converted_text = converter.convert(input_text)
            if self.ui.cbPunct.isChecked():
                output_text = convert_punctuation(converted_text, config)
            else:
                output_text = converted_text
            self.ui.tbDestination.document().setPlainText(output_text)
            if "Non" not in self.ui.lblSourceCode.text():
                self.ui.lblDestinationCode.setText("zh-Hant (繁体)" if self.ui.rbS2t.isChecked() else "zh-Hans (簡體)")
            else:
                self.ui.lblDestinationCode.setText(self.ui.lblSourceCode.text())
            self.ui.statusbar.showMessage("Process completed")

        if self.ui.tabWidget.currentIndex() == 1:
            if self.ui.listSource.count() == 0:
                self.ui.statusbar.showMessage("Nothing to convert: Empty file list.")
                return

            out_dir = self.ui.lineEditDir.text()
            if not os.path.exists(out_dir):
                msg = QMessageBox()
                msg.setWindowTitle("Attention")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText("Invalid output directory.")
                msg.setInformativeText("Output directory: " + out_dir + " not found.")
                msg.setDetailedText("Please set the required output directory.")
                msg.exec()
                self.ui.statusbar.showMessage("Invalid output directory.")
            else:
                self.ui.tbPreview.clear()
                for index in range(self.ui.listSource.count()):
                    file_path: str = self.ui.listSource.item(index).text()
                    if os.path.exists(file_path):
                        try:
                            with open(file_path, "r", encoding="utf-8") as f:
                                input_text = f.read()
                        except UnicodeDecodeError:
                            input_text = ""

                        if input_text:
                            converted_text = converter.convert(input_text)
                            if self.ui.cbPunct.isChecked():
                                output_text = convert_punctuation(converted_text, config)
                            else:
                                output_text = converted_text
                            output_filename = self.ui.lineEditDir.text() + "/" + os.path.basename(file_path)
                            with open(output_filename, "w", encoding="utf-8") as f:
                                f.write(output_text)
                            self.ui.tbPreview.appendPlainText(f"{index + 1}: {output_filename} --> Done.")
                        else:
                            self.ui.tbPreview.appendPlainText(f"{index + 1}: {file_path} --> Skip: Not text file.")
                    else:
                        self.ui.tbPreview.appendPlainText(f"{index + 1}: {file_path} --> File not found.")
                self.ui.statusbar.showMessage("Process completed")

    def update_source_code(self, text_code):
        match text_code:
            case 1:
                self.ui.lblSourceCode.setText("zh-Hant (繁體)")
                self.ui.rbT2s.setChecked(True)
            case 2:
                self.ui.lblSourceCode.setText("zh-Hans (簡體)")
                self.ui.rbS2t.setChecked(True)
            case _:
                self.ui.lblSourceCode.setText("Non-zh (其它)")

    def btn_savefile_click(self):
        filename = QFileDialog.getSaveFileName(
            self,
            "Save Text File",
            "./File.txt",
            "Text File (*.txt);;All Files (*.*)")

        if not filename[0]:
            return

        with open(filename[0], "w", encoding="utf-8") as f:
            f.write(self.ui.tbDestination.toPlainText())
        self.ui.statusbar.showMessage(f"File saved to {filename[0]}")

    def btn_add_clicked(self):
        # options = QFileDialog.Option()
        # options |= QFileDialog.DontUseNativeDialog
        file_dialog = QFileDialog(self)
        # file_dialog.setFileMode(QFileDialog.ExistingFiles)
        files, _ = file_dialog.getOpenFileNames(self, "Open Files", "", "All Files (*)")

        if files:
            self.display_file_list(files)
            self.ui.statusbar.showMessage("File(s) added.")

    def display_file_list(self, files):
        for file in files:
            # Check if the file path is not already in the list box
            if not self.file_path_exists(file):
                self.ui.listSource.addItem(file)

    def file_path_exists(self, file_path):
        # Check if the file path is already in the list box
        for index in range(self.ui.listSource.count()):
            item = self.ui.listSource.item(index)
            if item.text() == file_path:
                return True
        return False

    def btn_remove_clicked(self):
        selected_items = self.ui.listSource.selectedItems()
        if selected_items:
            for selected_item in selected_items:
                self.ui.listSource.takeItem(self.ui.listSource.row(selected_item))
            self.ui.statusbar.showMessage("File(s) removed.")

    def btn_clear_clicked(self):
        self.ui.listSource.clear()
        self.ui.statusbar.showMessage("File list cleared.")

    def btn_preview_clicked(self):
        selected_items = self.ui.listSource.selectedItems()
        if selected_items:
            selected_item = selected_items[0]
            file_path = selected_item.text()
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    contents = f.read()
            except UnicodeDecodeError:
                contents = ""
                self.ui.statusbar.showMessage(f"{file_path}: Not a valid text file.")
            self.ui.tbPreview.setPlainText(contents)

    def btn_out_directory_clicked(self):
        file_dialog = QFileDialog(self)
        directory = file_dialog.getExistingDirectory(self, "")
        if directory:
            self.ui.lineEditDir.setText(directory)
            self.ui.statusbar.showMessage(f"Output directory set: {directory}")

    def btn_preview_clear_clicked(self):
        self.ui.tbPreview.clear()
        self.ui.statusbar.showMessage("File preview cleared.")

    def btn_clear_tb_source_clicked(self):
        self.ui.tbSource.clear()

    def btn_clear_tb_destination_clicked(self):
        self.ui.tbDestination.clear()


def btn_exit_click():
    exit()


def check_text_code(text):
    converted_text = OpenCC("t2s").convert(text)
    if converted_text != text:
        return 1
    elif OpenCC("s2t").convert(converted_text) != text:
        return 2
    else:
        return 0


def convert_punctuation(input_text, config):
    # Declare a dictionary to store the characters and their mappings
    s2t_punctuation_chars = {
        '“': '「',
        '”': '」',
        '‘': '『',
        '’': '』'
    }
    # Use the join method to create the regular expression patterns
    if config[0] == "s":
        pattern = f"[{''.join(s2t_punctuation_chars.keys())}]"  # "[“”‘’]"
        output_text = re.sub(
            pattern, lambda m: s2t_punctuation_chars[m.group(0)], input_text)
    else:
        # Use the dict comprehension to reverse the dictionary
        t2s_punctuation_chars = {v: k for k, v in s2t_punctuation_chars.items()}
        pattern = f"[{''.join(t2s_punctuation_chars.keys())}]"  # "[「」『』]"
        output_text = re.sub(
            pattern, lambda m: t2s_punctuation_chars[m.group(0)], input_text)

    return output_text


if __name__ == "__main__":
    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    sys.exit(app.exec())
