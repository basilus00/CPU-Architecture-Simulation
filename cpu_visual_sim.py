import sys
from dataclasses import dataclass
from enum import Enum, auto

from PySide6.QtCore import Qt, QTimer, QRectF, QPointF
from PySide6.QtGui import QBrush, QPen, QColor, QFont, QPainterPath
from PySide6.QtWidgets import (
    QApplication, QWidget, QGraphicsView, QGraphicsScene,
    QGraphicsRectItem, QGraphicsSimpleTextItem, QGraphicsLineItem,
    QGraphicsPathItem, QHBoxLayout, QVBoxLayout, QPushButton, QLabel
)

# ----------------------------
# CPU + Micro-architecture
# ----------------------------
class State(Enum):
    FETCH_RA = auto()      # CO -> RA
    FETCH_RM = auto()      # MEM[RA] -> RM
    FETCH_RI = auto()      # RM -> RI (and decode)
    FETCH_INC = auto()     # CO <- CO + 1
    DECODE = auto()

    EXEC_LOAD_1 = auto()   # operand -> RA
    EXEC_LOAD_2 = auto()   # MEM[RA] -> RM
    EXEC_LOAD_3 = auto()   # RM -> ACC

    EXEC_STORE_1 = auto()  # operand -> RA
    EXEC_STORE_2 = auto()  # ACC -> RM
    EXEC_STORE_3 = auto()  # RM -> MEM[RA]

    EXEC_ADD_1 = auto()    # operand -> RA
    EXEC_ADD_2 = auto()    # MEM[RA] -> RM
    EXEC_ADD_3 = auto()    # ACC + RM -> ACC

    EXEC_JUMP = auto()     # operand -> CO
    HALT = auto()


