from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .settings import AppSettings, ThemeName


def stylesheet_for_theme(theme_name: ThemeName) -> str:
    if theme_name == "light":
        return """
        QDialog {
            background-color: #f8fafc;
            color: #0f172a;
        }
        QLabel {
            color: #0f172a;
        }
        QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
            background-color: #ffffff;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 6px 8px;
        }
        QAbstractItemView {
            background-color: #ffffff;
            color: #0f172a;
            selection-background-color: #dbeafe;
            selection-color: #0f172a;
            border: 1px solid #cbd5e1;
        }
        QPushButton {
            background-color: #e2e8f0;
            color: #0f172a;
            border: 1px solid #cbd5e1;
            border-radius: 8px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #dbeafe;
        }
        """

    return """
    QDialog {
        background-color: #0f172a;
        color: #e2e8f0;
    }
    QLabel {
        color: #e2e8f0;
    }
    QComboBox, QSpinBox, QDoubleSpinBox, QLineEdit {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 6px 8px;
    }
    QAbstractItemView {
        background-color: #1e293b;
        color: #f8fafc;
        selection-background-color: #334155;
        selection-color: #f8fafc;
        border: 1px solid #334155;
    }
    QPushButton {
        background-color: #1e293b;
        color: #f8fafc;
        border: 1px solid #334155;
        border-radius: 8px;
        padding: 6px 12px;
    }
    QPushButton:hover {
        background-color: #334155;
    }
    """


class AppSettingsDialog(QDialog):
    save_requested = Signal(object)
    test_requested = Signal(object)

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("ダーク", "dark")
        self.theme_combo.addItem("ライト", "light")

        self.sound_combo = QComboBox(self)
        self.sound_combo.addItem("標準", "gentle")
        self.sound_combo.addItem("太鼓", "taiko")
        self.sound_combo.addItem("斬撃", "zangeki")
        self.sound_combo.addItem("無音", "off")

        self.port_spin = QSpinBox(self)
        self.port_spin.setRange(1, 65535)

        self.host_edit = QLineEdit(self)
        self.host_edit.setPlaceholderText("127.0.0.1")

        self.duration_spin = QDoubleSpinBox(self)
        self.duration_spin.setRange(0.5, 60.0)
        self.duration_spin.setDecimals(1)
        self.duration_spin.setSingleStep(0.5)
        self.duration_spin.setSuffix(" 秒")

        self.max_visible_spin = QSpinBox(self)
        self.max_visible_spin.setRange(1, 10)

        self.note_label = QLabel(
            "待受ホストとポート番号の変更はアプリ再起動後に反映されます。",
            self,
        )
        self.note_label.setWordWrap(True)

        self.test_button = QPushButton("テスト通知", self)
        self.save_button = QPushButton("保存", self)
        self.cancel_button = QPushButton("キャンセル", self)

        self._build_ui()
        self.set_settings(settings)
        self._connect_signals()

    def set_settings(self, settings: AppSettings) -> None:
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(settings.theme))
        self.sound_combo.setCurrentIndex(self.sound_combo.findData(settings.sound_type))
        self.host_edit.setText(settings.bind_host)
        self.port_spin.setValue(settings.port)
        self.duration_spin.setValue(settings.duration_seconds)
        self.max_visible_spin.setValue(settings.max_visible)
        self.apply_theme(settings.theme)

    def settings_from_form(self) -> AppSettings:
        theme = self.theme_combo.currentData()
        sound_type = self.sound_combo.currentData()
        return AppSettings(
            theme=theme,
            sound_type=sound_type,
            bind_host=self.host_edit.text().strip() or "127.0.0.1",
            port=self.port_spin.value(),
            duration_seconds=self.duration_spin.value(),
            max_visible=self.max_visible_spin.value(),
        )

    def show_error(self, message: str) -> None:
        QMessageBox.critical(self, "設定", message)

    def apply_theme(self, theme_name: ThemeName) -> None:
        self.setStyleSheet(stylesheet_for_theme(theme_name))

    def _build_ui(self) -> None:
        form_layout = QFormLayout()
        form_layout.addRow("テーマ", self.theme_combo)
        form_layout.addRow("サウンド", self.sound_combo)
        form_layout.addRow("待受ホスト", self.host_edit)
        form_layout.addRow("ポート", self.port_spin)
        form_layout.addRow("表示時間", self.duration_spin)
        form_layout.addRow("スタック数", self.max_visible_spin)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.test_button)
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(form_layout)
        root_layout.addWidget(self.note_label)
        root_layout.addLayout(button_layout)

    def _connect_signals(self) -> None:
        self.theme_combo.currentIndexChanged.connect(self._sync_theme_preview)
        self.test_button.clicked.connect(self._emit_test_requested)
        self.save_button.clicked.connect(self._emit_save_requested)
        self.cancel_button.clicked.connect(self.reject)

    def _sync_theme_preview(self) -> None:
        self.apply_theme(self.theme_combo.currentData())

    def _emit_test_requested(self) -> None:
        self.test_requested.emit(self.settings_from_form())

    def _emit_save_requested(self) -> None:
        self.save_requested.emit(self.settings_from_form())
