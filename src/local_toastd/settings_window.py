from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .notification_types import NOTIFICATION_TYPES, NotificationType, display_label_for_type
from .settings import (
    MAX_FONT_SIZE,
    MAX_MAX_VISIBLE,
    MIN_FONT_SIZE,
    MIN_MAX_VISIBLE,
    AppSettings,
    NotificationSoundSettings,
    ThemeName,
)


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
        QGroupBox {
            margin-top: 12px;
            padding: 14px 12px 12px 12px;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            font-weight: 600;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #334155;
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
    QGroupBox {
        margin-top: 12px;
        padding: 14px 12px 12px 12px;
        border: 1px solid #334155;
        border-radius: 12px;
        font-weight: 600;
    }
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 12px;
        padding: 0 6px;
        color: #cbd5e1;
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
    test_requested = Signal(object, str)

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("設定")
        self.setModal(False)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        self.theme_combo = QComboBox(self)
        self.theme_combo.addItem("ダーク", "dark")
        self.theme_combo.addItem("ライト", "light")

        self.sound_combos: dict[NotificationType, QComboBox] = {
            notification_type: self._create_sound_combo()
            for notification_type in NOTIFICATION_TYPES
        }

        self.position_combo = QComboBox(self)
        self.position_combo.addItem("右上", "top_right")
        self.position_combo.addItem("中央上", "top_center")
        self.position_combo.addItem("右下", "bottom_right")

        self.font_size_spin = QSpinBox(self)
        self.font_size_spin.setRange(MIN_FONT_SIZE, MAX_FONT_SIZE)
        self.font_size_spin.setSuffix(" px")

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
        self.max_visible_spin.setRange(MIN_MAX_VISIBLE, MAX_MAX_VISIBLE)

        self.note_label = QLabel(
            "待受ホストとポート番号の変更はアプリ再起動後に反映されます。",
            self,
        )
        self.note_label.setWordWrap(True)

        self.test_buttons: dict[NotificationType, QPushButton] = {
            notification_type: QPushButton(
                f"{display_label_for_type(notification_type)}をテスト",
                self,
            )
            for notification_type in NOTIFICATION_TYPES
        }
        self.save_button = QPushButton("保存", self)
        self.cancel_button = QPushButton("キャンセル", self)

        self._build_ui()
        self.set_settings(settings)
        self._connect_signals()

    def set_settings(self, settings: AppSettings) -> None:
        self.theme_combo.setCurrentIndex(self.theme_combo.findData(settings.theme))
        self.sound_combos["type_a"].setCurrentIndex(
            self.sound_combos["type_a"].findData(settings.notification_sounds.type_a)
        )
        self.sound_combos["type_b"].setCurrentIndex(
            self.sound_combos["type_b"].findData(settings.notification_sounds.type_b)
        )
        self.sound_combos["type_c"].setCurrentIndex(
            self.sound_combos["type_c"].findData(settings.notification_sounds.type_c)
        )
        self.sound_combos["type_d"].setCurrentIndex(
            self.sound_combos["type_d"].findData(settings.notification_sounds.type_d)
        )
        self.position_combo.setCurrentIndex(self.position_combo.findData(settings.position))
        self.font_size_spin.setValue(settings.font_size)
        self.host_edit.setText(settings.bind_host)
        self.port_spin.setValue(settings.port)
        self.duration_spin.setValue(settings.duration_seconds)
        self.max_visible_spin.setValue(settings.max_visible)
        self.apply_theme(settings.theme)

    def settings_from_form(self) -> AppSettings:
        theme = self.theme_combo.currentData()
        return AppSettings(
            theme=theme,
            notification_sounds=NotificationSoundSettings(
                type_a=self.sound_combos["type_a"].currentData(),
                type_b=self.sound_combos["type_b"].currentData(),
                type_c=self.sound_combos["type_c"].currentData(),
                type_d=self.sound_combos["type_d"].currentData(),
            ),
            position=self.position_combo.currentData(),
            font_size=self.font_size_spin.value(),
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
        notification_group = QGroupBox("通知", self)
        notification_form = QFormLayout(notification_group)
        notification_form.addRow("テーマ", self.theme_combo)
        notification_form.addRow("表示時間", self.duration_spin)
        notification_form.addRow("スタック数", self.max_visible_spin)

        sound_group = QGroupBox("通知音", self)
        sound_form = QFormLayout(sound_group)
        for notification_type in NOTIFICATION_TYPES:
            sound_form.addRow(
                display_label_for_type(notification_type),
                self._build_sound_row(notification_type),
            )

        appearance_group = QGroupBox("表示", self)
        appearance_form = QFormLayout(appearance_group)
        appearance_form.addRow("表示位置", self.position_combo)
        appearance_form.addRow("文字サイズ", self.font_size_spin)

        server_group = QGroupBox("サーバー", self)
        server_layout = QVBoxLayout(server_group)
        server_form = QFormLayout()
        server_form.addRow("待受ホスト", self.host_edit)
        server_form.addRow("ポート", self.port_spin)
        server_layout.addLayout(server_form)
        server_layout.addWidget(self.note_label)

        button_layout = QHBoxLayout()
        button_layout.addStretch(1)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.cancel_button)

        root_layout = QVBoxLayout(self)
        root_layout.addWidget(notification_group)
        root_layout.addWidget(sound_group)
        root_layout.addWidget(appearance_group)
        root_layout.addWidget(server_group)
        root_layout.addLayout(button_layout)

    def _create_sound_combo(self) -> QComboBox:
        combo = QComboBox(self)
        combo.addItem("標準", "gentle")
        combo.addItem("太鼓", "taiko")
        combo.addItem("斬撃", "zangeki")
        combo.addItem("スクラッチ", "scratch")
        combo.addItem("無音", "off")
        return combo

    def _build_sound_row(self, notification_type: NotificationType) -> QWidget:
        row = QWidget(self)
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        layout.addWidget(self.sound_combos[notification_type], 1)
        layout.addWidget(self.test_buttons[notification_type])
        return row

    def _connect_signals(self) -> None:
        self.theme_combo.currentIndexChanged.connect(self._sync_theme_preview)
        for notification_type, button in self.test_buttons.items():
            button.clicked.connect(self._build_test_request_handler(notification_type))
        self.save_button.clicked.connect(self._emit_save_requested)
        self.cancel_button.clicked.connect(self.reject)

    def _sync_theme_preview(self) -> None:
        self.apply_theme(self.theme_combo.currentData())

    def _emit_test_requested(self, notification_type: NotificationType) -> None:
        self.test_requested.emit(self.settings_from_form(), notification_type)

    def _emit_save_requested(self) -> None:
        self.save_requested.emit(self.settings_from_form())

    def _build_test_request_handler(self, notification_type: NotificationType):
        def emit_test_request() -> None:
            self._emit_test_requested(notification_type)

        return emit_test_request
