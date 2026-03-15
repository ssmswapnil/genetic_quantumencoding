"""
Step 2: Data Encoding (Codon Weights)
=======================================
Two encoding strategies:

1. AMPLITUDE ENCODING:
   - n = ceil(log2(N_unique)) qubits
   - 2^(n-1) CNOT gates + 2^(n-1) Ry gates = 2^n total
   - Encodes weights as amplitudes of basis states
   - |psi> = (1/norm) * sum_i weight_i |i>

2. ANGLE ENCODING:
   - N_unique qubits (one per unique codon)
   - N_unique Ry gates, 0 CNOTs
   - Depth 1 (all rotations parallel)
   - Each codon weight encoded as rotation angle on its own qubit
   - |psi> = tensor_product_i  Ry(2*theta_i)|0>
   - Product state (no entanglement)
   - Data rescaled to (0, 2*pi] to avoid information loss
"""

import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, DensityMatrix


# ============================================================================
# AMPLITUDE ENCODING
# ============================================================================

def build_amplitude_vector(weight_vector: np.ndarray) -> np.ndarray:
    """Normalize weight vector into valid quantum amplitudes."""
    amps = weight_vector.astype(complex)
    norm = np.linalg.norm(amps)
    if norm > 0:
        amps /= norm
    return amps


def amplitude_encode(step1_result: dict) -> dict:
    """
    Amplitude encoding: weights become amplitudes of basis states.
    n = ceil(log2(N_unique)) qubits.
    Gate count: 2^(n-1) CNOTs + 2^(n-1) Ry = 2^n total.
    """
    weight_vec = step1_result['weight_vector']
    n_q = step1_result['num_qubits']

    amps = build_amplitude_vector(weight_vec)

    qc = QuantumCircuit(n_q)
    qc.initialize(amps, range(n_q))

    qc_m = QuantumCircuit(n_q, n_q)
    qc_m.initialize(amps, range(n_q))
    qc_m.measure(range(n_q), range(n_q))

    initial_sv = Statevector(amps)
    initial_dm = DensityMatrix(initial_sv)

    return {
        'encoding_type': 'amplitude',
        'circuit': qc,
        'circuit_meas': qc_m,
        'amplitudes': amps,
        'initial_sv': initial_sv,
        'initial_dm': initial_dm,
        'num_qubits': n_q,
        'logical_cnot': 2 ** (n_q - 1),
        'logical_ry': 2 ** (n_q - 1),
        'logical_total': 2 ** n_q,
    }


# ============================================================================
# ANGLE ENCODING
# ============================================================================

def rescale_weights_to_angles(weights: np.ndarray) -> np.ndarray:
    """
    Rescale codon weights to (0, 2*pi] for angle encoding.
    Uses min-max normalization: weight -> (weight / max_weight) * 2*pi
    This prevents information loss from the modulo-2pi effect.
    """
    max_w = np.max(weights[weights > 0]) if np.any(weights > 0) else 1.0
    angles = np.zeros_like(weights, dtype=float)
    for i in range(len(weights)):
        if weights[i] > 0:
            angles[i] = (weights[i] / max_w) * 2 * np.pi
    return angles


def angle_encode(step1_result: dict) -> dict:
    """
    Angle encoding: each unique codon gets its own qubit.
    Weight is encoded as Ry rotation angle on that qubit.
    
    N_unique qubits, N_unique Ry gates, 0 CNOTs, depth 1.
    Product state (no entanglement).
    
    |psi> = tensor_i Ry(theta_i)|0>
          = tensor_i [cos(theta_i/2)|0> + sin(theta_i/2)|1>]
    """
    unique_reg = step1_result['unique_register']
    n_unique = step1_result['num_unique']
    n_q = n_unique  # one qubit per unique codon

    # Get weights in order
    weights = np.array([entry['weight'] for entry in unique_reg], dtype=float)

    # Rescale to (0, 2*pi]
    angles = rescale_weights_to_angles(weights)

    # Build circuit: one Ry per qubit, no CNOTs
    qc = QuantumCircuit(n_q)
    for i in range(n_q):
        qc.ry(angles[i], i)

    qc_m = QuantumCircuit(n_q, n_q)
    for i in range(n_q):
        qc_m.ry(angles[i], i)
    qc_m.measure(range(n_q), range(n_q))

    # Compute the ideal initial state
    initial_sv = Statevector.from_instruction(qc)
    initial_dm = DensityMatrix(initial_sv)

    return {
        'encoding_type': 'angle',
        'circuit': qc,
        'circuit_meas': qc_m,
        'angles': angles,
        'weights': weights,
        'initial_sv': initial_sv,
        'initial_dm': initial_dm,
        'num_qubits': n_q,
        'logical_cnot': 0,
        'logical_ry': n_q,
        'logical_total': n_q,
    }


