"""
COA Module: Micro-Operations & T-State Instruction Cycle Engine
Breaks down instructions into standard educational clock cycles (T0 - T6)
using Register Transfer Notation (RTL).
"""

from typing import Dict, Any, Optional


class MicroOpStage:
    T0_FETCH_MAR = "T0"      # MAR <- PC
    T1_FETCH_MDR = "T1"      # MDR <- M[MAR], PC <- PC + 1
    T2_FETCH_IR  = "T2"      # IR <- MDR
    T3_DECODE    = "T3"      # Control Unit Decode Opcode & Operands
    T4_EXECUTE   = "T4"      # ALU / Address Computation / Condition Check
    T5_MEMORY    = "T5"      # Memory Read/Write (if memory instruction)
    T6_WRITEBACK = "T6"      # Register Writeback & Flag Update

    ORDER = [T0_FETCH_MAR, T1_FETCH_MDR, T2_FETCH_IR, T3_DECODE, T4_EXECUTE, T5_MEMORY, T6_WRITEBACK]


def describe_micro_op(stage: str, instruction: Optional[Any], cpu_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Produces a detailed Register Transfer Notation (RTL) description
    and active bus indicators for the given T-state.
    """
    pc = cpu_state.get("PC", 0)
    mar = cpu_state.get("MAR", 0)
    mdr = cpu_state.get("MDR", 0)
    ir = instruction.raw_assembly if instruction else "NOP"
    mnemonic = instruction.mnemonic if instruction else "NOP"

    if stage == MicroOpStage.T0_FETCH_MAR:
        return {
            "t_state": "T0",
            "phase": "FETCH",
            "rtl": f"MAR ← PC (MAR = 0x{pc:02X})",
            "description": "Place Program Counter on Address Bus; load Memory Address Register.",
            "active_buses": ["ADDRESS_BUS"],
            "bus_data": {"address_bus": f"0x{pc:02X}", "data_bus": None, "control_bus": "MEM_READ_WAIT"}
        }

    elif stage == MicroOpStage.T1_FETCH_MDR:
        return {
            "t_state": "T1",
            "phase": "FETCH",
            "rtl": f"MDR ← M[MAR], PC ← PC + 1 (PC = 0x{pc+1:02X})",
            "description": "Read machine word from RAM into MDR; simultaneously increment PC.",
            "active_buses": ["DATA_BUS", "CONTROL_BUS"],
            "bus_data": {"address_bus": f"0x{mar:02X}", "data_bus": f"0x{mdr & 0xFFFFFFFF:08X}", "control_bus": "MEM_READ"}
        }

    elif stage == MicroOpStage.T2_FETCH_IR:
        return {
            "t_state": "T2",
            "phase": "FETCH",
            "rtl": "IR ← MDR",
            "description": f"Transfer fetched instruction into Instruction Register: '{ir}'.",
            "active_buses": ["INTERNAL_BUS"],
            "bus_data": {"address_bus": None, "data_bus": f"0x{mdr & 0xFFFFFFFF:08X}", "control_bus": "IR_LATCH"}
        }

    elif stage == MicroOpStage.T3_DECODE:
        rd = instruction.rd if instruction else "-"
        rs1 = instruction.rs1 if instruction else "-"
        rs2 = instruction.rs2 if instruction else "-"
        imm = instruction.imm if instruction else 0
        return {
            "t_state": "T3",
            "phase": "DECODE",
            "rtl": f"CU_DECODE(IR) → Opcode: {mnemonic}, Rd: {rd}, Rs1: {rs1}, Rs2: {rs2}, Imm: {imm}",
            "description": "Control Unit decodes opcode, asserts internal control lines, reads source registers.",
            "active_buses": ["CONTROL_BUS"],
            "bus_data": {"address_bus": None, "data_bus": None, "control_bus": f"CTRL_OP_{mnemonic}"}
        }

    elif stage == MicroOpStage.T4_EXECUTE:
        # ALU operation description based on mnemonic
        if mnemonic in ("ADD", "ADDI"):
            rtl = "ALU_OUT ← Rs1 + (Rs2 or Imm)"
            desc = "ALU performs 32-bit addition."
        elif mnemonic in ("SUB", "SUBI"):
            rtl = "ALU_OUT ← Rs1 - (Rs2 or Imm)"
            desc = "ALU performs two's complement subtraction."
        elif mnemonic == "MUL":
            rtl = "ALU_OUT ← Rs1 × Rs2"
            desc = "ALU multiplier performs integer product."
        elif mnemonic in ("DIV", "MOD"):
            rtl = "ALU_OUT ← Rs1 / Rs2"
            desc = "ALU divider performs integer quotient/modulo."
        elif mnemonic in ("CMP", "CMPI"):
            rtl = "ALU_TEMP ← Rs1 - Rs2; Update Condition Flags"
            desc = "ALU subtracts operands to evaluate Zero, Sign, and Carry flags without altering registers."
        elif mnemonic.startswith("J"):
            rtl = f"Branch Evaluation for {mnemonic}"
            desc = "Condition logic checks flags to determine branch target address."
        elif mnemonic in ("LOAD", "STORE"):
            rtl = f"MAR ← Effective Address ({instruction.imm})"
            desc = "Load target memory address into MAR."
        elif mnemonic == "LDI":
            rtl = f"ALU_OUT ← Imm ({instruction.imm})"
            desc = "Immediate value latched into execution buffer."
        else:
            rtl = "ALU_NOP"
            desc = "No execution micro-operation required."

        return {
            "t_state": "T4",
            "phase": "EXECUTE",
            "rtl": rtl,
            "description": desc,
            "active_buses": ["INTERNAL_ALU_BUS"],
            "bus_data": {"address_bus": None, "data_bus": None, "control_bus": "ALU_ACTIVE"}
        }

    elif stage == MicroOpStage.T5_MEMORY:
        if mnemonic == "LOAD":
            addr = instruction.imm
            return {
                "t_state": "T5",
                "phase": "MEMORY",
                "rtl": f"MDR ← M[MAR] (Read address 0x{addr:02X})",
                "description": "Access RAM to read data value into MDR.",
                "active_buses": ["ADDRESS_BUS", "DATA_BUS", "CONTROL_BUS"],
                "bus_data": {"address_bus": f"0x{addr:02X}", "data_bus": "DATA_IN", "control_bus": "MEM_READ"}
            }
        elif mnemonic == "STORE":
            addr = instruction.imm
            rs_val = cpu_state.get("registers", {}).get(instruction.rs1, 0)
            return {
                "t_state": "T5",
                "phase": "MEMORY",
                "rtl": f"M[MAR] ← MDR (Write {rs_val} to 0x{addr:02X})",
                "description": "Write data from MDR to RAM at address held in MAR.",
                "active_buses": ["ADDRESS_BUS", "DATA_BUS", "CONTROL_BUS"],
                "bus_data": {"address_bus": f"0x{addr:02X}", "data_bus": str(rs_val), "control_bus": "MEM_WRITE"}
            }
        else:
            return {
                "t_state": "T5",
                "phase": "MEMORY",
                "rtl": "NOP (No memory bus cycle needed)",
                "description": "Memory bus idle for register-register instruction.",
                "active_buses": [],
                "bus_data": {"address_bus": None, "data_bus": None, "control_bus": "IDLE"}
            }

    elif stage == MicroOpStage.T6_WRITEBACK:
        rd = instruction.rd if instruction else "-"
        return {
            "t_state": "T6",
            "phase": "WRITEBACK",
            "rtl": f"{rd} ← RESULT; Update Status Flags [ZF, SF, CF, OF]",
            "description": "Latching output into destination register and updating processor status flags.",
            "active_buses": ["INTERNAL_BUS"],
            "bus_data": {"address_bus": None, "data_bus": None, "control_bus": "REG_WRITE"}
        }

    return {"t_state": stage, "phase": "UNKNOWN", "rtl": "", "description": "", "active_buses": [], "bus_data": {}}