@dataclass
class CPU:
    memory: list
    CO: int = 0
    RI: int = 0
    RA: int = 0
    RM: int = 0
    ACC: int = 0
    DRAP: int = 0

    opcode: int = 0
    operand: int = 0
    state: State = State.FETCH_RA
    halted: bool = False

    last_transfer: str = ""
    last_detail: str = ""

    def reset(self):
        self.memory = [0] * 40
        self.memory[0] = 1010
        self.memory[1] = 3011
        self.memory[2] = 2012
        self.memory[3] = 5005
        self.memory[5] = 99
        self.memory[10] = 23
        self.memory[11] = 14

        self.CO = 0
        self.RI = 0
        self.RA = 0
        self.RM = 0
        self.ACC = 0
        self.DRAP = 0
        self.opcode = 0
        self.operand = 0
        self.state = State.FETCH_RA
        self.halted = False
        self.last_transfer = ""
        self.last_detail = "Reset."

    def step(self):
        if self.halted:
            self.last_transfer = ""
            self.last_detail = "HALT."
            return

        s = self.state
        self.last_transfer = ""
        self.last_detail = ""

        # -------- FETCH --------
        if s == State.FETCH_RA:
            self.RA = self.CO
            self.last_transfer = "CO->RA"
            self.last_detail = f"FETCH: RA <- CO ({self.CO})"
            self.state = State.FETCH_RM

        elif s == State.FETCH_RM:
            self.RM = self.memory[self.RA]
            self.last_transfer = "MEM->RM"
            self.last_detail = f"FETCH: RM <- MEM[{self.RA}] ({self.RM})"
            self.state = State.FETCH_RI

        elif s == State.FETCH_RI:
            self.RI = self.RM
            self.opcode = self.RI // 100
            self.operand = self.RI % 100
            self.last_transfer = "RM->RI"
            self.last_detail = f"FETCH: RI <- RM ({self.RI}) ; opcode={self.opcode} operand={self.operand}"
            self.state = State.FETCH_INC

        elif s == State.FETCH_INC:
            self.CO += 1
            self.last_transfer = "CO++"
            self.last_detail = f"FETCH: CO <- CO + 1 ({self.CO})"
            self.state = State.DECODE

        # -------- DECODE --------
        elif s == State.DECODE:
            if self.opcode == 10:
                self.state = State.EXEC_LOAD_1
                self.last_detail = "DECODE: LOAD"
            elif self.opcode == 20:
                self.state = State.EXEC_STORE_1
                self.last_detail = "DECODE: STORE"
            elif self.opcode == 30:
                self.state = State.EXEC_ADD_1
                self.last_detail = "DECODE: ADD"
            elif self.opcode == 50:
                self.state = State.EXEC_JUMP
                self.last_detail = "DECODE: JUMP"
            elif self.opcode == 99:
                self.state = State.HALT
                self.last_detail = "DECODE: HALT"
            else:
                self.last_detail = f"DECODE: Unknown opcode {self.opcode} -> HALT"
                self.state = State.HALT

        # -------- EXEC LOAD (10) --------
        elif s == State.EXEC_LOAD_1:
            self.RA = self.operand
            self.last_transfer = "OP->RA"
            self.last_detail = f"LOAD: RA <- operand ({self.operand})"
            self.state = State.EXEC_LOAD_2

        elif s == State.EXEC_LOAD_2:
            self.RM = self.memory[self.RA]
            self.last_transfer = "MEM->RM"
            self.last_detail = f"LOAD: RM <- MEM[{self.RA}] ({self.RM})"
            self.state = State.EXEC_LOAD_3

        elif s == State.EXEC_LOAD_3:
            self.ACC = self.RM
            self.last_transfer = "RM->ACC"
            self.last_detail = f"LOAD: ACC <- RM ({self.ACC})"
            self.state = State.FETCH_RA

        # -------- EXEC STORE (20) --------
        elif s == State.EXEC_STORE_1:
            self.RA = self.operand
            self.last_transfer = "OP->RA"
            self.last_detail = f"STORE: RA <- operand ({self.operand})"
            self.state = State.EXEC_STORE_2

        elif s == State.EXEC_STORE_2:
            self.RM = self.ACC
            self.last_transfer = "ACC->RM"
            self.last_detail = f"STORE: RM <- ACC ({self.RM})"
            self.state = State.EXEC_STORE_3

        elif s == State.EXEC_STORE_3:
            self.memory[self.RA] = self.RM
            self.last_transfer = "RM->MEM"
            self.last_detail = f"STORE: MEM[{self.RA}] <- RM ({self.RM})"
            self.state = State.FETCH_RA

        # -------- EXEC ADD (30) --------
        elif s == State.EXEC_ADD_1:
            self.RA = self.operand
            self.last_transfer = "OP->RA"
            self.last_detail = f"ADD: RA <- operand ({self.operand})"
            self.state = State.EXEC_ADD_2

        elif s == State.EXEC_ADD_2:
            self.RM = self.memory[self.RA]
            self.last_transfer = "MEM->RM"
            self.last_detail = f"ADD: RM <- MEM[{self.RA}] ({self.RM})"
            self.state = State.EXEC_ADD_3

        elif s == State.EXEC_ADD_3:
            res = self.ACC + self.RM
            self.ACC = res
            self.last_transfer = "ALU->ACC"
            self.last_detail = f"ADD: ACC <- ACC + RM ({res})"
            self.state = State.FETCH_RA

        # -------- EXEC JUMP (50) --------
        elif s == State.EXEC_JUMP:
            self.CO = self.operand
            self.last_transfer = "OP->CO"
            self.last_detail = f"JUMP: CO <- operand ({self.operand})"
            self.state = State.FETCH_RA

        # -------- HALT --------
        elif s == State.HALT:
            self.halted = True
            self.last_transfer = "HALT"
            self.last_detail = "HALT: Program stopped."


# ----------------------------
# Graphics helpers
# ----------------------------
class Block:
    """A labeled rectangle with a value text."""
    def __init__(self, scene, x, y, w, h, label):
        self.rect = QGraphicsRectItem(x, y, w, h)
        self.rect.setPen(QPen(Qt.black, 2))
        self.rect.setBrush(QBrush(QColor("#f3f3f3")))
        self.rect.setZValue(10)
        scene.addItem(self.rect)

        self.label = QGraphicsSimpleTextItem(label, self.rect)
        self.label.setBrush(QBrush(Qt.black))
        self.label.setPos(x + 6, y + 4)
        self.label.setFont(QFont("Arial", 9, QFont.Bold))

        self.value = QGraphicsSimpleTextItem("", self.rect)
        self.value.setBrush(QBrush(QColor("#0b3d91")))
        self.value.setPos(x + 6, y + 22)
        self.value.setFont(QFont("Arial", 12, QFont.Bold))

        self.base_brush = self.rect.brush()

    def set_value(self, v):
        self.value.setText(str(v))

    def highlight(self, on: bool, color="#ffe082"):
        self.rect.setBrush(QBrush(QColor(color) if on else self.base_brush.color()))


class RoutedArrow:
    """
    Orthogonal (Manhattan) polyline path. Prevents cutting through blocks.
    Hot-highlight turns pen thick red.
    """
    def __init__(self, scene, points, color="#1e88e5"):
        self.item = QGraphicsPathItem()
        self.item.setZValue(5)

        self.base_pen = QPen(QColor(color), 3)
        self.hot_pen = QPen(QColor("#e53935"), 6)
        self.item.setPen(self.base_pen)

        path = QPainterPath()
        x0, y0 = points[0]
        path.moveTo(QPointF(x0, y0))
        for (x, y) in points[1:]:
            path.lineTo(QPointF(x, y))

        self.item.setPath(path)
        scene.addItem(self.item)

    def set_hot(self, hot: bool):
        self.item.setPen(self.hot_pen if hot else self.base_pen)