# ============================================================================
# PRINTING
# ============================================================================

def print_step2(step1_result: dict, step2_result: dict):
    """Print Step 2 report for either encoding type."""
    enc_type = step2_result['encoding_type']
    n_q = step2_result['num_qubits']
    reg = step1_result['unique_register']

    if enc_type == 'amplitude':
        _print_amplitude(step1_result, step2_result)
    elif enc_type == 'angle':
        _print_angle(step1_result, step2_result)


def _print_amplitude(step1_result, step2_result):
    """Print amplitude encoding report."""
    n_q = step2_result['num_qubits']
    amps = step2_result['amplitudes']
    n_states = 2 ** n_q
    reg = step1_result['unique_register']

    print("\n" + "=" * 65)
    print("STEP 2: AMPLITUDE ENCODING (CODON WEIGHTS)")
    print("=" * 65)
    print(f"\n  Qubits:            {n_q}")
    print(f"  Hilbert space:     2^{n_q} = {n_states}")
    print(f"  Unique codons:     {step1_result['num_unique']}")
    print(f"  States used:       {step1_result['num_unique']}/{n_states}")

    print(f"\n  Logical gates (amplitude encoding):")
    print(f"    CNOT gates:      {step2_result['logical_cnot']}  (2^(n-1))")
    print(f"    Ry rotations:    {step2_result['logical_ry']}  (2^(n-1))")
    print(f"    Total:           {step2_result['logical_total']}  (2^n)")

    print(f"\n  Quantum state |psi> = (1/N) * sum_i weight_i |i>:")
    print(f"  {'Basis':>8}  {'Weight':>6}  {'Amplitude':>12}  {'P(|a|²)':>10}  Codon")
    print(f"  {'-'*8}  {'-'*6}  {'-'*12}  {'-'*10}  {'-'*6}")

    for entry in reg:
        idx = entry['unique_index']
        a = amps[idx]
        p = np.abs(a) ** 2
        print(f"  |{entry['binary']}>  {entry['weight']:6d}  {a.real:12.6f}  {p:10.6f}  {entry['codon']}")

    for i in range(step1_result['num_unique'], 2 ** n_q):
        binary = format(i, f'0{step1_result["num_qubits"]}b')
        print(f"  |{binary}>  {0:6d}  {0:12.6f}  {0:10.6f}  (unused)")

    total_prob = sum(np.abs(amps[e['unique_index']]) ** 2 for e in reg)
    print(f"\n  Total probability: {total_prob:.6f}")


def _print_angle(step1_result, step2_result):
    """Print angle encoding report."""
    n_q = step2_result['num_qubits']
    angles = step2_result['angles']
    weights = step2_result['weights']
    reg = step1_result['unique_register']

    print("\n" + "=" * 65)
    print("STEP 2: ANGLE ENCODING (CODON WEIGHTS)")
    print("=" * 65)
    print(f"\n  Qubits:            {n_q} (one per unique codon)")
    print(f"  Encoding:          Ry(theta_i)|0> per qubit")
    print(f"  Product state:     Yes (no entanglement)")

    print(f"\n  Logical gates (angle encoding):")
    print(f"    CNOT gates:      {step2_result['logical_cnot']}")
    print(f"    Ry rotations:    {step2_result['logical_ry']}")
    print(f"    Total:           {step2_result['logical_total']}")
    print(f"    Circuit depth:   1")

    print(f"\n  Qubit assignments:")
    print(f"  {'Qubit':>6}  {'Codon':>6}  {'Weight':>6}  {'Angle(rad)':>12}  {'Angle(deg)':>12}")
    print(f"  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*12}  {'-'*12}")

    for i, entry in enumerate(reg):
        w = weights[i]
        a = angles[i]
        print(f"  q[{i:2d}]  {entry['codon']:>6}  {w:6.0f}  {a:12.6f}  {np.degrees(a):12.2f}°")

    # Show the product state structure
    print(f"\n  State: |psi> = ", end="")
    parts = []
    for i, entry in enumerate(reg):
        a = angles[i]
        parts.append(f"Ry({a:.3f})|0>_q{i}")
    print(" ⊗ ".join(parts[:4]))
    if len(parts) > 4:
        print(f"         ⊗ " + " ⊗ ".join(parts[4:8]))
    if len(parts) > 8:
        print(f"         ⊗ " + " ⊗ ".join(parts[8:]))
