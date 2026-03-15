"""
Step 3a: Simulation
=====================
Transpile circuit for FakeSherbrooke — the transpiler converts logical gates
to the backend's native gate set (ECR, Rz, Sx, etc.).

Reports both logical gate counts (from encoding result) and transpiled counts.

Density matrix extraction:
  Aer:        Statevector.from_instruction() on ORIGINAL circuit (n qubits)
  Sherbrooke: AerSimulator(method='density_matrix', noise_model=...) on ORIGINAL circuit
"""

import numpy as np
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_aer.noise import NoiseModel
from qiskit_ibm_runtime.fake_provider import FakeSherbrooke
from qiskit.quantum_info import Statevector, DensityMatrix


def get_circuit_metrics(transpiled_circuit) -> dict:
    """Extract depth, gate counts, two-qubit gates, SWAPs from transpiled circuit."""
    gc = dict(transpiled_circuit.count_ops())
    two_q = sum(v for k, v in gc.items()
                if k in ['cx', 'cnot', 'ecr', 'cz', 'swap', 'iswap'])
    return {
        'depth': transpiled_circuit.depth(),
        'total_gates': sum(gc.values()),
        'gate_counts': gc,
        'two_qubit_gates': two_q,
        'swap_count': gc.get('swap', 0),
    }


def run_dual_simulation(encoding_result: dict, shots: int = 8192) -> dict:
    """
    1. Read logical gate counts from encoding result (not hardcoded)
    2. Transpile for FakeSherbrooke — report transpiled metrics
    3. Run transpiled circuit on FakeSherbrooke for noisy counts
    4. Run original circuit on Aer for ideal counts
    5. Extract DMs from both
    """
    qc = encoding_result['circuit']
    qc_m = encoding_result['circuit_meas']
    n_q = encoding_result['num_qubits']
    enc_type = encoding_result['encoding_type']

    # Read logical gate counts from the encoding result
    logical_cnot = encoding_result['logical_cnot']
    logical_ry = encoding_result['logical_ry']
    logical_total = encoding_result['logical_total']

    backend = FakeSherbrooke()

    # === TRANSPILE ===
    transpiled_meas = transpile(qc_m, backend=backend, optimization_level=3)
    transpiled_metrics = get_circuit_metrics(transpiled_meas)

    print(f"\n  Logical circuit ({enc_type} encoding):")
    print(f"    CNOT gates:      {logical_cnot}")
    print(f"    Ry rotations:    {logical_ry}")
    print(f"    Total:           {logical_total}")

    print(f"\n  Transpiled circuit (FakeSherbrooke native gates):")
    print(f"    Depth:           {transpiled_metrics['depth']}")
    print(f"    Total gates:     {transpiled_metrics['total_gates']}")
    print(f"    Two-qubit gates: {transpiled_metrics['two_qubit_gates']}")
    print(f"    SWAPs:           {transpiled_metrics['swap_count']}")
    print(f"    Gate breakdown:  {transpiled_metrics['gate_counts']}")

    # === AER (ideal) ===
    print(f"\n  Running on Aer (ideal, original {n_q}-qubit circuit)...")
    aer_sim = AerSimulator()
    aer_transpiled = transpile(qc_m, backend=aer_sim, optimization_level=0)
    aer_result = aer_sim.run(aer_transpiled, shots=shots).result()
    aer_counts = aer_result.get_counts()

    aer_dm = None
    try:
        sv = Statevector.from_instruction(qc)
        aer_dm = DensityMatrix(sv)
        print(f"    [Aer] Density matrix: exact ({n_q}-qubit statevector)")
    except Exception as e:
        print(f"    [Aer] Statevector failed: {e}")

    if aer_dm is None:
        aer_dm = _dm_from_counts(aer_counts, n_q)
        print(f"    [Aer] Density matrix: diagonal fallback")

    # === FAKESHERBROOKE (noisy) ===
    print(f"  Running on FakeSherbrooke (noisy, transpiled circuit)...")
    sherbrooke_result = backend.run(transpiled_meas, shots=shots).result()
    sherbrooke_counts = sherbrooke_result.get_counts()

    sherbrooke_dm = None
    try:
        noise = NoiseModel.from_backend(backend)
        dm_sim = AerSimulator(method='density_matrix', noise_model=noise)
        qc_dm = qc.copy()
        qc_dm.save_density_matrix()
        dm_transpiled = transpile(qc_dm, backend=dm_sim, optimization_level=3)
        dm_result = dm_sim.run(dm_transpiled).result()
        dm_data = dm_result.data()['density_matrix']
        sherbrooke_dm = DensityMatrix(dm_data)
        print(f"    [Sherbrooke] Density matrix: noisy ({n_q}-qubit DM simulation)")
    except Exception as e:
        print(f"    [Sherbrooke] Noisy DM failed: {e}")

    if sherbrooke_dm is None:
        sherbrooke_dm = _dm_from_counts(sherbrooke_counts, n_q)
        print(f"    [Sherbrooke] Density matrix: diagonal fallback")

    metrics = {
        'logical_cnot': logical_cnot,
        'logical_ry': logical_ry,
        'logical_total': logical_total,
        **transpiled_metrics,
    }

    return {
        'aer': {
            'counts': aer_counts,
            'dm': aer_dm,
            'metrics': metrics,
            'shots': shots,
        },
        'sherbrooke': {
            'counts': sherbrooke_counts,
            'dm': sherbrooke_dm,
            'metrics': metrics,
            'shots': shots,
        },
    }


def _dm_from_counts(counts: dict, num_qubits: int) -> DensityMatrix:
    """Diagonal DM from counts (fallback)."""
    n = 2 ** num_qubits
    arr = np.zeros((n, n), dtype=complex)
    total = sum(counts.values())
    for bs, c in counts.items():
        idx = int(bs, 2)
        if idx < n:
            arr[idx, idx] = c / total
    return DensityMatrix(arr)