# ----------------------------
# Main Window
# ----------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simulateur Machine Élémentaire (Python / Qt)")

        self.cpu = CPU(memory=[0] * 40)
        self.cpu.reset()

        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHints(self.view.renderHints())

        # UI
        self.step_btn = QPushButton("Étape suivante")
        self.reset_btn = QPushButton("Réinitialiser")
        self.run_btn = QPushButton("Auto (run/stop)")
        self.status = QLabel("Prêt.")
        self.detail = QLabel("")

        self.status.setStyleSheet("font-weight: bold; color: #0b3d91;")
        self.detail.setStyleSheet("color: #333;")

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.step_btn)
        btn_row.addWidget(self.run_btn)
        btn_row.addWidget(self.reset_btn)

        layout = QVBoxLayout()
        layout.addWidget(self.view, stretch=1)
        layout.addLayout(btn_row)
        layout.addWidget(self.status)
        layout.addWidget(self.detail)
        self.setLayout(layout)

        # Timer for auto-run
        self.timer = QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.on_step)

        # Diagram state
        self.blocks = {}
        self.arrows = {}
        self.mem_cells = []

        self._build_diagram()

        # Connect
        self.step_btn.clicked.connect(self.on_step)
        self.reset_btn.clicked.connect(self.on_reset)
        self.run_btn.clicked.connect(self.on_toggle_run)

        self.refresh()

    # ---------- geometry helpers (anchors on edges) ----------
    def _r(self, key: str):
        return self.blocks[key].rect.rect()

    def _top(self, key: str):
        r = self._r(key)
        return (r.x() + r.width() / 2, r.y())

    def _bottom(self, key: str):
        r = self._r(key)
        return (r.x() + r.width() / 2, r.y() + r.height())

    def _left(self, key: str):
        r = self._r(key)
        return (r.x(), r.y() + r.height() / 2)

    def _right(self, key: str):
        r = self._r(key)
        return (r.x() + r.width(), r.y() + r.height() / 2)

    def _build_diagram(self):
        self.scene.clear()
        self.scene.setSceneRect(QRectF(0, 0, 1100, 650))

        # --- Panels like the PDF ---
        cpu_panel = QGraphicsRectItem(20, 40, 520, 560)
        cpu_panel.setBrush(QBrush(QColor("#cfcfcf")))
        cpu_panel.setPen(QPen(QColor("#666"), 2))
        self.scene.addItem(cpu_panel)

        mem_panel = QGraphicsRectItem(580, 70, 480, 430)
        mem_panel.setBrush(QBrush(QColor("#d8d8d8")))
        mem_panel.setPen(QPen(QColor("#666"), 2))
        self.scene.addItem(mem_panel)

        # Titles
        t1 = QGraphicsSimpleTextItem("CPU")
        t1.setFont(QFont("Arial", 12, QFont.Bold))
        t1.setPos(30, 45)
        self.scene.addItem(t1)

        t2 = QGraphicsSimpleTextItem("Mémoire")
        t2.setFont(QFont("Arial", 12, QFont.Bold))
        t2.setPos(590, 75)
        self.scene.addItem(t2)

        # --- BUS ---
        self.bus_y = 585
        bus = QGraphicsLineItem(40, self.bus_y, 1040, self.bus_y)
        bus.setPen(QPen(QColor("#0b3d91"), 10))
        self.scene.addItem(bus)

        bus_label = QGraphicsSimpleTextItem("Bus")
        bus_label.setFont(QFont("Arial", 12, QFont.Bold))
        bus_label.setPos(1005, self.bus_y - 28)
        self.scene.addItem(bus_label)

        # Memory riser up from bus
        self.mem_riser_x = 820
        mem_riser = QGraphicsLineItem(self.mem_riser_x, self.bus_y, self.mem_riser_x, 505)
        mem_riser.setPen(QPen(QColor("#0b3d91"), 6))
        self.scene.addItem(mem_riser)

        # --- Blocks (same positions you already had) ---
        self.blocks["SEQ"] = Block(self.scene, 240, 55, 120, 50, "SEQ")

        self.blocks["ACC"] = Block(self.scene, 70, 175, 90, 60, "ACC")
        self.blocks["UAL"] = Block(self.scene, 160, 135, 140, 90, "UAL")
        self.blocks["DRAP"] = Block(self.scene, 200, 245, 90, 50, "Drap")

        self.blocks["RA"] = Block(self.scene, 520, 120, 70, 55, "RA")

        self.blocks["RI"] = Block(self.scene, 300, 350, 80, 135, "RI")
        self.blocks["CO"] = Block(self.scene, 395, 350, 80, 135, "CO")

        # Memory grid
        start_x, start_y = 600, 105
        cell_w, cell_h = 110, 28

        self.mem_cells = []
        for col in range(4):
            base = col * 10
            hdr = QGraphicsRectItem(start_x + col * cell_w, start_y - 22, cell_w, 20)
            hdr.setBrush(QBrush(QColor("#c9c9c9")))
            hdr.setPen(QPen(Qt.black, 1))
            self.scene.addItem(hdr)

            txt = QGraphicsSimpleTextItem(f"{base:02d}-{base+9:02d}", hdr)
            txt.setPos(hdr.rect().x() + 6, hdr.rect().y() + 2)
            txt.setFont(QFont("Arial", 9, QFont.Bold))

            for row in range(10):
                addr = base + row
                x = start_x + col * cell_w
                y = start_y + row * cell_h

                cell = QGraphicsRectItem(x, y, cell_w, cell_h)
                cell.setPen(QPen(Qt.black, 1))
                cell.setBrush(QBrush(Qt.white))
                cell.setZValue(1)
                self.scene.addItem(cell)

                t = QGraphicsSimpleTextItem("", cell)
                t.setPos(x + 6, y + 6)
                t.setFont(QFont("Consolas", 9))
                self.mem_cells.append((addr, cell, t))

        self.blocks["RM"] = Block(self.scene, 740, 520, 140, 55, "RM")

        # --- Organized routed arrows (NO block cutting) ---
        self.arrows = {}

        # define routing lanes (x coordinates) that stay clear of blocks
        lane_to_ra_x = 495       # just left of RA
        lane_mid_cpu_x = 250     # between ACC/UAL and RI/CO
        lane_regs_x = 350        # between RI and CO

        # CO -> RA (go up, across, then into RA bottom)
        co_src = self._top("CO")
        ra_dst = self._bottom("RA")
        self.arrows["CO->RA"] = RoutedArrow(self.scene, [
            co_src,
            (co_src[0], co_src[1] - 30),
            (lane_to_ra_x, co_src[1] - 30),
            (lane_to_ra_x, ra_dst[1] + 12),
            (ra_dst[0], ra_dst[1] + 12),
            ra_dst
        ], color="#1e88e5")

        # MEM -> RM (memory riser -> RM top, short clean)
        rm_top = self._top("RM")
        self.arrows["MEM->RM"] = RoutedArrow(self.scene, [
            (self.mem_riser_x, 520),
            (self.mem_riser_x, rm_top[1] - 10),
            (rm_top[0], rm_top[1] - 10),
            rm_top
        ], color="#1e88e5")

        # RM -> RI (RM left -> lane -> RI right)
        rm_left = self._left("RM")
        ri_right = self._right("RI")
        track_y = 485  # horizontal track above RM, below memory
        self.arrows["RM->RI"] = RoutedArrow(self.scene, [
            rm_left,
            (lane_regs_x, rm_left[1]),
            (lane_regs_x, track_y),
            (ri_right[0] + 10, track_y),
            (ri_right[0] + 10, ri_right[1]),
            ri_right
        ], color="#1e88e5")

        # RM -> ACC (use bus highway: RM -> bus -> ACC bottom)
        acc_bottom = self._bottom("ACC")
        self.arrows["RM->ACC"] = RoutedArrow(self.scene, [
            rm_left,
            (rm_left[0] - 25, rm_left[1]),
            (rm_left[0] - 25, self.bus_y),
            (acc_bottom[0], self.bus_y),
            acc_bottom
        ], color="#1e88e5")

        # ACC -> RM (use bus: ACC right -> bus -> RM bottom)
        acc_right = self._right("ACC")
        rm_bottom = self._bottom("RM")
        self.arrows["ACC->RM"] = RoutedArrow(self.scene, [
            acc_right,
            (acc_right[0] + 20, acc_right[1]),
            (acc_right[0] + 20, self.bus_y),
            (rm_bottom[0], self.bus_y),
            rm_bottom
        ], color="#e53935")

        # RM -> MEM (write): RM top -> across -> memory riser
        rm_top2 = self._top("RM")
        self.arrows["RM->MEM"] = RoutedArrow(self.scene, [
            rm_top2,
            (rm_top2[0], rm_top2[1] - 25),
            (self.mem_riser_x, rm_top2[1] - 25),
            (self.mem_riser_x, 520)
        ], color="#e53935")

        # OP -> RA (RI top -> lane -> RA left)
        ri_top = self._top("RI")
        ra_left = self._left("RA")
        self.arrows["OP->RA"] = RoutedArrow(self.scene, [
            ri_top,
            (ri_top[0], ri_top[1] - 25),
            (lane_to_ra_x, ri_top[1] - 25),
            (lane_to_ra_x, ra_left[1]),
            ra_left
        ], color="#43a047")

        # OP -> CO (RI top -> lane -> CO left)
        co_left = self._left("CO")
        self.arrows["OP->CO"] = RoutedArrow(self.scene, [
            ri_top,
            (ri_top[0], ri_top[1] - 25),
            (lane_regs_x, ri_top[1] - 25),
            (lane_regs_x, co_left[1]),
            co_left
        ], color="#43a047")

        # ALU -> ACC (short local route)
        ual_left = self._left("UAL")
        acc_top = self._top("ACC")
        self.arrows["ALU->ACC"] = RoutedArrow(self.scene, [
            ual_left,
            (ual_left[0] - 20, ual_left[1]),
            (ual_left[0] - 20, acc_top[1] - 10),
            (acc_top[0], acc_top[1] - 10),
            acc_top
        ], color="#8e24aa")

        # Put blocks above wires (already zValue=10 in Block; arrows are 5)
        # (memory cells are zValue=1)

    def refresh(self):
        # Update block values
        self.blocks["ACC"].set_value(self.cpu.ACC)
        self.blocks["CO"].set_value(self.cpu.CO)
        self.blocks["RI"].set_value(self.cpu.RI)
        self.blocks["RA"].set_value(self.cpu.RA)
        self.blocks["RM"].set_value(self.cpu.RM)
        self.blocks["DRAP"].set_value(self.cpu.DRAP)
        self.blocks["SEQ"].set_value(self.cpu.state.name)

        # Memory: highlight current RA
        for addr, cell, text in self.mem_cells:
            val = self.cpu.memory[addr]
            text.setText(f"{addr:02d}: {val}")
            if addr == self.cpu.RA:
                cell.setBrush(QBrush(QColor("#fff59d")))
            else:
                cell.setBrush(QBrush(Qt.white))

        # Clear highlights
        for a in self.arrows.values():
            a.set_hot(False)
        for b in self.blocks.values():
            b.highlight(False)

        # Active transfer
        t = self.cpu.last_transfer
        if t in self.arrows:
            self.arrows[t].set_hot(True)

        # Block highlight mapping
        if t == "CO->RA":
            self.blocks["CO"].highlight(True)
            self.blocks["RA"].highlight(True)
        elif t == "MEM->RM":
            self.blocks["RM"].highlight(True)
        elif t == "RM->RI":
            self.blocks["RM"].highlight(True)
            self.blocks["RI"].highlight(True)
        elif t == "RM->ACC":
            self.blocks["RM"].highlight(True)
            self.blocks["ACC"].highlight(True)
        elif t == "ACC->RM":
            self.blocks["ACC"].highlight(True)
            self.blocks["RM"].highlight(True)
        elif t == "RM->MEM":
            self.blocks["RM"].highlight(True)
        elif t == "OP->RA":
            self.blocks["RI"].highlight(True, "#c8e6c9")
            self.blocks["RA"].highlight(True, "#c8e6c9")
        elif t == "OP->CO":
            self.blocks["RI"].highlight(True, "#c8e6c9")
            self.blocks["CO"].highlight(True, "#c8e6c9")
        elif t == "ALU->ACC":
            self.blocks["UAL"].highlight(True, "#e1bee7")
            self.blocks["ACC"].highlight(True, "#e1bee7")

        # Status
        if self.cpu.halted:
            self.status.setText("ARRÊT DU PROGRAMME (99)")
            self.step_btn.setEnabled(False)
        else:
            self.status.setText(f"État: {self.cpu.state.name}")
            self.step_btn.setEnabled(True)

        self.detail.setText(self.cpu.last_detail)

    def on_step(self):
        self.cpu.step()
        self.refresh()

    def on_reset(self):
        self.timer.stop()
        self.run_btn.setText("Auto (run/stop)")
        self.cpu.reset()
        self.refresh()

    def on_toggle_run(self):
        if self.timer.isActive():
            self.timer.stop()
            self.run_btn.setText("Auto (run/stop)")
        else:
            self.timer.start()
            self.run_btn.setText("Stop")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = MainWindow()
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())