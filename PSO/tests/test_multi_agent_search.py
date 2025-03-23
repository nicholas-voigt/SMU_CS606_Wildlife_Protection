from SMU_CS606_Wildlife_Protection.PSO.multi_agent_search import PSODroneSearch
import numpy as np

def test_multiple_runs(num_runs=5):
    """Run multiple simulations and collect statistics"""
    iterations_needed = []
    final_scores = []
    
    for i in range(num_runs):
        print(f"\nRun {i+1}/{num_runs}")
        search = PSODroneSearch()
        search.run_search()
        
        # Collect results
        iterations_needed.append(search.global_best_score)
        final_scores.append(search.global_best_score)
        
        # Optional: show plot for each run
        search.plot_results()
    
    # Print statistics
    print("\nTest Results:")
    print(f"Average final score: {np.mean(final_scores):.2f}")
    print(f"Best final score: {np.min(final_scores):.2f}")
    print(f"Worst final score: {np.max(final_scores):.2f}")

def test_different_parameters():
    """Test the effect of different parameters"""
    # Test with more drones
    search = PSODroneSearch()
    search.NUM_PARTICLES = 40
    print("\nTesting with 40 drones:")
    search.run_search()
    search.plot_results()
    
    # Test with different search parameters
    search = PSODroneSearch()
    search.W = 0.7    # Increase inertia
    search.C1 = 2.0   # Increase cognitive coefficient
    search.C2 = 2.0   # Increase social coefficient
    print("\nTesting with modified PSO parameters:")
    search.run_search()
    search.plot_results()

if __name__ == "__main__":
    print("Running multiple simulations...")
    test_multiple_runs(3)  # Run 3 simulations
    
    print("\nTesting different parameters...")
    test_different_parameters() 