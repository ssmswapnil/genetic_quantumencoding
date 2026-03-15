"""
Efficient Quantum Encoding of Genetic Information
===================================================
PhysisTechne Symposium 2026 — Quantum Computing Track

Runs TWO encoding strategies on the same data:
  1. Amplitude Encoding: 4 qubits, 2^n gates (CNOTs + Ry)
  2. Angle Encoding: 12 qubits, 12 Ry gates, 0 CNOTs, depth 1

Both share the same Step 1 (codon division + classical register)
and the same Step 3 (simulation + tomography + reconstruction + fidelity).
"""

import os
import sys
import json
import time
from collections import Counter

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

from src.compression import DNA_SEQUENCE, build_classical_register, print_step1
from src.encoding import amplitude_encode, angle_encode, print_step2
from src.simulation import run_dual_simulation
from src.reconstruction import reconstruct_dna, compute_accuracy
from src.fidelity import compute_all_fidelities

SHOTS = 8192
RESULTS_DIR = os.path.join(SCRIPT_DIR, 'results')


def run_step3(s1, s2, label):
    """Step 3: Simulate + reconstruct for a given encoding."""
    print(f"\n{'='*65}")
    print(f"STEP 3: SIMULATION + RECONSTRUCTION ({label})")
    print(f"{'='*65}")

    sim = run_dual_simulation(s2, shots=SHOTS)

    for name, key in [("Aer (ideal)", 'aer'), ("FakeSherbrooke (noisy)", 'sherbrooke')]:
        top5 = Counter(sim[key]['counts']).most_common(5)
        print(f"\n  {name} — Top 5 counts:")
        print(f"    {dict(top5)}")

    n_q = s2['num_qubits']
    aer_recon = reconstruct_dna(sim['aer']['counts'], s1, n_q, SHOTS)
    sher_recon = reconstruct_dna(sim['sherbrooke']['counts'], s1, n_q, SHOTS)

    aer_acc = compute_accuracy(DNA_SEQUENCE, aer_recon['reconstructed_dna'])
    sher_acc = compute_accuracy(DNA_SEQUENCE, sher_recon['reconstructed_dna'])

    print(f"\n  Reconstruction:")
    print(f"    Original:          {DNA_SEQUENCE}")
    print(f"    Aer recon:         {aer_recon['reconstructed_dna']}")
    print(f"    Aer match:         {aer_acc['exact_match']} ({aer_acc['char_accuracy']:.2%})")
    print(f"    Sherbrooke recon:  {sher_recon['reconstructed_dna']}")
    print(f"    Sherbrooke match:  {sher_acc['exact_match']} ({sher_acc['char_accuracy']:.2%})")

    return {
        'aer': sim['aer'],
        'sherbrooke': sim['sherbrooke'],
        'aer_recon': {**aer_recon, **aer_acc},
        'sherbrooke_recon': {**sher_recon, **sher_acc},
    }


def run_pipeline(s1, encode_fn, label):
    """Run Step 2 + Step 3 + Fidelity for one encoding type."""
    s2 = encode_fn(s1)
    print_step2(s1, s2)
    s3 = run_step3(s1, s2, label)
    fid = compute_all_fidelities(s2, s3)
    return s2, s3, fid


