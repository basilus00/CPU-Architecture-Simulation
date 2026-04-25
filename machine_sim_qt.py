import sys
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QFrame, QScrollArea
)

# -----------------------------
# Theme (blue-ish, modern)
# -----------------------------
THEME = """
QWidget {
    background: #0b1220;
    color: #e8eefc;
    font-family: "JetBrains Mono", "Consolas", monospace;
}
QFrame#Card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
}
QFrame#Card2 {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 10px;
}
QLabel#Title {
    color: rgba(232,238,252,0.75);
    font-size: 12px;
    letter-spacing: 1px;
}
QLabel#Small {
    color: rgba(232,238,252,0.65);
    font-size: 11px;
}
QLabel#Dim {
    color: rgba(232,238,252,0.55);
    font-size: 10px;
}
QLabel#Flow {
    color: rgba(232,238,252,0.80);
    font-size: 12px;
}
QPushButton {
    padding: 7px 14px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.14);
    background: rgba(255,255,255,0.04);
}
QPushButton:hover { background: rgba(255,255,255,0.07); }
QPushButton:disabled { color: rgba(232,238,252,0.35); border-color: rgba(255,255,255,0.08); }
QPushButton#Primary {
    background: #2b7de9;
    border: 1px solid #1f5fb3;
    color: #ffffff;
}
QPushButton#Primary:hover { background: #1f5fb3; }

QFrame#BusBar {
    background: rgba(255,255,255,0.10);
    border-radius: 4px;
}
QFrame#BusBar[active="true"] {
    background: #2b7de9;
}
QFrame#BusBar[activeRed="true"] {
    background: #e24b4a;
}

QFrame#Block {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 10px;
}
QFrame#Block[active="true"] {
    border: 1px solid #2b7de9;
    box-shadow: 0 0 0 2px rgba(43,125,233,0.20);
}
QFrame#Block[activeRed="true"] {
    border: 1px solid #e24b4a;
}

QLabel#BlockLabel {
    color: rgba(232,238,252,0.55);
    font-size: 10px;
    letter-spacing: 1px;
}
QLabel#BlockValue {
    color: rgba(232,238,252,0.92);
    font-size: 18px;
    font-weight: 600;
}

QFrame#MemCell {
    background: rgba(255,255,255,0.03);
    border: 1px solid rgba(255,255,255,0.10);
    border-radius: 8px;
}
QFrame#MemCell[read="true"] {
    background: rgba(43,125,233,0.16);
    border: 1px solid rgba(43,125,233,0.60);
}
QFrame#MemCell[write="true"] {
    background: rgba(226,75,74,0.16);
    border: 1px solid rgba(226,75,74,0.65);
}
QLabel#Addr {
    color: rgba(232,238,252,0.55);
    font-size: 10px;
}
QLabel#Val {
    color: rgba(232,238,252,0.90);
    font-size: 12px;
    font-weight: 600;
}
QLabel#Val[read="true"] { color: #7cb3ff; }
QLabel#Val[write="true"] { color: #ff8d8c; }

QFrame#Tag {
    border-radius: 6px;
    padding: 2px 8px;
}
QFrame#Tag[mode="chercher"] { background: rgba(43,125,233,0.18); }
QFrame#Tag[mode="decoder"] { background: rgba(188,117,23,0.20); }
QFrame#Tag[mode="executer"] { background: rgba(226,75,74,0.18); }
QLabel#TagText {
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}
QLabel#TagText[mode="chercher"] { color: #7cb3ff; }
QLabel#TagText[mode="decoder"] { color: #f2c07a; }
QLabel#TagText[mode="executer"] { color: #ff8d8c; }

QFrame#LogEntry {
    background: rgba(255,255,255,0.02);
    border-top: 1px solid rgba(255,255,255,0.07);
}
QLabel#LogText {
    color: rgba(232,238,252,0.70);
    font-size: 11px;
}
QLabel#LogText[current="true"] {
    color: #7cb3ff;
    font-weight: 700;
}
"""


# -----------------------------
# Data + micro-step builder
# -----------------------------
MEM_INIT: Dict[int, str] = {
    0: "1010", 1: "3011", 2: "2012", 3: "5005", 4: "", 5: "99", 6: "", 7: "", 8: "", 9: "",
    10: "23", 11: "14", 12: "", 13: "", 14: "", 15: "", 16: "", 17: "", 18: "", 19: "",
    20: "", 21: "", 22: "", 23: "", 24: "", 25: "", 26: "", 27: "", 28: "", 29: "",
    30: "", 31: "", 32: "", 33: "", 34: "", 35: "", 36: "", 37: "", 38: "", 39: ""
}


