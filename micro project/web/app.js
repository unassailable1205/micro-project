/**
 * Smart Code Analyzer & Execution Simulator Frontend Application
 * Handles API interaction, UI tab switching, simulation stepping,
 * DFA table rendering, and recursion tree visualization.
 */

// Application State
const state = {
  presets: [],
  dfaTables: {},
  currentDfa: 'identifier',
  currentDnc: 'fastpow',
  runningInterval: null,
  clockSpeedMs: 400,
  cpuHalted: false,
};

// DOM Elements
const el = {
  presetSelect: document.getElementById('preset-select'),
  sourceEditor: document.getElementById('source-editor'),
  codeLineCount: document.getElementById('code-line-count'),
  assemblyViewer: document.getElementById('assembly-viewer'),
  asmInstrCount: document.getElementById('asm-instr-count'),
  machineWordsList: document.getElementById('machine-words-list'),
  consoleOutput: document.getElementById('console-output'),
  btnClearConsole: document.getElementById('btn-clear-console'),

  btnAnalyze: document.getElementById('btn-analyze'),
  btnStepMicro: document.getElementById('btn-step-micro'),
  btnStepInstr: document.getElementById('btn-step-instr'),
  btnRun: document.getElementById('btn-run'),
  btnPause: document.getElementById('btn-pause'),
  btnReset: document.getElementById('btn-reset'),
  speedRange: document.getElementById('speed-range'),
  speedLabel: document.getElementById('speed-label'),

  // COA Elements
  rtlText: document.getElementById('current-rtl-text'),
  pillAddr: document.getElementById('pill-addr'),
  pillData: document.getElementById('pill-data'),
  pillCtrl: document.getElementById('pill-ctrl'),
  regR0: document.getElementById('reg-R0'),
  regR1: document.getElementById('reg-R1'),
  regR2: document.getElementById('reg-R2'),
  regR3: document.getElementById('reg-R3'),
  regPC: document.getElementById('reg-PC'),
  regMAR: document.getElementById('reg-MAR'),
  regMDR: document.getElementById('reg-MDR'),
  regSP: document.getElementById('reg-SP'),
  regIRText: document.getElementById('reg-IR-text'),
  flagZF: document.getElementById('flag-ZF'),
  flagSF: document.getElementById('flag-SF'),
  flagCF: document.getElementById('flag-CF'),
  flagOF: document.getElementById('flag-OF'),
  statCycles: document.getElementById('stat-cycles'),
  statInstrs: document.getElementById('stat-instrs'),
  statStatus: document.getElementById('stat-status'),
  memoryTbody: document.getElementById('memory-tbody'),

  // FLAT Elements
  flatTokenCount: document.getElementById('flat-token-count'),
  tokensTbody: document.getElementById('tokens-tbody'),
  dfaTableContainer: document.getElementById('dfa-table-container'),
  astJson: document.getElementById('ast-json'),

  // DAA Elements
  daaTimeVal: document.getElementById('daa-time-val'),
  daaTimeDesc: document.getElementById('daa-time-desc'),
  daaSpaceVal: document.getElementById('daa-space-val'),
  daaSpaceDesc: document.getElementById('daa-space-desc'),
  daaLoopVal: document.getElementById('daa-loop-val'),
  daaVarsVal: document.getElementById('daa-vars-val'),
  mtA: document.getElementById('mt-a'),
  mtB: document.getElementById('mt-b'),
  mtK: document.getElementById('mt-k'),
  mtP: document.getElementById('mt-p'),
  btnSolveMt: document.getElementById('btn-solve-mt'),
  mtBound: document.getElementById('mt-bound'),
  mtExplanation: document.getElementById('mt-explanation'),

  benchNaiveName: document.getElementById('bench-naive-name'),
  benchNaiveInstr: document.getElementById('bench-naive-instr'),
  benchNaiveCycles: document.getElementById('bench-naive-cycles'),
  benchDncName: document.getElementById('bench-dnc-name'),
  benchDncInstr: document.getElementById('bench-dnc-instr'),
  benchDncCycles: document.getElementById('bench-dnc-cycles'),
  benchSpeedup: document.getElementById('bench-speedup'),
  benchReduction: document.getElementById('bench-reduction'),
  treeCanvas: document.getElementById('tree-canvas'),
};