def print_comparison(amp_data, ang_data):
    """Print side-by-side comparison of both encodings."""
    s2_amp, s3_amp, fid_amp = amp_data
    s2_ang, s3_ang, fid_ang = ang_data
    m_amp = s3_amp['sherbrooke']['metrics']
    m_ang = s3_ang['sherbrooke']['metrics']

    print("\n" + "=" * 65)
    print("COMPARISON: AMPLITUDE vs ANGLE ENCODING")
    print("=" * 65)
    print(f"""
  {'Metric':<35} {'Amplitude':>12} {'Angle':>12}
  {'-'*35} {'-'*12} {'-'*12}
  Qubits                             {s2_amp['num_qubits']:>12} {s2_ang['num_qubits']:>12}
  Logical CNOT gates                 {s2_amp['logical_cnot']:>12} {s2_ang['logical_cnot']:>12}
  Logical Ry gates                   {s2_amp['logical_ry']:>12} {s2_ang['logical_ry']:>12}
  Logical total gates                {s2_amp['logical_total']:>12} {s2_ang['logical_total']:>12}
  Transpiled depth                   {m_amp['depth']:>12} {m_ang['depth']:>12}
  Transpiled total gates             {m_amp['total_gates']:>12} {m_ang['total_gates']:>12}
  Transpiled two-qubit gates         {m_amp['two_qubit_gates']:>12} {m_ang['two_qubit_gates']:>12}
  Transpiled SWAPs                   {m_amp['swap_count']:>12} {m_ang['swap_count']:>12}
  F(initial, Aer)                    {fid_amp['raw_fidelity_aer']:>12.6f} {fid_ang['raw_fidelity_aer']:>12.6f}
  F(initial, Sherbrooke)             {fid_amp['raw_fidelity_sherbrooke']:>12.6f} {fid_ang['raw_fidelity_sherbrooke']:>12.6f}
  F(Aer, Sherbrooke)                 {fid_amp['inter_simulator_fidelity']:>12.6f} {fid_ang['inter_simulator_fidelity']:>12.6f}
  Noise drop                         {fid_amp['fidelity_drop']:>12.6f} {fid_ang['fidelity_drop']:>12.6f}
  Reconstruction (Aer)               {'PASS' if s3_amp['aer_recon']['exact_match'] else 'FAIL':>12} {'PASS' if s3_ang['aer_recon']['exact_match'] else 'FAIL':>12}
  Reconstruction (Sherbrooke)        {'PASS' if s3_amp['sherbrooke_recon']['exact_match'] else 'FAIL':>12} {'PASS' if s3_ang['sherbrooke_recon']['exact_match'] else 'FAIL':>12}
""")


def main():
    print("=" * 65)
    print("  EFFICIENT QUANTUM ENCODING OF GENETIC INFORMATION")
    print("  PhysisTechne Symposium 2026")
    print("=" * 65)
    print(f"\n  Target: {DNA_SEQUENCE} ({len(DNA_SEQUENCE)} bases)\n")

    t0 = time.time()

    # Step 1: Same for both encodings
    s1 = build_classical_register(DNA_SEQUENCE)
    print_step1(s1)

    # Run amplitude encoding pipeline
    print("\n\n" + "#" * 65)
    print("# ENCODING 1: AMPLITUDE ENCODING")
    print("#" * 65)
    amp_data = run_pipeline(s1, amplitude_encode, "AMPLITUDE")

    # Run angle encoding pipeline
    print("\n\n" + "#" * 65)
    print("# ENCODING 2: ANGLE ENCODING")
    print("#" * 65)
    ang_data = run_pipeline(s1, angle_encode, "ANGLE")

    # Comparison
    print_comparison(amp_data, ang_data)

    elapsed = time.time() - t0
    print(f"  Total runtime: {elapsed:.1f}s")

    # Save results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    s2_amp, s3_amp, fid_amp = amp_data
    s2_ang, s3_ang, fid_ang = ang_data

    summary = {
        'sequence': DNA_SEQUENCE,
        'length': len(DNA_SEQUENCE),
        'num_codons': s1['num_codons'],
        'unique_codons': s1['num_unique'],
        'amplitude_encoding': {
            'qubits': s2_amp['num_qubits'],
            'logical_gates': s2_amp['logical_total'],
            'fidelity_aer': fid_amp['raw_fidelity_aer'],
            'fidelity_sherbrooke': fid_amp['raw_fidelity_sherbrooke'],
            'transpiled_depth': s3_amp['sherbrooke']['metrics']['depth'],
        },
        'angle_encoding': {
            'qubits': s2_ang['num_qubits'],
            'logical_gates': s2_ang['logical_total'],
            'fidelity_aer': fid_ang['raw_fidelity_aer'],
            'fidelity_sherbrooke': fid_ang['raw_fidelity_sherbrooke'],
            'transpiled_depth': s3_ang['sherbrooke']['metrics']['depth'],
        },
        'runtime': elapsed,
    }

    with open(os.path.join(RESULTS_DIR, 'summary.json'), 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"  Saved to {RESULTS_DIR}/summary.json")


if __name__ == "__main__":
    main()