def decode(instr: str):
    if not instr:
        return None, None
    s = str(instr).zfill(4)
    return int(s[:2]), int(s[2:])


def code_desc(code: int):
    return {
        10: "Charger ACC",
        20: "Ranger ACC→mém",
        30: "Additionner ACC",
        50: "Saut incond.",
        99: "Arrêt"
    }.get(code, "?")


@dataclass
class Step:
    phase: str
    sub: str
    desc: str
    flow: str
    state: Dict[str, Any]  # {"cpu":{...}, "mem":{...}}
    activeBlocks: List[str]
    busActive: bool
    highlightAddr: Optional[int] = None
    writeAddr: Optional[int] = None


def build_steps(mem0: Dict[int, str]) -> List[Step]:
    steps: List[Step] = []

    cpu = {
        "co": 0, "ri_code": None, "ri_operand": None,
        "ra": None, "rm": None, "acc": None, "seq_code": None,
        "ual": "—",
    }
    mem = dict(mem0)

    def clone_state():
        return {"cpu": dict(cpu), "mem": dict(mem)}

    def add_step(phase, sub, desc, flow, active, bus, h=None, w=None):
        steps.append(Step(
            phase=phase, sub=sub, desc=desc, flow=flow,
            state=clone_state(),
            activeBlocks=active or [],
            busActive=bus,
            highlightAddr=h,
            writeAddr=w
        ))

    add_step("initial", "", "État initial — programme chargé, CO = 0",
             "Prêt. Appuyez sur Étape suivante pour commencer.",
             ["blk-co"], False)

    max_iter = 100
    for _ in range(max_iter):
        co = cpu["co"]

        # CHERCHER
        cpu["ra"] = co
        add_step("chercher", "CO dans RA",
                 "CO → RA (prépare lecture de l'instruction)",
                 f"CO [{co}] → RA",
                 ["blk-co", "blk-ra"], True)

        cpu["co"] = co + 1
        add_step("chercher", "Incrémentation CO",
                 "CO = CO + 1 (pointe la prochaine instruction)",
                 f"CO ← {cpu['co']}",
                 ["blk-co"], False)

        cpu["rm"] = mem.get(co, "") or ""
        add_step("chercher", "Lecture instruction",
                 "Mem[RA] → RM (instruction lue en mémoire)",
                 f"Mem[{co}] = {cpu['rm'] or '—'} → RM",
                 ["blk-ra", "blk-seq"], True, h=co)

        code, operand = decode(cpu["rm"])
        cpu["ri_code"] = code
        cpu["ri_operand"] = operand
        add_step("chercher", "RM dans RI",
                 "RM → RI (instruction dans le registre d'instruction)",
                 f"RM [{cpu['rm'] or '—'}] → RI",
                 ["blk-ri", "blk-seq"], True, h=co)

        if code is None:
            add_step("executer", "Arrêt", "Cellule vide — arrêt.", "—", [], False)
            break

        # DÉCODER
        cpu["seq_code"] = code
        add_step("decoder", "Décodage RI",
                 f"RI décodé → SEQ (opération: {code_desc(code)})",
                 f"Code = {code} ({code_desc(code)})",
                 ["blk-seq", "blk-ri"], False)

        if code == 99:
            add_step("executer", "Arrêt programme", "Code 99 → arrêt du programme.", "FIN", ["blk-seq"], False)
            break

        if code == 50:
            cpu["ra"] = operand
            add_step("decoder", "Adresse saut dans RA",
                     f"Opérande ({operand}) → RA pour saut",
                     f"Opérande {operand} → RA",
                     ["blk-ra", "blk-ri"], True)
            cpu["co"] = operand
            add_step("executer", "Branchement: adresse dans CO",
                     f"RA → CO (saut à l'adresse {operand})",
                     f"CO ← {operand}",
                     ["blk-co", "blk-ra"], True)
            add_step("initial", "", f"État après saut — prêt à exécuter adresse {operand}",
                     f"CO = {operand}",
                     ["blk-co"], False)
            continue

        # for 10/20/30: operand address -> RA, read operand -> RM
        cpu["ra"] = operand
        add_step("decoder", "Adresse opérande dans RA",
                 f"Opérande ({operand}) → RA (prépare accès à la donnée)",
                 f"Opérande [{operand}] → RA",
                 ["blk-ra", "blk-ri"], True)

        cpu["rm"] = mem.get(operand, "") or ""
        add_step("decoder", "Lecture opérande dans RM",
                 f"Mem[RA={operand}] → RM (donnée: {cpu['rm'] or '—'})",
                 f"Mem[{operand}] = {cpu['rm'] or '—'} → RM",
                 ["blk-ra"], True, h=operand)

        # EXÉCUTER
        if code == 10:
            cpu["acc"] = int(cpu["rm"]) if (cpu["rm"] and cpu["rm"].isdigit()) else 0
            cpu["ual"] = "LOAD"
            add_step("executer", "Chargement RM dans ACC",
                     f"RM → ACC (ACC = {cpu['acc']})",
                     f"ACC ← {cpu['acc']}",
                     ["blk-acc", "blk-ual"], True, h=operand)

        elif code == 30:
            prev = cpu["acc"] or 0
            opv = int(cpu["rm"]) if (cpu["rm"] and cpu["rm"].lstrip("-").isdigit()) else 0
            cpu["acc"] = prev + opv
            cpu["ual"] = f"{prev}+{opv}={cpu['acc']}"
            add_step("executer", "Addition RM + ACC, somme dans ACC",
                     f"ACC ({prev}) + RM ({opv}) = {cpu['acc']} → ACC",
                     f"ACC = {prev} + {opv} = {cpu['acc']}",
                     ["blk-acc", "blk-ual"], True, h=operand)

        elif code == 20:
            val = cpu["acc"] or 0
            cpu["rm"] = str(val)
            cpu["ual"] = "STORE"
            add_step("executer", "ACC dans RM",
                     f"ACC ({val}) → RM prêt pour écriture",
                     f"ACC [{val}] → RM",
                     ["blk-acc"], True)

            mem[operand] = str(val)
            add_step("executer", "Écriture en mémoire",
                     f"RM → Mem[{operand}] ({val} écrit en mémoire)",
                     f"RM → Mem[{operand}] = {val}",
                     ["blk-ra"], True, w=operand)

        add_step("initial", "État fin instruction",
                 f"Instruction à CO={co} terminée. Prochain CO={cpu['co']}",
                 f"CO = {cpu['co']}",
                 ["blk-co"], False)

    return steps


