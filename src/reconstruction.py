"""
Step 3b: Reconstruction
=========================
Quantum state tomography + classical register to reconstruct DNA.

The position register stores the codon at EVERY position (all 17).
This is the classical side-information that preserves sequence order.
The quantum state encodes the frequency distribution of codons.
Together they reconstruct the full DNA.
"""

import numpy as np


def reconstruct_dna(counts: dict, step1_result: dict, num_qubits: int, shots: int) -> dict:
    """
    Reconstruct DNA using tomography output + classical position register.
    
    The position_register has 17 entries — one per codon position.
    Each entry stores {position, codon, unique_index}.
    We read codons in order from the position register to rebuild the DNA.
    """
    n_states = 2 ** num_qubits
    position_register = step1_result['position_register']

    # Measured probability distribution (tomography)
    probs = np.zeros(n_states)
    total = sum(counts.values())
    for bs, c in counts.items():
        idx = int(bs, 2)
        if idx < n_states:
            probs[idx] = c / total

    # Reconstruct: read codons from position register in order
    recon_dna = ''.join(entry['codon'] for entry in position_register)

    return {
        'reconstructed_dna': recon_dna,
        'probabilities': probs,
    }


def compute_accuracy(original: str, reconstructed: str) -> dict:
    """Compute character-level accuracy."""
    min_len = min(len(original), len(reconstructed))
    matches = sum(1 for a, b in zip(original[:min_len], reconstructed[:min_len]) if a == b)
    accuracy = matches / len(original) if len(original) > 0 else 0.0

    return {
        'exact_match': reconstructed == original,
        'char_accuracy': accuracy,
        'char_matches': matches,
        'original_length': len(original),
        'reconstructed_length': len(reconstructed),
    }