// =========================================================
// Initialization
// =========================================================
document.addEventListener('DOMContentLoaded', async () => {
  setupNavigationTabs();
  setupEventListeners();
  await loadPresets();
  await loadDfaTables();
  await solveMasterTheorem();
  await loadDivideAndConquerTree('fastpow');

  // Trigger initial compilation of default preset
  if (el.presetSelect.value) {
    handleAnalyze();
  }
});

function setupNavigationTabs() {
  // Left sub-tabs (Source Code / Assembly / Machine Words)
  document.querySelectorAll('.sub-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.sub-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.sub-pane').forEach(p => p.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.tab).classList.add('active');
    });
  });

  // Right module views (COA / FLAT / DAA)
  document.querySelectorAll('.module-tab').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.module-tab').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.module-view').forEach(v => v.classList.remove('active'));
      btn.classList.add('active');
      document.getElementById(btn.dataset.view).classList.add('active');
    });
  });

  // DFA Selector pills
  document.querySelectorAll('.dfa-selector-pills .pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.dfa-selector-pills .pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.currentDfa = pill.dataset.dfa;
      renderDfaTable(state.currentDfa);
    });
  });

  // D&C Tree pills
  document.querySelectorAll('.tree-controls .pill').forEach(pill => {
    pill.addEventListener('click', () => {
      document.querySelectorAll('.tree-controls .pill').forEach(p => p.classList.remove('active'));
      pill.classList.add('active');
      state.currentDnc = pill.dataset.dnc;
      loadDivideAndConquerTree(state.currentDnc);
    });
  });
}

function setupEventListeners() {
  el.presetSelect.addEventListener('change', onPresetChange);
  el.btnAnalyze.addEventListener('click', handleAnalyze);
  el.btnStepMicro.addEventListener('click', handleStepMicro);
  el.btnStepInstr.addEventListener('click', handleStepInstr);
  el.btnRun.addEventListener('click', handleRun);
  el.btnPause.addEventListener('click', handlePause);
  el.btnReset.addEventListener('click', handleReset);
  el.btnClearConsole.addEventListener('click', () => { el.consoleOutput.innerHTML = ''; });

  el.speedRange.addEventListener('input', (e) => {
    state.clockSpeedMs = parseInt(e.target.value, 10);
    el.speedLabel.textContent = `${state.clockSpeedMs}ms`;
    if (state.runningInterval) {
      clearInterval(state.runningInterval);
      state.runningInterval = setInterval(handleStepInstr, state.clockSpeedMs);
    }
  });

  el.btnSolveMt.addEventListener('click', solveMasterTheorem);

  el.sourceEditor.addEventListener('input', () => {
    const lines = el.sourceEditor.value.split('\n').length;
    el.codeLineCount.textContent = `${lines} Line${lines > 1 ? 's' : ''}`;
  });
}

// =========================================================
// API Calls & Data Fetching
// =========================================================
async function loadPresets() {
  try {
    const res = await fetch('/api/presets');
    const data = await res.json();
    state.presets = data.presets || [];
    el.presetSelect.innerHTML = '';
    state.presets.forEach((p, idx) => {
      const opt = document.createElement('option');
      opt.value = p.id;
      opt.textContent = p.title;
      el.presetSelect.appendChild(opt);
    });
    if (state.presets.length > 0) {
      el.sourceEditor.value = state.presets[0].code;
      const lines = state.presets[0].code.split('\n').length;
      el.codeLineCount.textContent = `${lines} Lines`;
    }
  } catch (err) {
    logConsole(`Failed to load presets: ${err.message}`, 'error');
  }
}

function onPresetChange() {
  const selectedId = el.presetSelect.value;
  const p = state.presets.find(item => item.id === selectedId);
  if (p) {
    el.sourceEditor.value = p.code;
    const lines = p.code.split('\n').length;
    el.codeLineCount.textContent = `${lines} Lines`;
    handleAnalyze();
  }
}