# -----------------------------
# UI Widgets
# -----------------------------
class Block(QFrame):
    def __init__(self, title: str, value_big=True):
        super().__init__()
        self.setObjectName("Block")
        self.setProperty("active", False)
        self.setProperty("activeRed", False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 10)
        lay.setSpacing(6)

        self.lbl = QLabel(title)
        self.lbl.setObjectName("BlockLabel")
        lay.addWidget(self.lbl)

        self.value = QLabel("—")
        self.value.setObjectName("BlockValue")
        if not value_big:
            self.value.setStyleSheet("font-size: 14px; font-weight: 600;")
        lay.addWidget(self.value)

        self.extra = QLabel("")
        self.extra.setObjectName("Dim")
        lay.addWidget(self.extra)

        self.extra.hide()

    def set_value(self, text: str):
        self.value.setText(text)

    def set_extra(self, text: str):
        self.extra.setText(text)
        self.extra.setVisible(bool(text))

    def set_active(self, on: bool, red: bool = False):
        self.setProperty("active", on and not red)
        self.setProperty("activeRed", on and red)
        self.style().unpolish(self)
        self.style().polish(self)


class MemCell(QFrame):
    def __init__(self, addr: int):
        super().__init__()
        self.addr = addr
        self.setObjectName("MemCell")
        self.setProperty("read", False)
        self.setProperty("write", False)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(2)

        self.addr_lbl = QLabel(f"{addr}:")
        self.addr_lbl.setObjectName("Addr")
        lay.addWidget(self.addr_lbl)

        self.val_lbl = QLabel("—")
        self.val_lbl.setObjectName("Val")
        lay.addWidget(self.val_lbl)

    def set_value(self, v: str):
        self.val_lbl.setText(v if v else "—")

    def set_flags(self, read=False, write=False):
        self.setProperty("read", read)
        self.setProperty("write", write)
        self.val_lbl.setProperty("read", read)
        self.val_lbl.setProperty("write", write)
        self.style().unpolish(self)
        self.style().polish(self)
        self.val_lbl.style().unpolish(self.val_lbl)
        self.val_lbl.style().polish(self.val_lbl)


