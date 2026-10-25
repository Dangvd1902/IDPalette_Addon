import sys
import os
import json
import ctypes
from ctypes import wintypes
from PyQt6.QtWidgets import (
    QApplication, QTreeWidget, QTreeWidgetItem,
    QVBoxLayout, QHBoxLayout, QWidget, QLabel,
    QComboBox, QLineEdit, QPushButton, QDialog, QMessageBox
)
from PyQt6.QtCore import QTimer, Qt
from archicad import ACConnection

# 1. Xác định đúng thư mục gốc để lưu config.json (hỗ trợ cả .py và .exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

TARGET_BUILTIN_NAMES = {
    "Id": "ID",
    "Element ID": "ID",
    "Category_StructuralFunction": "Structural Function",
    "Structural Function": "Structural Function",
    "Category_Position": "Position",
    "Position": "Position",
    "Renovation_RenovationStatus": "Renovation Status",
    "Renovation Status": "Renovation Status"
}

# Windows API để bắt sự kiện click chuột và phím ESC mà không làm nháy Archicad
user32 = ctypes.windll.user32

# Use pointer-sized Win32 handles explicitly (important on 64-bit Windows).
EnumWindowsProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
user32.GetForegroundWindow.restype = wintypes.HWND
user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
user32.GetWindowTextLengthW.restype = ctypes.c_int
user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
user32.GetWindowTextW.restype = ctypes.c_int
user32.GetAsyncKeyState.argtypes = [ctypes.c_int]
user32.GetAsyncKeyState.restype = ctypes.c_short
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.IsWindowVisible.restype = wintypes.BOOL
user32.IsIconic.argtypes = [wintypes.HWND]
user32.IsIconic.restype = wintypes.BOOL
user32.EnumWindows.argtypes = [EnumWindowsProc, wintypes.LPARAM]
user32.EnumWindows.restype = wintypes.BOOL

VK_LBUTTON = 0x01
VK_ESCAPE = 0x1B


def is_archicad_active():
    """Kiểm tra xem cửa sổ đang active có phải là Archicad không"""
    hwnd = user32.GetForegroundWindow()
    if not hwnd:
        return False
    length = user32.GetWindowTextLengthW(hwnd)
    if length == 0:
        return False
    buf = ctypes.create_unicode_buffer(length + 1)
    user32.GetWindowTextW(hwnd, buf, length + 1)
    return "archicad" in buf.value.lower()


def is_archicad_window_visible():
    """Return True if Archicad is visible and not minimized, False if hidden/minimized,
    or None if no Archicad-titled top-level window can be identified.
    """
    window_states = []

    def enum_window(hwnd, _lparam):
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return True

        title_buffer = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, title_buffer, length + 1)
        if "archicad" in title_buffer.value.lower():
            window_states.append((
                bool(user32.IsWindowVisible(hwnd)),
                bool(user32.IsIconic(hwnd))
            ))
        return True

    callback = EnumWindowsProc(enum_window)
    user32.EnumWindows(callback, 0)

    if not window_states:
        return None

    visible_windows = [state for state in window_states if state[0]]
    if not visible_windows:
        return False

    return any(not is_minimized for _is_visible, is_minimized in visible_windows)