async function loadDfaTables() {
  try {
    const res = await fetch('/api/dfa/tables');
    state.dfaTables = await res.json();
    renderDfaTable(state.currentDfa);
  } catch (err) {
    logConsole(`Failed to load DFA tables: ${err.message}`, 'error');
  }
}

function renderDfaTable(dfaKey) {
  const tableData = state.dfaTables[dfaKey];
  if (!tableData) return;

  let html = `<table class="data-table"><thead><tr><th>State</th>`;
  tableData.alphabet.forEach(sym => {
    html += `<th>${sym}</th>`;
  });
  html += `</tr></thead><tbody>`;

  tableData.rows.forEach(r => {
    const isStart = r.is_start ? '👉 ' : '';
    const isAccept = r.is_accept ? ' ★' : '';
    const stateLabel = `${isStart}${r.state}${isAccept}`;
    html += `<tr><td><strong>${stateLabel}</strong></td>`;
    tableData.alphabet.forEach(sym => {
      const target = r.transitions[sym] || '-';
      html += `<td>${target}</td>`;
    });
    html += `</tr>`;
  });
  html += `</tbody></table>`;
  el.dfaTableContainer.innerHTML = html;
}

// =========================================================
// Main Analyze & Compile Workflow
// =========================================================
async function handleAnalyze() {
  const source = el.sourceEditor.value;
  logConsole('Starting Lexical (FLAT), Syntax (AST), and Architecture (COA) analysis...', 'system');

  try {
    const res = await fetch('/api/analyze', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_code: source }),
    });

    const data = await res.json();

    if (!res.ok) {
      logConsole(`[${data.stage || 'ERROR'}]: ${data.error} at line ${data.line || '?'}, col ${data.column || '?'}`, 'error');
      alert(`Analysis Error:\n${data.error}`);
      return;
    }

    // 1. Update FLAT Token Stream & AST
    renderTokens(data.flat.tokens);
    el.flatTokenCount.textContent = `${data.flat.token_count} Tokens`;
    el.astJson.textContent = JSON.stringify(data.flat.ast, null, 2);

    // 2. Update COA Assembly & Machine Words
    el.assemblyViewer.textContent = data.coa.assembly;
    el.asmInstrCount.textContent = `${data.coa.instruction_count} Instructions`;
    renderMachineWords(data.coa.instructions);

    // 3. Update COA CPU & RAM
    updateCpuDisplay(data.coa.cpu_state);
    renderMemory(data.coa.memory_dump, data.coa.cpu_state.PC, data.coa.cpu_state.MAR);

    // 4. Update DAA Complexity
    updateDaaMetrics(data.daa);

    logConsole(`Analysis Succeeded! Compiled ${data.coa.instruction_count} instructions. Complexity: ${data.daa.time_complexity}`, 'stdout');
  } catch (err) {
    logConsole(`Network or Server error: ${err.message}`, 'error');
  }
}

function renderTokens(tokens) {
  if (!tokens || tokens.length === 0) {
    el.tokensTbody.innerHTML = `<tr><td colspan="4" class="placeholder-text">No tokens found.</td></tr>`;
    return;
  }

  let html = '';
  tokens.forEach(tok => {
    const traceSummary = (tok.dfa_trace || [])
      .map(t => `${t.from_state}→(${t.char})→${t.to_state}`)
      .join(', ') || 'N/A';

    html += `<tr>
      <td><span class="badge ${getBadgeClass(tok.type)}">${tok.type}</span></td>
      <td><strong>${escapeHtml(tok.value)}</strong></td>
      <td>Line ${tok.line}, Col ${tok.column}</td>
      <td style="font-size:11px; color:#9aa7b8;">${traceSummary}</td>
    </tr>`;
  });
  el.tokensTbody.innerHTML = html;
}

function getBadgeClass(type) {
  if (type === 'KEYWORD') return 'flat-badge';
  if (type === 'IDENTIFIER') return 'coa-badge';
  if (type === 'INTEGER' || type === 'FLOAT') return 'daa-badge';
  return 'badge-ready';
}

