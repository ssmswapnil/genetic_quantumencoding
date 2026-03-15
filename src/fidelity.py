"""
Fidelity Calculations
======================
Raw fidelity:       F(initial_state, backend_output) for each backend
Sim comparison:     F(aer_output, sherbrooke_output)
"""

from qiskit.quantum_info import state_fidelity


def compute_all_fidelities(step2_result: dict, step3_result: dict) -> dict:
    """
    Compute all fidelity metrics.
    
    Raw fidelity:
        F(rho_initial, rho_aer)         — should be ~1.0
        F(rho_initial, rho_sherbrooke)   — shows noise impact
    
    Simulator comparison:
        F(rho_aer, rho_sherbrooke)       — direct degradation measure
    """
    print("\n" + "=" * 65)
    print("FIDELITY CALCULATIONS")
    print("=" * 65)

    initial_dm = step2_result['initial_dm']
    aer_dm = step3_result['aer']['dm']
    sherbrooke_dm = step3_result['sherbrooke']['dm']

    # Raw fidelity
    f_aer = state_fidelity(initial_dm, aer_dm) if aer_dm is not None else 0.0
    f_sher = state_fidelity(initial_dm, sherbrooke_dm) if sherbrooke_dm is not None else 0.0

    print(f"\n  RAW FIDELITY (initial state vs backend output):")
    print(f"    F(initial, Aer)        = {f_aer:.6f}")
    print(f"    F(initial, Sherbrooke)  = {f_sher:.6f}")
    print(f"    Fidelity drop (noise)  = {f_aer - f_sher:.6f}")

    # Simulator comparison
    f_inter = 0.0
    if aer_dm is not None and sherbrooke_dm is not None:
        f_inter = state_fidelity(aer_dm, sherbrooke_dm)

    print(f"\n  SIMULATOR COMPARISON:")
    print(f"    F(Aer, Sherbrooke)     = {f_inter:.6f}")

    return {
        'raw_fidelity_aer': f_aer,
        'raw_fidelity_sherbrooke': f_sher,
        'fidelity_drop': f_aer - f_sher,
        'inter_simulator_fidelity': f_inter,
    }