class LogEntry(QFrame):
    def __init__(self, text: str, current: bool):
        super().__init__()
        self.setObjectName("LogEntry")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 6, 10, 6)
        self.lbl = QLabel(text)
        self.lbl.setObjectName("LogText")
        self.lbl.setProperty("current", current)
        lay.addWidget(self.lbl)

    def set_current(self, cur: bool):
        self.lbl.setProperty("current", cur)
        self.lbl.style().unpolish(self.lbl)
        self.lbl.style().polish(self.lbl)


# -----------------------------
# Main Window
# -----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Machine élémentaire — simulateur pas à pas (Qt/Python)")

        self.mem = dict(MEM_INIT)
        self.steps: List[Step] = []
        self.step_idx = 0

        root = QVBoxLayout(self)
        root.setContentsMargins(14, 14, 14, 14)
        root.setSpacing(10)

        title = QLabel("Machine élémentaire — simulateur pas à pas")
        title.setObjectName("Title")
        title.setAlignment(Qt.AlignHCenter)
        root.addWidget(title)

        # Phase display
        self.phase_card = QFrame()
        self.phase_card.setObjectName("Card")
        ph_lay = QHBoxLayout(self.phase_card)
        ph_lay.setContentsMargins(12, 10, 12, 10)
        ph_lay.setSpacing(10)

        self.tag = QFrame()
        self.tag.setObjectName("Tag")
        self.tag.setProperty("mode", "chercher")
        tag_lay = QHBoxLayout(self.tag)
        tag_lay.setContentsMargins(8, 4, 8, 4)
        self.tag_text = QLabel("CHERCHER")
        self.tag_text.setObjectName("TagText")
        self.tag_text.setProperty("mode", "chercher")
        tag_lay.addWidget(self.tag_text)

        self.phase_desc = QLabel("État initial — programme chargé, CO = 0")
        self.phase_desc.setObjectName("Small")

        ph_lay.addWidget(self.tag, 0)
        ph_lay.addWidget(self.phase_desc, 1)
        root.addWidget(self.phase_card)

        # Flow
        self.flow = QLabel("Prêt. Appuyez sur Étape suivante pour commencer.")
        self.flow.setObjectName("Flow")
        self.flow.setWordWrap(True)

        flow_card = QFrame()
        flow_card.setObjectName("Card2")
        fl = QVBoxLayout(flow_card)
        fl.setContentsMargins(12, 10, 12, 10)
        fl.addWidget(self.flow)
        root.addWidget(flow_card)

        # Bus
        bus_row = QVBoxLayout()
        bus_label = QLabel("Bus de données")
        bus_label.setObjectName("Dim")
        bus_label.setAlignment(Qt.AlignRight)
        bus_row.addWidget(bus_label)

        self.bus_bar = QFrame()
        self.bus_bar.setObjectName("BusBar")
        self.bus_bar.setFixedHeight(8)
        self.bus_bar.setProperty("active", False)
        self.bus_bar.setProperty("activeRed", False)
        bus_row.addWidget(self.bus_bar)
        root.addLayout(bus_row)

        # Machine layout: CPU left, memory right
        machine = QHBoxLayout()
        machine.setSpacing(10)
        root.addLayout(machine, 1)

        # CPU side
        cpu_col = QVBoxLayout()
        cpu_col.setSpacing(8)
        machine.addLayout(cpu_col, 0)

        self.blk_seq = Block("SEQ — Séquenceur", value_big=False)
        self.blk_seq.set_value("—")
        cpu_col.addWidget(self.blk_seq)

        self.blk_ual = Block("UAL", value_big=False)
        self.blk_ual.set_value("—")
        cpu_col.addWidget(self.blk_ual)

        self.blk_acc = Block("ACC")
        cpu_col.addWidget(self.blk_acc)

        reg_row = QHBoxLayout()
        reg_row.setSpacing(8)
        cpu_col.addLayout(reg_row)

        self.blk_ri = Block("RI", value_big=False)
        self.blk_ri.set_extra("—")
        reg_row.addWidget(self.blk_ri, 1)

        self.blk_co = Block("CO", value_big=False)
        reg_row.addWidget(self.blk_co, 1)

        self.blk_ra = Block("RA — Registre d'adresse", value_big=False)
        cpu_col.addWidget(self.blk_ra)

        cpu_col.addStretch(1)

        # Memory side card
        mem_card = QFrame()
        mem_card.setObjectName("Card")
        machine.addWidget(mem_card, 1)

        mem_lay = QVBoxLayout(mem_card)
        mem_lay.setContentsMargins(12, 12, 12, 12)
        mem_lay.setSpacing(8)

        mem_title = QLabel("Mémoire")
        mem_title.setObjectName("BlockLabel")
        mem_lay.addWidget(mem_title)

        self.mem_grid = QGridLayout()
        self.mem_grid.setHorizontalSpacing(6)
        self.mem_grid.setVerticalSpacing(6)
        mem_lay.addLayout(self.mem_grid)

        # exactly like your grid (first 0..19 visible). You can extend to 40 with scroll if you want.
        self.mem_cells: Dict[int, MemCell] = {}
        visible_addrs = list(range(0, 20))
        for i, addr in enumerate(visible_addrs):
            r = i // 4
            c = i % 4
            cell = MemCell(addr)
            self.mem_cells[addr] = cell
            self.mem_grid.addWidget(cell, r, c)

        # RM display inside memory card
        rm_wrap = QFrame()
        rm_wrap.setObjectName("Card2")
        rm_lay = QVBoxLayout(rm_wrap)
        rm_lay.setContentsMargins(10, 8, 10, 8)
        rm_lay.setSpacing(4)
        rm_label = QLabel("RM — Registre mémoire")
        rm_label.setObjectName("BlockLabel")
        rm_lay.addWidget(rm_label)
        self.rm_value = QLabel("—")
        self.rm_value.setFont(QFont(self.rm_value.font().family(), 16, QFont.Bold))
        self.rm_value.setStyleSheet("color: #7cb3ff;")
        rm_lay.addWidget(self.rm_value)
        mem_lay.addWidget(rm_wrap)

        # Controls
        ctrl = QHBoxLayout()
        ctrl.setSpacing(8)
        root.addLayout(ctrl)

        self.btn_reset = QPushButton("↺ Réinitialiser")
        self.btn_step = QPushButton("Étape suivante →")
        self.btn_step.setObjectName("Primary")
        self.btn_run = QPushButton("▶ Auto")
        self.btn_stop = QPushButton("■ Stop")
        self.btn_stop.setDisabled(True)

        ctrl.addWidget(self.btn_reset)
        ctrl.addWidget(self.btn_step)
        ctrl.addWidget(self.btn_run)
        ctrl.addWidget(self.btn_stop)
        ctrl.addStretch(1)

        self.step_info = QLabel("Étape 0")
        self.step_info.setObjectName("Dim")
        ctrl.addWidget(self.step_info)

        # Log
        log_card = QFrame()
        log_card.setObjectName("Card")
        root.addWidget(log_card)

        log_lay = QVBoxLayout(log_card)
        log_lay.setContentsMargins(0, 0, 0, 0)
        log_lay.setSpacing(0)

        log_hdr = QLabel("Journal d'exécution")
        log_hdr.setObjectName("BlockLabel")
        log_hdr.setStyleSheet("padding: 8px 12px; background: rgba(255,255,255,0.03);")
        log_lay.addWidget(log_hdr)

        self.log_area = QScrollArea()
        self.log_area.setWidgetResizable(True)
        self.log_area.setFrameShape(QFrame.NoFrame)
        self.log_area.setStyleSheet("background: transparent;")
        log_lay.addWidget(self.log_area)

        self.log_body = QWidget()
        self.log_body_lay = QVBoxLayout(self.log_body)
        self.log_body_lay.setContentsMargins(0, 0, 0, 0)
        self.log_body_lay.setSpacing(0)
        self.log_area.setWidget(self.log_body)

        # Timer
        self.timer = QTimer(self)
        self.timer.setInterval(900)
        self.timer.timeout.connect(self.on_step)

        # Connect
        self.btn_reset.clicked.connect(self.on_reset)
        self.btn_step.clicked.connect(self.on_step)
        self.btn_run.clicked.connect(self.on_run)
        self.btn_stop.clicked.connect(self.on_stop)

        self.on_reset()

    # ----- render -----
    def set_phase(self, phase: str, desc: str):
        if phase == "chercher":
            mode = "chercher"
            text = "CHERCHER"
        elif phase == "decoder":
            mode = "decoder"
            text = "DÉCODER"
        elif phase == "executer":
            mode = "executer"
            text = "EXÉCUTER"
        else:
            mode = "chercher"
            text = "ÉTAT"
        self.tag.setProperty("mode", mode)
        self.tag_text.setProperty("mode", mode)
        self.tag_text.setText(text)
        self.tag.style().unpolish(self.tag); self.tag.style().polish(self.tag)
        self.tag_text.style().unpolish(self.tag_text); self.tag_text.style().polish(self.tag_text)
        self.phase_desc.setText(desc)

    def set_bus(self, active: bool, red: bool = False):
        self.bus_bar.setProperty("active", active and not red)
        self.bus_bar.setProperty("activeRed", active and red)
        self.bus_bar.style().unpolish(self.bus_bar)
        self.bus_bar.style().polish(self.bus_bar)

    def set_block_actives(self, ids: List[str]):
        mapping = {
            "blk-seq": self.blk_seq,
            "blk-ual": self.blk_ual,
            "blk-acc": self.blk_acc,
            "blk-ri": self.blk_ri,
            "blk-co": self.blk_co,
            "blk-ra": self.blk_ra,
        }
        for k, w in mapping.items():
            w.set_active(k in ids)

    def render_memory(self, mem: Dict[int, str], highlight: Optional[int], write: Optional[int]):
        for addr, cell in self.mem_cells.items():
            cell.set_value(mem.get(addr, ""))
            cell.set_flags(read=(addr == highlight), write=(addr == write))

    def apply_step(self, s: Step):
        cpu = s.state["cpu"]
        self.mem = dict(s.state["mem"])

        self.set_phase(s.phase, s.desc)
        self.flow.setText(s.flow)
        self.set_bus(s.busActive)

        self.blk_co.set_value(str(cpu.get("co", "—")) if cpu.get("co") is not None else "—")
        self.blk_ra.set_value(str(cpu.get("ra", "—")) if cpu.get("ra") is not None else "—")

        rm = cpu.get("rm", "")
        self.rm_value.setText(rm if rm else "—")

        acc = cpu.get("acc", None)
        self.blk_acc.set_value(str(acc) if acc is not None else "—")

        ri_code = cpu.get("ri_code", None)
        ri_op = cpu.get("ri_operand", None)
        self.blk_ri.set_value(str(ri_code) if ri_code is not None else "—")
        self.blk_ri.set_extra(f"op: {ri_op}" if ri_op is not None else "—")

        seq_code = cpu.get("seq_code", None)
        self.blk_seq.set_value(f"Code = {seq_code}" if seq_code is not None else "—")

        ual = cpu.get("ual", "—")
        self.blk_ual.set_value(str(ual) if ual is not None else "—")

        self.set_block_actives(s.activeBlocks)
        self.render_memory(self.mem, s.highlightAddr, s.writeAddr)

        self.step_info.setText(f"Étape {self.step_idx} / {len(self.steps)-1}")
        self.btn_step.setDisabled(self.step_idx >= len(self.steps) - 1)

    def log_add(self, text: str):
        # un-current previous
        for i in range(self.log_body_lay.count()):
            w = self.log_body_lay.itemAt(i).widget()
            if isinstance(w, LogEntry):
                w.set_current(False)

        entry = LogEntry(text, True)
        self.log_body_lay.addWidget(entry)
        # keep bottom spacer
        if self.log_body_lay.count() == 1:
            self.log_body_lay.addStretch(1)

    # ----- actions -----
    def on_reset(self):
        self.on_stop()
        self.mem = dict(MEM_INIT)
        self.steps = build_steps(self.mem)
        self.step_idx = 0

        # clear log
        while self.log_body_lay.count():
            item = self.log_body_lay.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()

        self.apply_step(self.steps[0])
        self.log_add("[0] INITIAL: Programme chargé, CO = 0")

    def on_step(self):
        if self.step_idx >= len(self.steps) - 1:
            self.on_stop()
            return
        self.step_idx += 1
        s = self.steps[self.step_idx]
        self.apply_step(s)
        self.log_add(f"[{self.step_idx}] {s.phase.upper()} {s.sub}: {s.desc}")

    def on_run(self):
        self.btn_run.setDisabled(True)
        self.btn_stop.setDisabled(False)
        self.timer.start()

    def on_stop(self):
        self.timer.stop()
        self.btn_run.setDisabled(False)
        self.btn_stop.setDisabled(True)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(THEME)
    w = MainWindow()
    w.resize(1100, 780)
    w.show()
    sys.exit(app.exec())