function renderMachineWords(instructions) {
  if (!instructions || instructions.length === 0) {
    el.machineWordsList.innerHTML = `<p class="placeholder-text">No instructions assembled.</p>`;
    return;
  }

  let html = `<table class="data-table"><thead><tr>
    <th>Addr</th><th>Mnemonic</th><th>Hex</th><th>Binary (32-Bit Formatted)</th>
  </tr></thead><tbody>`;

  instructions.forEach(ins => {
    html += `<tr>
      <td>0x${ins.address.toString(16).padStart(2, '0').toUpperCase()}</td>
      <td><strong>${ins.assembly}</strong></td>
      <td style="color:#f0883e;">${ins.hex}</td>
      <td style="color:#39c5cf; font-size:11px;">${ins.binary}</td>
    </tr>`;
  });
  html += `</tbody></table>`;
  el.machineWordsList.innerHTML = html;
}

// =========================================================
// CPU Simulator Controls (COA Module)
// =========================================================
async function handleStepMicro() {
  try {
    const res = await fetch('/api/cpu/step_micro', { method: 'POST' });
    const data = await res.json();
    if (data.halted && data.message) {
      logConsole(`CPU Execution Complete: ${data.message}`, 'system');
      handlePause();
      return;
    }
    updateTStatePipeline(data.t_state);
    el.rtlText.textContent = data.rtl || 'NOP';
    updateBuses(data.active_buses || []);
    if (data.cpu_state) {
      updateCpuDisplay(data.cpu_state);
      renderMemory(data.memory_dump, data.cpu_state.PC, data.cpu_state.MAR);
    }
    logConsole(`[${data.t_state}]: ${data.rtl} | ${data.description}`, 'micro');
  } catch (err) {
    logConsole(`Step Micro error: ${err.message}`, 'error');
  }
}

async function handleStepInstr() {
  try {
    const res = await fetch('/api/cpu/step_instruction', { method: 'POST' });
    const data = await res.json();
    if (data.halted) {
      logConsole(`CPU Halted. Total cycles: ${data.cpu_state?.clock_cycles}`, 'system');
      handlePause();
    }
    if (data.cpu_state) {
      updateCpuDisplay(data.cpu_state);
      renderMemory(data.memory_dump, data.cpu_state.PC, data.cpu_state.MAR);
    }
    // Update T-state pipeline to T0
    updateTStatePipeline('T0');
    el.rtlText.textContent = `Completed Instruction: ${data.instruction}`;
    logConsole(`Executed Instruction: ${data.instruction}`, 'stdout');
  } catch (err) {
    logConsole(`Step Instruction error: ${err.message}`, 'error');
    handlePause();
  }
}

function handleRun() {
  if (state.runningInterval) return;
  el.btnRun.style.display = 'none';
  el.btnPause.style.display = 'inline-flex';
  logConsole('Running CPU simulation continuously...', 'system');
  state.runningInterval = setInterval(handleStepInstr, state.clockSpeedMs);
}

function handlePause() {
  if (state.runningInterval) {
    clearInterval(state.runningInterval);
    state.runningInterval = null;
  }
  el.btnRun.style.display = 'inline-flex';
  el.btnPause.style.display = 'none';
  logConsole('CPU simulation paused.', 'system');
}

async function handleReset() {
  handlePause();
  try {
    const res = await fetch('/api/cpu/reset', { method: 'POST' });
    const data = await res.json();
    updateCpuDisplay(data.cpu_state);
    renderMemory(data.memory_dump, data.cpu_state.PC, data.cpu_state.MAR);
    updateTStatePipeline('T0');
    el.rtlText.textContent = 'MAR ← PC';
    updateBuses([]);
    logConsole('CPU and RAM have been reset.', 'system');
  } catch (err) {
    logConsole(`Reset error: ${err.message}`, 'error');
  }
}

