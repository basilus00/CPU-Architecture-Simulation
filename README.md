# CPU Architecture Simulation — Elementary Machine (Qt + Python)

This repository contains **two educational CPU simulators**:

1) **`machine_sim_qt.py`** — a **step‑by‑step visual simulator** (PySide6 / Qt) that reproduces the “machine élémentaire” style used in computer architecture courses (FETCH → DECODE → EXECUTE), highlighting transfers between **CO, RI, RA, RM, ACC, UAL, SEQ** and the memory grid.

2) **`simpleCPU.py`** — a **console CPU simulator** (register machine) that demonstrates the classic **fetch → decode → execute** cycle with an ALU and a Zero flag.

The goal is to help students understand **how a CPU executes instructions** and how values move between registers, memory, and the ALU.

---

## Contents

- [`machine_sim_qt.py`](./machine_sim_qt.py) — Qt GUI simulator (blue theme, step log, memory grid)
- [`simpleCPU.py`](./simpleCPU.py) — console CPU (R1..R4, memory[0..15], branching)
- [`Qwen_html_20260425_1zdw71sdp.html`](./Qwen_html_20260425_1zdw71sdp.html) — original HTML/canvas prototype (reference)
  
![html_GUI Screenshot](docs/html.png)

---

## 1) GUI Simulator (Qt) — `machine_sim_qt.py`

### What it shows
The GUI simulates an **elementary machine** using micro‑steps. You can run one micro‑step at a time and see:

- **Phase tag**: `CHERCHER` (Fetch), `DÉCODER` (Decode), `EXÉCUTER` (Execute)
- **Flow description**: human‑readable explanation of the current transfer
- **Bus bar**: highlights when a transfer uses the bus
- **CPU blocks** (left):
  - `SEQ` — Sequencer / control
  - `UAL` — ALU
  - `ACC` — accumulator
  - `RI` — instruction register
  - `CO` — program counter
  - `RA` — address register
- **Memory** (right): grid of addresses (default view shows 0..19)
- **RM** — memory buffer register (displayed under memory)
- **Execution log**: list of all micro‑steps, highlighting the current one

### Instruction format
Instructions are stored as **4 digits**:
- `opcode = instr // 100`
- `operand = instr % 100`

Supported opcodes (as implemented in the step builder):

| Opcode | Name  | Meaning |
|------:|-------|---------|
| 10 | LOAD  | `ACC ← MEM[operand]` |
| 20 | STORE | `MEM[operand] ← ACC` |
| 30 | ADD   | `ACC ← ACC + MEM[operand]` |
| 50 | JUMP  | `CO ← operand` |
| 99 | HALT  | Stop |

### Default demo program (preloaded)
Memory is initialized with a small example:

- `1010` (LOAD from address 10)
- `3011` (ADD address 11)
- `2012` (STORE into address 12)
- `5005` (JUMP to address 5, for demonstration)
- `99` (HALT)

And sample data:
- `MEM[10] = 23`
- `MEM[11] = 14`

Expected result: after executing LOAD + ADD + STORE, **37** should be written to `MEM[12]`.

### Run the GUI
![GUI Screenshot](docs/gui.png)
#### Requirements
- Python **3.9+**
- PySide6 (Qt bindings)

Install:
```bash
pip install PySide6
```

Run:
```bash
python machine_sim_qt.py
```

### Controls
- **↺ Réinitialiser**: reset memory/registers and rebuild the step list
- **Étape suivante →**: advance exactly one micro‑step
- **▶ Auto** / **■ Stop**: auto-run through micro‑steps with a timer

### Customization
- Change initial memory/program: edit `MEM_INIT` in `machine_sim_qt.py`
- Adjust the micro‑step sequence: edit `build_steps()` in `machine_sim_qt.py`
- Show all memory cells (0..39): change `visible_addrs = list(range(0, 20))` to `range(0, 40)` (or implement scrolling)
- Theme: modify the `THEME` stylesheet string

---

## 2) Console CPU (Register Machine) — `simpleCPU.py`

### What it simulates
A small register machine with:

- Registers: `R1, R2, R3, R4`
- Memory: `memory[0..15]`
- `pc` (program counter)
- `ir` (instruction register)
- `alu_temp` (temporary ALU storage)
- `zero_flag` (used by `JZ`)

### Supported instructions
Instructions are tuples like `("MOV", "R1", 2)`:

| Instruction | Example | Meaning |
|------------|---------|---------|
| MOV | `("MOV","R1",2)` | load immediate/register into destination |
| ADD | `("ADD","R1","R2")` | `R1 ← R1 + R2` |
| SUB | `("SUB","R1","R2")` | `R1 ← R1 - R2` |
| LOAD | `("LOAD","R1",0)` | `R1 ← memory[0]` |
| STORE | `("STORE","R1",0)` | `memory[0] ← R1` |
| JMP | `("JMP",3)` | `pc ← 3` |
| JZ | `("JZ",7)` | if Zero flag true, `pc ← 7` |
| HALT | `("HALT",)` | stop |

### Run the console CPU
```bash
python simpleCPU.py
```

It prints:
- FETCH / DECODE / EXECUTE messages
- register and memory state after each instruction
- a 1-second pause per cycle for readability (`time.sleep(1)`)

---

## Troubleshooting

### `ModuleNotFoundError: No module named 'PySide6'`
PySide6 is installed in a different environment than the interpreter you’re using to run the program.

Fix:
```bash
python -m pip install PySide6
python -c "import PySide6; print(PySide6.__version__)"
```

In VS Code: select the correct Python interpreter (`Ctrl+Shift+P` → “Python: Select Interpreter”).

---

## Roadmap / Ideas
- Add routed arrows and full schematic diagram wiring (PDF-like)
- Add explicit DRAP/flags behavior in the GUI simulator
- Add additional opcodes (SUB, conditional jumps)
- Export step traces to a file (for assignments / grading)

---