class NoScrollComboBox(QComboBox):
    """Vô hiệu hóa thay đổi giá trị khi lăn chuột ngang qua ô"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def wheelEvent(self, event):
        event.ignore()


class FilterConfigDialog(QDialog):
    """Hộp thoại tích chọn các Classification và Custom Property muốn hiển thị"""
    def __init__(self, parent, all_cls_systems, all_custom_groups, current_config):
        super().__init__(parent)
        self.setWindowTitle("Chọn mục hiển thị")
        self.resize(390, 520)

        layout = QVBoxLayout(self)

        top_btns = QHBoxLayout()
        btn_all = QPushButton("Chọn tất cả")
        btn_none = QPushButton("Bỏ chọn tất cả")
        btn_all.clicked.connect(lambda: self.set_all_checks(Qt.CheckState.Checked))
        btn_none.clicked.connect(lambda: self.set_all_checks(Qt.CheckState.Unchecked))
        top_btns.addWidget(btn_all)
        top_btns.addWidget(btn_none)
        layout.addLayout(top_btns)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Danh mục (Classifications & Properties)"])
        layout.addWidget(self.tree)

        font = self.tree.font()
        font.setBold(True)

        enabled_cls = set(current_config.get("classifications", []))
        enabled_props = set(current_config.get("properties", []))

        self.cls_root = QTreeWidgetItem(self.tree, ["CLASSIFICATIONS"])
        self.cls_root.setFont(0, font)
        for sys_key in all_cls_systems:
            item = QTreeWidgetItem(self.cls_root, [sys_key])
            item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
            state = Qt.CheckState.Checked if sys_key in enabled_cls else Qt.CheckState.Unchecked
            item.setCheckState(0, state)

        self.prop_root = QTreeWidgetItem(self.tree, ["CUSTOM PROPERTIES"])
        self.prop_root.setFont(0, font)
        for grp_name, prop_list in all_custom_groups.items():
            grp_item = QTreeWidgetItem(self.prop_root, [grp_name])
            grp_item.setFlags(
                grp_item.flags()
                | Qt.ItemFlag.ItemIsUserCheckable
                | Qt.ItemFlag.ItemIsAutoTristate
            )
            for prop_name in prop_list:
                prop_key = f"{grp_name}::{prop_name}"
                p_item = QTreeWidgetItem(grp_item, [prop_name])
                p_item.setData(0, Qt.ItemDataRole.UserRole, prop_key)
                p_item.setFlags(p_item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                state = Qt.CheckState.Checked if prop_key in enabled_props else Qt.CheckState.Unchecked
                p_item.setCheckState(0, state)

        self.tree.expandAll()

        bottom_btns = QHBoxLayout()
        btn_save = QPushButton("Lưu cấu hình")
        btn_save.setStyleSheet("font-weight: bold; padding: 5px 12px;")
        btn_cancel = QPushButton("Hủy")
        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        bottom_btns.addStretch()
        bottom_btns.addWidget(btn_cancel)
        bottom_btns.addWidget(btn_save)
        layout.addLayout(bottom_btns)

    def set_all_checks(self, state):
        for i in range(self.cls_root.childCount()):
            self.cls_root.child(i).setCheckState(0, state)
        for i in range(self.prop_root.childCount()):
            grp = self.prop_root.child(i)
            for j in range(grp.childCount()):
                grp.child(j).setCheckState(0, state)

    def get_selected_config(self):
        cls_selected = []
        for i in range(self.cls_root.childCount()):
            it = self.cls_root.child(i)
            if it.checkState(0) == Qt.CheckState.Checked:
                cls_selected.append(it.text(0))

        props_selected = []
        for i in range(self.prop_root.childCount()):
            grp = self.prop_root.child(i)
            for j in range(grp.childCount()):
                p_it = grp.child(j)
                if p_it.checkState(0) == Qt.CheckState.Checked:
                    props_selected.append(p_it.data(0, Qt.ItemDataRole.UserRole))

        return {
            "classifications": cls_selected,
            "properties": props_selected
        }


class EventDrivenIDPalette(QWidget):
    def __init__(self, conn):
        super().__init__()
        self.conn = conn
        self.acc = conn.commands
        self.act = conn.types

        self.setWindowTitle("ID & Custom Properties")
        self.resize(420, 450)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(6, 6, 6, 6)

        header_layout = QHBoxLayout()
        self.status_label = QLabel("Sẵn sàng: Click chọn đối tượng trong Archicad")
        self.status_label.setStyleSheet("color: #888; font-size: 11px;")

        self.btn_sync = QPushButton("Đọc chọn")
        self.btn_sync.setToolTip("Đọc ngay đối tượng đang chọn")
        self.btn_sync.setFixedWidth(68)
        self.btn_sync.clicked.connect(self.force_fetch_selection)

        self.btn_reload = QPushButton("↻")
        self.btn_reload.setToolTip("Kết nối / Quét lại danh mục dự án từ Archicad")
        self.btn_reload.setFixedWidth(28)
        self.btn_reload.clicked.connect(self.reload_project_data)

        self.btn_settings = QPushButton("⚙ Mục hiển thị")
        self.btn_settings.setFixedWidth(105)
        self.btn_settings.clicked.connect(self.open_settings_dialog)

        header_layout.addWidget(self.status_label)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_sync)
        header_layout.addWidget(self.btn_reload)
        header_layout.addWidget(self.btn_settings)
        self.layout.addLayout(header_layout)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Mục (Field)", "Giá trị (Value)"])
        self.tree.setColumnWidth(0, 165)
        self.layout.addWidget(self.tree)

        self.current_elements = []
        self.last_selected_guids = frozenset()
        self.is_updating_ui = False

        self.all_cls_meta = {}
        self.all_cls_trees_cache = {}
        self.builtin_props_meta = []
        self.all_custom_groups = {}
        self.custom_props_lookup = {}

        self.active_prop_ids = []
        self.active_prop_meta = {}
        self.active_group_items = {}
        self.active_sys_ids = []
        self.active_cls_widgets = {}

        self.config = self.load_config()
        self.scan_project_metadata()
        self.rebuild_active_ui()
        self.clear_values_display()

        # Hẹn giờ đọc 1 lần sau khi nhả chuột trái 80ms
        self.fetch_delay_timer = QTimer(self)
        self.fetch_delay_timer.setSingleShot(True)
        self.fetch_delay_timer.timeout.connect(self.fetch_selection_once)

        self.was_lbutton_down = False
        self.was_esc_down = False
        self.input_watcher = QTimer(self)
        self.input_watcher.timeout.connect(self.watch_user_input)
        self.input_watcher.start(40)

        # Hide the palette when Archicad is hidden/minimized, then restore it
        # when Archicad becomes visible again. Keep the independent palette
        # above Archicad while Archicad itself is visible.
        self._hidden_by_archicad = False
        self.visibility_watcher = QTimer(self)
        self.visibility_watcher.timeout.connect(self.sync_visibility_with_archicad)
        self.visibility_watcher.start(250)

        self.force_fetch_selection()

    def watch_user_input(self):
        if not is_archicad_active():
            self.was_lbutton_down = False
            self.was_esc_down = False
            return

        lbutton_down = (user32.GetAsyncKeyState(VK_LBUTTON) & 0x8000) != 0
        esc_down = (user32.GetAsyncKeyState(VK_ESCAPE) & 0x8000) != 0

        if (self.was_lbutton_down and not lbutton_down) or (self.was_esc_down and not esc_down):
            self.fetch_delay_timer.start(80)

        self.was_lbutton_down = lbutton_down
        self.was_esc_down = esc_down

    def sync_visibility_with_archicad(self):
        """Keep the palette out of sight while Archicad is minimized or hidden."""
        archicad_visible = is_archicad_window_visible()

        # None means no matching top-level window could be identified; do not
        # unexpectedly hide the palette based on an uncertain detection.
        if archicad_visible is False:
            if self.isVisible():
                self._hidden_by_archicad = True
                self.hide()
        elif archicad_visible is True and self._hidden_by_archicad:
            self._hidden_by_archicad = False
            self.show()
            self.raise_()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"classifications": [], "properties": []}

    def save_config(self):
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.status_label.setText(f"Lỗi lưu config: {e}")

    def flatten_cls_items(self, items, prefix=""):
        res = []
        for wrapper in items:
            item = wrapper.classificationItem
            name_str = f"{item.id} - {item.name}".strip(" -")
            res.append((f"{prefix}{name_str}", item.classificationItemId))
            if hasattr(item, 'children') and item.children:
                res.extend(self.flatten_cls_items(item.children, prefix + "  "))
        return res

    def scan_project_metadata(self):
        self.all_cls_meta.clear()
        self.builtin_props_meta.clear()
        self.all_custom_groups.clear()
        self.custom_props_lookup.clear()

        try:
            cls_systems = self.acc.GetAllClassificationSystems()
            for cs in cls_systems:
                sys_name = f"{cs.name} {getattr(cs, 'version', '')}".strip()
                self.all_cls_meta[sys_name] = cs

            raw_items = self.acc.GetAllPropertyIds()
            all_ids = [item.propertyId if hasattr(item, 'propertyId') else item for item in raw_items]
            details = self.acc.GetDetailsOfProperties(all_ids)

            seen_builtin = set()
            for prop_id, d in zip(all_ids, details):
                defn = d.propertyDefinition
                grp_name = defn.group.name if hasattr(defn, 'group') and defn.group else None

                if defn.name in TARGET_BUILTIN_NAMES and not grp_name:
                    label = TARGET_BUILTIN_NAMES[defn.name]
                    if label not in seen_builtin:
                        seen_builtin.add(label)
                        self.builtin_props_meta.append((prop_id, label, defn))
                elif grp_name:
                    self.all_custom_groups.setdefault(grp_name, []).append(defn.name)
                    key = f"{grp_name}::{defn.name}"
                    self.custom_props_lookup[key] = (prop_id, grp_name, defn.name, defn)

            return True
        except Exception:
            self.status_label.setText("⚠ Đóng hộp thoại trong Archicad rồi bấm ↻")
            return False

    def reload_project_data(self):
        # Thử kết nối lại nếu người dùng vừa đổi cửa sổ dự án Archicad
        new_conn = ACConnection.connect()
        if new_conn:
            self.conn = new_conn
            self.acc = new_conn.commands
            self.act = new_conn.types

        self.all_cls_trees_cache.clear()
        if self.scan_project_metadata():
            self.rebuild_active_ui()
            self.force_fetch_selection()
            self.status_label.setText("Đã tải lại danh mục dự án!")

    def create_property_widget(self, prop_id, defn):
        val_type = getattr(defn, 'valueType', 'string')
        is_editable = getattr(defn, 'isEditable', True)

        if hasattr(defn, 'possibleEnumValues') and defn.possibleEnumValues:
            combo = NoScrollComboBox()
            combo.addItem("<Undefined>", None)
            disp_to_idx = {}
            for i, enum_wrap in enumerate(defn.possibleEnumValues, start=1):
                ev = enum_wrap.enumValue
                disp = getattr(ev, 'displayValue', str(ev.enumValueId))
                combo.addItem(disp, ev.enumValueId)
                disp_to_idx[disp] = i
            combo.setEnabled(is_editable)
            combo.currentIndexChanged.connect(
                lambda idx, pid=prop_id, cb=combo: self.on_enum_changed(pid, cb)
            )
            return combo, val_type, True, disp_to_idx, is_editable
        else:
            line_edit = QLineEdit()
            if not is_editable:
                line_edit.setReadOnly(True)
                line_edit.setStyleSheet("color: #777;")
            else:
                line_edit.editingFinished.connect(
                    lambda pid=prop_id, le=line_edit, vt=val_type: self.on_text_changed(pid, le, vt)
                )
            return line_edit, val_type, False, None, is_editable

    def rebuild_active_ui(self):
        self.is_updating_ui = True
        self.tree.setUpdatesEnabled(False)
        self.tree.clear()
        self.active_prop_ids.clear()
        self.active_prop_meta.clear()
        self.active_group_items.clear()
        self.active_sys_ids.clear()
        self.active_cls_widgets.clear()

        font = self.tree.font()
        font.setBold(True)

        # 1. Nhóm ID AND CATEGORIES
        id_group = QTreeWidgetItem(self.tree, ["ID AND CATEGORIES", ""])
        id_group.setFont(0, font)
        self.active_group_items["__BUILTIN__"] = id_group

        for prop_id, label, defn in self.builtin_props_meta:
            self.active_prop_ids.append(prop_id)
            item = QTreeWidgetItem(id_group, [label, ""])
            w, vt, is_enum, emap, ed = self.create_property_widget(prop_id, defn)
            self.tree.setItemWidget(item, 1, w)
            self.active_prop_meta[prop_id.guid] = (item, id_group, w, vt, is_enum, emap, ed)

        # 2. Nhóm CLASSIFICATIONS
        selected_cls = self.config.get("classifications", [])
        valid_cls = [k for k in selected_cls if k in self.all_cls_meta]
        if valid_cls:
            cls_group = QTreeWidgetItem(self.tree, ["CLASSIFICATIONS", ""])
            cls_group.setFont(0, font)
            for sys_key in valid_cls:
                cs = self.all_cls_meta[sys_key]
                sys_id = cs.classificationSystemId

                if sys_id.guid not in self.all_cls_trees_cache:
                    try:
                        root_items = self.acc.GetAllClassificationsInSystem(sys_id)
                        self.all_cls_trees_cache[sys_id.guid] = self.flatten_cls_items(root_items)
                    except Exception:
                        self.status_label.setText("⚠ Đóng hộp thoại trong Archicad rồi bấm ↻")
                        continue

                self.active_sys_ids.append(sys_id)
                item = QTreeWidgetItem(cls_group, [sys_key, ""])

                combo = NoScrollComboBox()
                combo.addItem("<Unclassified>", None)

                flat_list = self.all_cls_trees_cache.get(sys_id.guid, [])
                guid_to_idx = {}
                for i, (c_label, c_id) in enumerate(flat_list, start=1):
                    combo.addItem(c_label, c_id)
                    guid_to_idx[c_id.guid] = i

                combo.currentIndexChanged.connect(
                    lambda idx, sid=sys_id, cb=combo: self.on_cls_changed(sid, cb)
                )
                self.tree.setItemWidget(item, 1, combo)
                self.active_cls_widgets[sys_id.guid] = (combo, guid_to_idx)

        # 3. Nhóm CUSTOM PROPERTIES
        selected_props = self.config.get("properties", [])
        for prop_key in selected_props:
            if prop_key not in self.custom_props_lookup:
                continue
            prop_id, grp_name, prop_name, defn = self.custom_props_lookup[prop_key]

            if grp_name not in self.active_group_items:
                grp_item = QTreeWidgetItem(self.tree, [grp_name, ""])
                grp_item.setFont(0, font)
                self.active_group_items[grp_name] = grp_item

            grp_item = self.active_group_items[grp_name]
            self.active_prop_ids.append(prop_id)
            item = QTreeWidgetItem(grp_item, [prop_name, ""])
            w, vt, is_enum, emap, ed = self.create_property_widget(prop_id, defn)
            self.tree.setItemWidget(item, 1, w)
            self.active_prop_meta[prop_id.guid] = (item, grp_item, w, vt, is_enum, emap, ed)

        self.tree.expandAll()
        self.tree.setUpdatesEnabled(True)
        self.is_updating_ui = False

    def clear_values_display(self):
        self.is_updating_ui = True
        self.tree.setUpdatesEnabled(False)
        for combo, _ in self.active_cls_widgets.values():
            combo.blockSignals(True)
            combo.setCurrentIndex(0)
            combo.blockSignals(False)
        for _, _, w, _, is_enum, _, _ in self.active_prop_meta.values():
            w.blockSignals(True)
            if is_enum:
                w.setCurrentIndex(0)
            else:
                w.setText("")
            w.blockSignals(False)
        self.tree.setUpdatesEnabled(True)
        self.is_updating_ui = False

    def open_settings_dialog(self):
        if not self.all_cls_meta and not self.all_custom_groups:
            if not self.scan_project_metadata():
                return

        dlg = FilterConfigDialog(
            self,
            list(self.all_cls_meta.keys()),
            self.all_custom_groups,
            self.config
        )
        if dlg.exec() == QDialog.DialogCode.Accepted:
            self.config = dlg.get_selected_config()
            self.save_config()
            self.rebuild_active_ui()
            self.force_fetch_selection()
            self.status_label.setText("Đã lưu cấu hình hiển thị!")

    def force_fetch_selection(self):
        self.last_selected_guids = frozenset(["__FORCE__"])
        self.fetch_selection_once()

    def fetch_selection_once(self):
        if self.is_updating_ui:
            return
        try:
            selection = self.acc.GetSelectedElements()
            if not selection:
                if self.last_selected_guids:
                    self.last_selected_guids = frozenset()
                    self.current_elements = []
                    self.clear_values_display()
                    self.status_label.setText("Chưa chọn đối tượng")
                return

            guids = frozenset(s.elementId.guid for s in selection)
            if guids == self.last_selected_guids:
                return

            self.last_selected_guids = guids
            self.current_elements = [s.elementId for s in selection]
            self.status_label.setText(f"Đang chọn: {len(self.current_elements)} đối tượng")
            self.refresh_values_only()

        except Exception:
            pass

    def refresh_values_only(self):
        if not self.current_elements:
            return
        self.is_updating_ui = True
        elem = self.current_elements[0]

        self.tree.setUpdatesEnabled(False)
        try:
            if self.active_sys_ids:
                cls_results = self.acc.GetClassificationsOfElements([elem], self.active_sys_ids)
                if cls_results and cls_results[0].classificationIds:
                    for sys_id, cls_wrap in zip(self.active_sys_ids, cls_results[0].classificationIds):
                        if sys_id.guid not in self.active_cls_widgets:
                            continue
                        combo, guid_map = self.active_cls_widgets[sys_id.guid]
                        combo.blockSignals(True)
                        curr_guid = None
                        if hasattr(cls_wrap, 'classificationId') and cls_wrap.classificationId.classificationItemId:
                            curr_guid = cls_wrap.classificationId.classificationItemId.guid
                        combo.setCurrentIndex(guid_map.get(curr_guid, 0))
                        combo.blockSignals(False)

            if self.active_prop_ids:
                val_results = self.acc.GetPropertyValuesOfElements([elem], self.active_prop_ids)
                if val_results:
                    for prop_id, val_wrap in zip(self.active_prop_ids, val_results[0].propertyValues):
                        item, grp_item, widget, vt, is_enum, enum_map, is_ed = self.active_prop_meta[prop_id.guid]
                        pv = val_wrap.propertyValue
                        status = getattr(pv, 'status', 'normal')

                        widget.blockSignals(True)
                        if status == 'notAvailable':
                            if is_enum:
                                widget.setCurrentIndex(0)
                            else:
                                widget.setText("<N/A>")
                        else:
                            if is_enum:
                                disp = getattr(pv.value, 'displayValue', None) if hasattr(pv, 'value') else None
                                widget.setCurrentIndex(enum_map.get(disp, 0))
                            else:
                                val_str = str(pv.value) if hasattr(pv, 'value') and pv.value is not None else ""
                                widget.setText(val_str)
                        widget.blockSignals(False)
        except Exception:
            pass
        finally:
            self.tree.setUpdatesEnabled(True)
            self.is_updating_ui = False

    def on_text_changed(self, prop_id, line_edit, val_type):
        if self.is_updating_ui or not self.current_elements:
            return
        text_val = line_edit.text().strip()
        if text_val == "<N/A>":
            return
        try:
            if val_type == 'number':
                new_pv = self.act.NormalNumberPropertyValue(float(text_val or 0), type='number', status='normal')
            elif val_type == 'integer':
                new_pv = self.act.NormalIntegerPropertyValue(int(text_val or 0), type='integer', status='normal')
            else:
                new_pv = self.act.NormalStringPropertyValue(text_val, type='string', status='normal')

            self.acc.SetPropertyValuesOfElements([
                self.act.ElementPropertyValue(e, prop_id, new_pv) for e in self.current_elements
            ])
            self.status_label.setText(f"Đã lưu: {text_val}")
        except Exception as e:
            self.status_label.setText(f"Lỗi ghi dữ liệu: {e}")

    def on_enum_changed(self, prop_id, combo):
        if self.is_updating_ui or not self.current_elements:
            return
        enum_val_id = combo.currentData()
        try:
            if enum_val_id is None:
                new_pv = self.act.UserUndefinedPropertyValue(type='singleEnum', status='userUndefined')
            else:
                new_pv = self.act.NormalSingleEnumPropertyValue(enum_val_id, type='singleEnum', status='normal')
            self.acc.SetPropertyValuesOfElements([
                self.act.ElementPropertyValue(e, prop_id, new_pv) for e in self.current_elements
            ])
            self.status_label.setText(f"Đã lưu: {combo.currentText()}")
        except Exception as e:
            self.status_label.setText(f"Lỗi: {e}")

    def on_cls_changed(self, sys_id, combo):
        if self.is_updating_ui or not self.current_elements:
            return
        item_id = combo.currentData()
        try:
            cls_id = self.act.ClassificationId(sys_id, item_id)
            self.acc.SetClassificationsOfElements([
                self.act.ElementClassification(e, cls_id) for e in self.current_elements
            ])
            self.status_label.setText(f"Đã lưu phân loại: {combo.currentText().strip()}")
            self.refresh_values_only()
        except Exception as e:
            self.status_label.setText(f"Lỗi: {e}")


def main():
    app = QApplication(sys.argv)

    # Vòng lặp kiểm tra kết nối Archicad (hỗ trợ bấm Retry nếu lỡ bật tool trước khi bật Archicad)
    conn = None
    while not conn:
        conn = ACConnection.connect()
        if not conn:
            msg = QMessageBox()
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Không tìm thấy Archicad")
            msg.setText(
                "Chưa kết nối được với Archicad!\n\n"
                "Hãy đảm bảo bạn đã mở phần mềm Archicad và đang mở một file dự án."
            )
            msg.setStandardButtons(
                QMessageBox.StandardButton.Retry | QMessageBox.StandardButton.Close
            )
            ret = msg.exec()
            if ret == QMessageBox.StandardButton.Close:
                sys.exit(0)

    palette = EventDrivenIDPalette(conn)
    palette.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