function updateTStatePipeline(activeT) {
  document.querySelectorAll('.t-state-node').forEach(node => {
    if (node.dataset.t === activeT) {
      node.classList.add('active');
    } else {
      node.classList.remove('active');
    }
  });
}

function updateBuses(activeBuses) {
  el.pillAddr.classList.toggle('active', activeBuses.includes('ADDRESS_BUS'));
  el.pillData.classList.toggle('active', activeBuses.includes('DATA_BUS'));
  el.pillCtrl.classList.toggle('active', activeBuses.includes('CONTROL_BUS') || activeBuses.includes('INTERNAL_BUS'));
}

function updateCpuDisplay(cpu) {
  if (!cpu) return;

  // General Purpose Registers
  updateRegisterVal(el.regR0, cpu.registers.R0);
  updateRegisterVal(el.regR1, cpu.registers.R1);
  updateRegisterVal(el.regR2, cpu.registers.R2);
  updateRegisterVal(el.regR3, cpu.registers.R3);

  // Special Registers
  updateRegisterVal(el.regPC, cpu.PC);
  updateRegisterVal(el.regMAR, cpu.MAR);
  updateRegisterVal(el.regMDR, cpu.MDR);
  updateRegisterVal(el.regSP, cpu.SP);

  // IR & Flags
  el.regIRText.textContent = cpu.IR || 'NOP';
  el.flagZF.textContent = `ZF: ${cpu.flags.ZF}`;
  el.flagZF.classList.toggle('active', cpu.flags.ZF === 1);
  el.flagSF.textContent = `SF: ${cpu.flags.SF}`;
  el.flagSF.classList.toggle('active', cpu.flags.SF === 1);
  el.flagCF.textContent = `CF: ${cpu.flags.CF}`;
  el.flagCF.classList.toggle('active', cpu.flags.CF === 1);
  el.flagOF.textContent = `OF: ${cpu.flags.OF}`;
  el.flagOF.classList.toggle('active', cpu.flags.OF === 1);

  // Counters
  el.statCycles.textContent = cpu.clock_cycles;
  el.statInstrs.textContent = cpu.instruction_count;
  el.statStatus.textContent = cpu.halted ? 'HALTED' : 'RUNNING';
  el.statStatus.className = `v ${cpu.halted ? 'badge-speedup' : 'badge-ready'}`;

  // Console output
  if (cpu.stdout && cpu.stdout.length > 0) {
    const lastMsg = cpu.stdout[cpu.stdout.length - 1];
    logConsole(lastMsg, 'stdout');
  }
}

function updateRegisterVal(regBox, val) {
  const valEl = regBox.querySelector('.reg-val');
  const hexEl = regBox.querySelector('.reg-hex');
  if (valEl.textContent !== String(val)) {
    regBox.classList.add('highlight');
    setTimeout(() => regBox.classList.remove('highlight'), 300);
  }
  valEl.textContent = val;
  hexEl.textContent = `0x${(val & 0xFFFF).toString(16).padStart(4, '0').toUpperCase()}`;
}

function renderMemory(memoryDump, currentPC, currentMAR) {
  if (!memoryDump || memoryDump.length === 0) {
    el.memoryTbody.innerHTML = `<tr><td colspan="6" class="placeholder-text">Memory empty.</td></tr>`;
    return;
  }

  let html = '';
  memoryDump.forEach(cell => {
    let rowClass = '';
    if (cell.address === currentPC && cell.segment === 'CODE') {
      rowClass = 'active-pc';
    } else if (cell.address === currentMAR) {
      rowClass = 'active-mar';
    }

    const segClass = cell.segment === 'CODE' ? 'mem-seg-code' : 'mem-seg-data';
    const displayVal = cell.instruction || cell.value;

    html += `<tr class="${rowClass}">
      <td>${cell.hex_addr} (${cell.address})</td>
      <td class="${segClass}">${cell.segment}</td>
      <td style="color:#d29922;">${cell.label || '-'}</td>
      <td>${cell.value}</td>
      <td style="color:#5e6f84;">${cell.hex_val}</td>
      <td><strong>${displayVal}</strong></td>
    </tr>`;
  });
  el.memoryTbody.innerHTML = html;
}

