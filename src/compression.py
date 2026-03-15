"""
Step 1: Classical Bit Register (Codon-Based)
==============================================
Divide DNA into codons (size 3). Count frequency of each unique codon (= weight).
Build classical register with an index for EVERY codon position (not just unique ones).
This preserves the full sequence ordering needed for reconstruction.
"""

import numpy as np
from collections import Counter, OrderedDict


DNA_SEQUENCE = "ATGCGTACGTTAGCGTACGATCGTAGCTAGCTTGACGATCGTACGTTAGC"


def divide_into_codons(sequence: str) -> list:
    """Divide DNA into codons (groups of 3). Last group may have <3 bases."""
    return [sequence[i:i+3] for i in range(0, len(sequence), 3)]


def build_classical_register(sequence: str) -> dict:
    """
    Step 1 entry point.
    
    1. Divide sequence into codons (size 3)
    2. Count frequency of each unique codon (= weight)
    3. Assign an index to each unique codon
    4. Build classical register with an entry for EVERY codon position
       (17 entries, not 12) — so we know exactly where each codon sits
    
    The quantum state will encode:
        - Number of basis states = number of unique codons
        - Amplitude of |i> = weight (frequency) of unique codon i
    
    The classical register stores:
        - Full position-by-position codon sequence (for reconstruction)
        - Mapping from unique codon index to codon string
    """
    # Step 1: Divide into codons
    codon_sequence = divide_into_codons(sequence)
    
    # Step 2: Count frequencies (weights)
    freq = Counter(codon_sequence)
    
    # Step 3: Assign index to each unique codon (ordered by first appearance)
    seen = OrderedDict()
    for codon in codon_sequence:
        if codon not in seen:
            seen[codon] = len(seen)
    
    unique_codons = seen  # {codon_string: unique_index}
    n_unique = len(unique_codons)
    n_qubits = int(np.ceil(np.log2(max(n_unique, 2))))
    
    # Step 4a: Unique codon register (for quantum state)
    unique_register = []
    for codon, idx in unique_codons.items():
        unique_register.append({
            'unique_index': idx,
            'codon': codon,
            'weight': freq[codon],
            'binary': format(idx, f'0{n_qubits}b'),
        })
    
    # Step 4b: Full position register — one entry per codon position (all 17)
    position_register = []
    for pos, codon in enumerate(codon_sequence):
        position_register.append({
            'position': pos,
            'codon': codon,
            'unique_index': unique_codons[codon],
            'binary': format(unique_codons[codon], f'0{n_qubits}b'),
        })
    
    # Weight vector for quantum state: amplitude[unique_index] = weight
    n_states = 2 ** n_qubits
    weight_vector = np.zeros(n_states)
    for entry in unique_register:
        weight_vector[entry['unique_index']] = entry['weight']
    
    return {
        'sequence': sequence,
        'codon_sequence': codon_sequence,
        'num_codons': len(codon_sequence),
        'unique_codons': unique_codons,
        'num_unique': n_unique,
        'weights': dict(freq),
        'unique_register': unique_register,
        'position_register': position_register,
        'num_qubits': n_qubits,
        'weight_vector': weight_vector,
    }


def print_step1(result: dict):
    """Print Step 1 report."""
    seq = result['sequence']
    codons = result['codon_sequence']
    n_q = result['num_qubits']
    
    print("=" * 65)
    print("STEP 1: PREPARE CLASSICAL BIT REGISTER (CODON-BASED)")
    print("=" * 65)
    print(f"\n  Sequence:           {seq}")
    print(f"  Length:             {len(seq)} bases")
    print(f"  Codons (size 3):   {codons}")
    print(f"  Total codons:      {result['num_codons']}")
    print(f"  Unique codons:     {result['num_unique']}")
    print(f"  Qubits needed:     {n_q} (ceil(log2({result['num_unique']})))")
    print(f"  Naive qubits:      {len(seq) * 2}")
    print(f"  Reduction:         {(1 - n_q / (len(seq) * 2)) * 100:.1f}%")
    
    print(f"\n  Unique codon register (for quantum state):")
    print(f"  {'Idx':>4}  {'Binary':>{n_q}}  {'Codon':>6}  {'Weight':>6}")
    print(f"  {'-'*4}  {'-'*n_q}  {'-'*6}  {'-'*6}")
    for e in result['unique_register']:
        print(f"  {e['unique_index']:4d}  {e['binary']}  {e['codon']:>6}  {e['weight']:6d}")
    
    print(f"\n  Full position register (all {result['num_codons']} codons):")
    print(f"  {'Pos':>4}  {'Codon':>6}  {'Unique Idx':>10}  {'Binary':>{n_q}}")
    print(f"  {'-'*4}  {'-'*6}  {'-'*10}  {'-'*n_q}")
    for e in result['position_register']:
        print(f"  {e['position']:4d}  {e['codon']:>6}  {e['unique_index']:10d}  {e['binary']}")
    
    print(f"\n  Weight check: sum = {sum(e['weight'] for e in result['unique_register'])} "
          f"(should be {result['num_codons']})")
