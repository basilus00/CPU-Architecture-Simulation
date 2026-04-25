import time
class CPU:
    def __init__(self):
        # Registers
        self.registers = {
            "R1": 0,
            "R2": 0,
            "R3": 0,
            "R4": 0
        }
        self.memory = [0] * 16  # Simple memory with 16 addresses
        self.pc = 0  #points to the next instruction in the program
        self.ir = None #current instruction being executed
        self.alu_temp = 0 
        self.zero_flag = False #flag register with only one flag for simplicity (Zero Flag)
        #State of the CPU 
        self.running = True
        self.program = []

    def load_program(self, program_code):
        """Charging the program into the CPU's memory."""
        self.program = program_code
        self.pc = 0
        self.running = True
        self.ir = None
        #initialization of memory and registers for a clean state
        self.memory = [0] * 16
        for k in self.registers: self.registers[k] = 0

    def fetch(self):
        """1. FETCH: getting the next instruction from memory."""
        if self.pc < len(self.program):
            self.ir = self.program[self.pc]
            print(f"[FETCH]    PC={self.pc} -> Instruction in charge: {self.ir}")
            self.pc += 1
        else:
            self.running = False
    def decode_and_execute(self):
        """2. DECODE & 3. EXECUTE: interpreting and executing the instruction."""
        if not self.ir: return
        opcode = self.ir[0]
        print(f"[DECODE]   Operation detected is: {opcode}")

        #  ADD R1, R2 (ALU)
        if opcode == "ADD":
            dest = self.ir[1]
            src = self.ir[2]
            val1 = self.registers[dest]
            val2 = self.registers[src] if isinstance(src, str) else self.registers[src] #support for immediate values if src is an integer
            print(f"[EXECUTE]  -> sending values {val1} and {val2} to ALU")
            self.alu_temp = val1 + val2 
            print(f"           [ALU] Calculating : {val1} + {val2} = {self.alu_temp}")

            self.registers[dest] = self.alu_temp
            self.zero_flag = (self.alu_temp == 0)
            print(f"           Storing results in  {dest}.")

        # SUB R1, R2 (ALU)
        elif opcode == "SUB":
            dest = self.ir[1]
            src = self.ir[2]
            val1 = self.registers[dest]
            val2 = self.registers[src]

            print(f"[EXECUTE]  -> Sending values {val1} and {val2} to ALU.")
            self.alu_temp = val1 - val2
            print(f"           [ALU] Calculating : {val1} - {val2} = {self.alu_temp}")
            
            self.registers[dest] = self.alu_temp
            self.zero_flag = (self.alu_temp == 0)
            print(f"           Storing results in  {dest}.")

        # MOV R1, Value or register
        elif opcode == "MOV":
            dest = self.ir[1]
            src = self.ir[2]
            value = src if isinstance(src, int) else self.registers[src] #support for immediate values if src is an integer
            self.registers[dest] = value
            print(f"[EXECUTE]  MOV: {dest} <- {value}")

        # STORE R1, Adresse
        elif opcode == "STORE":
            reg_src = self.ir[1]
            mem_addr = self.ir[2]
            print(f"[EXECUTE]  STORE: Writing Register({reg_src}) -> Memory[{mem_addr}]")
            self.memory[mem_addr] = self.registers[reg_src]

        #LOAD R1, Adresse
        elif opcode == "LOAD":
            dest_reg = self.ir[1]
            mem_addr = self.ir[2]
            print(f"[EXECUTE]  LOAD: Reading Memory[{mem_addr}] -> Register({dest_reg})")
            self.registers[dest_reg] = self.memory[mem_addr]

        # JMP Adresse 
        elif opcode == "JMP":
            addr = self.ir[1]
            print(f"[EXECUTE]  JMP: {addr}")
            self.pc = addr

        # JZ Adresse 
        elif opcode == "JZ":
            addr = self.ir[1]
            if self.zero_flag:
                print(f"[EXECUTE]  JZ: flag zero detected jumping to  {addr}")
                self.pc = addr
            else:
                print(f"[EXECUTE]  JZ: flag zero not detected, continue to next instruction.")

        # HALT 
        elif opcode == "HALT":
            self.running = False
            print("[EXECUTE]  HALT: Stopping the CPU.")

        else:
            print(f"[ERROR] unknown instruction {opcode}")
            self.running = False

    def run(self):
        print("=== Starting CPU simulation===")
        print("-" * 50)
        
        while self.running:
            self.fetch()
            if self.running:
                self.decode_and_execute()
            self.display_state()
        print("=== END of execution ===")

    def display_state(self):
        print(f"\n REGISTRES: {self.registers}")
        print(f" MEMORY:   {self.memory}")
        print(f" FLAGS:     Zero={self.zero_flag}")
        print("-" * 50)
        time.sleep(1) 

# Test program
program = [
    ("MOV", "R1", 2),      # 0: R1 = 2 (Counter)
    ("MOV", "R2", 1),      # 1: R2 = 1 
    ("MOV", "R3", 99),     # 2: R3 = 99 
    ("SUB", "R1", "R2"),   # 3: R1 = R1 - R2 (ALU active)
    ("STORE", "R1", 0),    # 4: Saving R1 in memory[0] for observation
    ("JZ",  7),            # 5: If R1 == 0, jump to 7 (End)
    ("JMP", 3),            # 6: else returning to instruction 3
    ("HALT",)              # 7: HALT
]

# Launching the CPU simulation with the test program
cpu = CPU()
cpu.load_program(program)
cpu.run()