// =========================================================
// DAA Complexity & Master Theorem
// =========================================================
function updateDaaMetrics(daa) {
  if (!daa) return;
  el.daaTimeVal.textContent = daa.time_complexity;
  el.daaTimeDesc.textContent = daa.time_explanation;
  el.daaSpaceVal.textContent = daa.space_complexity;
  el.daaSpaceDesc.textContent = daa.space_explanation;
  el.daaLoopVal.textContent = daa.max_loop_depth;
  el.daaVarsVal.textContent = daa.variables_allocated;
}

async function solveMasterTheorem() {
  const a = parseFloat(el.mtA.value);
  const b = parseFloat(el.mtB.value);
  const k = parseFloat(el.mtK.value);
  const p = parseFloat(el.mtP.value);

  try {
    const res = await fetch('/api/daa/solve-master', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ a, b, k, p }),
    });
    const data = await res.json();
    if (data.error) {
      el.mtBound.textContent = 'Error';
      el.mtExplanation.textContent = data.error;
      return;
    }
    el.mtBound.textContent = `${data.bound} (Case ${data.case})`;
    el.mtExplanation.textContent = data.explanation;
  } catch (err) {
    logConsole(`Master theorem error: ${err.message}`, 'error');
  }
}

async function loadDivideAndConquerTree(algo) {
  try {
    let params = {};
    if (algo === 'fastpow') params = { base: 2, exp: 8 };
    else if (algo === 'karatsuba') params = { x: 42, y: 18 };
    else if (algo === 'binsearch') params = { array: [2, 5, 8, 12, 16, 23, 38, 45, 56, 72, 91], target: 23 };

    const res = await fetch('/api/daa/divide-and-conquer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ algorithm: algo, params }),
    });

    const data = await res.json();
    renderTree(data.tree);

    // Update Benchmark Card
    const bm = data.benchmark;
    if (bm) {
      el.benchNaiveName.textContent = bm.naive.algorithm;
      el.benchNaiveInstr.textContent = bm.naive.instructions;
      el.benchNaiveCycles.textContent = bm.naive.clock_cycles;

      el.benchDncName.textContent = bm.divide_and_conquer.algorithm;
      el.benchDncInstr.textContent = bm.divide_and_conquer.instructions;
      el.benchDncCycles.textContent = bm.divide_and_conquer.clock_cycles;

      el.benchSpeedup.textContent = bm.speedup_factor;
      el.benchReduction.textContent = `(${bm.cycle_reduction_percent} CPU cycles saved)`;
    }
  } catch (err) {
    logConsole(`D&C tree load error: ${err.message}`, 'error');
  }
}

function renderTree(rootNode) {
  if (!rootNode) return;

  function buildHtml(node) {
    let html = `<div class="tree-node-card">
      <div class="tree-node-title">${node.name}</div>
      <div class="tree-node-op">${node.operation}</div>
      ${node.combine_step ? `<div style="font-size:10px; color:#9aa7b8; margin:2px 0;">Combine: ${node.combine_step}</div>` : ''}
      <div class="tree-node-res">Result: ${node.result}</div>`;

    if (node.children && node.children.length > 0) {
      html += `<div style="display:flex; justify-content:center; gap:8px; margin-top:8px; border-top:1px dashed #2b394f; padding-top:6px;">`;
      node.children.forEach(c => {
        html += buildHtml(c);
      });
      html += `</div>`;
    }
    html += `</div>`;
    return html;
  }

  el.treeCanvas.innerHTML = `<div style="text-align:center;">${buildHtml(rootNode)}</div>`;
}

// Utility: Logging to Console
function logConsole(message, type = 'system') {
  const entry = document.createElement('div');
  entry.className = `log-entry ${type}`;
  const time = new Date().toLocaleTimeString();
  entry.textContent = `[${time}] ${message}`;
  el.consoleOutput.appendChild(entry);
  el.consoleOutput.scrollTop = el.consoleOutput.scrollHeight;
}

function escapeHtml(text) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}
