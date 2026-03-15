# Efficient Quantum Encoding of Genetic Information

**PhysisTechne Symposium 2026 — Quantum Computing Track**

A quantum computing pipeline that encodes a 50-base DNA sequence into optimized quantum circuits using two encoding strategies — **amplitude encoding** and **angle encoding** — and benchmarks them on IBM's FakeSherbrooke (127-qubit Eagle processor) simulator.

## Results

| Metric | Amplitude Encoding | Angle Encoding |
|---|---|---|
| Qubits | 4 | 12 |
| Logical CNOT gates | 8 | 0 |
| Logical Ry gates | 8 | 12 |
| Logical total gates | 16 | 12 |
| Transpiled depth (Sherbrooke) | 67 | 5 |
| Transpiled two-qubit gates | 15 | 0 |
| F(initial, Aer) | 1.000000 | 1.000000 |
| F(initial, Sherbrooke) | 0.958512 | 0.985308 |
| Noise drop | 0.041488 | 0.014692 |
| Reconstruction accuracy | 100% | 100% |

## Pipeline

### Step 1 — Classical Bit Register

Divide the DNA sequence into **codons** (triplets of 3 bases). Count the frequency of each unique codon — this is its **weight**. Build two classical registers:

- **Unique register** (12 entries): maps each unique codon to an index and stores its weight
- **Position register** (17 entries): records which codon appears at every position in the sequence

```
ATGCGTACGTTAGCGTACGATCGTAGCTAGCTTGACGATCGTACGTTAGC
 → ['ATG', 'CGT', 'ACG', 'TTA', 'GCG', 'TAC', 'GAT', 'CGT', 'AGC', 'TAG', 'CTT', 'GAC', 'GAT', 'CGT', 'ACG', 'TTA', 'GC']
 → 17 codons, 12 unique, weights: CGT=3, ACG=2, TTA=2, GAT=2, rest=1
```

### Step 2 — Quantum Encoding

Two encoding strategies are applied to the same codon weights:

**Amplitude Encoding:** Encodes codon weights as amplitudes of basis states on `ceil(log2(12)) = 4` qubits. Uses `2^(n-1) = 8` CNOT gates and `8` Ry rotation gates (16 total). The quantum state is:

```
|ψ⟩ = (1/N) Σᵢ weightᵢ |i⟩
```

**Angle Encoding:** Encodes each codon weight as an Ry rotation angle on its own qubit — 12 qubits, 12 Ry gates, 0 CNOTs, depth 1. Weights are rescaled to (0, 2π]. The state is a product state (no entanglement):

```
|ψ⟩ = ⊗ᵢ Ry(θᵢ)|0⟩
```

### Step 3 — Simulation + Tomography + Reconstruction

Both circuits are transpiled for FakeSherbrooke and run on:

- **Aer Simulator** (ideal, no noise) — baseline
- **FakeSherbrooke** (IBM Eagle noise model) — realistic hardware noise

Density matrices are extracted for fidelity calculation. The DNA is reconstructed using the classical position register.

### Fidelity

Three fidelity metrics are computed:

- `F(initial, Aer)` — does the ideal simulator reproduce the target state?
- `F(initial, Sherbrooke)` — how much does noise degrade the state?
- `F(Aer, Sherbrooke)` — direct comparison between backends

## Project Structure

```
├── main.py                    # Entry point — runs both encodings and prints comparison
├── requirements.txt           # Python dependencies
├── src/
│   ├── __init__.py
│   ├── compression.py         # Step 1: Codon division + classical register
│   ├── encoding.py            # Step 2: Amplitude & angle encoding functions
│   ├── simulation.py          # Step 3a: Aer + FakeSherbrooke simulation
│   ├── reconstruction.py      # Step 3b: Tomography + classical register → DNA
│   └── fidelity.py            # Fidelity calculations
├── results/
│   └── summary.json           # Output metrics
└── data/
    └── dna_12000.txt           # Bonus: 12,001-base Rhesus monkey chr16 fragment
```

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows

pip install -r requirements.txt
```

## Usage

```bash
python main.py
```

Runs both amplitude and angle encoding pipelines, prints detailed step-by-step output, a side-by-side comparison table, and saves results to `results/summary.json`.

## Requirements

- Python 3.10+
- Qiskit >= 1.0
- Qiskit Aer >= 0.14
- Qiskit IBM Runtime >= 0.20
- NumPy >= 1.24

## DNA Sequence

**Target (50 bases):**
```
ATGCGTACGTTAGCGTACGATCGTAGCTAGCTTGACGATCGTACGTTAGC
```

**Bonus (12,001 bases):** Rhesus macaque (*Macaca mulatta*) chromosome 16 fragment from `NC_133421.1:91056922-91068922`, gene LOC144335571. Stored in `data/dna_12000.txt`.

## References

- IBM Quantum Learning — [Data Encoding](https://quantum.cloud.ibm.com/learning/en/courses/quantum-machine-learning/data-encoding)
- Qiskit Documentation — [FakeSherbrooke](https://docs.quantum.ibm.com/api/qiskit-ibm-runtime/fake_provider)

## License

[MIT](LICENSE)
