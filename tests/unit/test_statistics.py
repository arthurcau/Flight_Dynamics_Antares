import pytest
import numpy as np
from antares_fd.simulation.statistics import calculate_covariance_ellipse

def test_covariance_ellipse():
    # Circular distribution
    np.random.seed(42)
    # Generate 1,000,000 points to approximate theoretical properties well
    # Using small N will fail tight assertions
    x = np.random.normal(0, 1, 100000)
    y = np.random.normal(0, 1, 100000)
    
    # 50% probability chi-square(2) value is approx 1.386
    res_50 = calculate_covariance_ellipse(x, y, 0.5)
    assert np.isclose(res_50['chi2_val'], 1.386, atol=0.01)
    
    # 95% probability chi-square(2) value is approx 5.991
    res_95 = calculate_covariance_ellipse(x, y, 0.95)
    assert np.isclose(res_95['chi2_val'], 5.991, atol=0.01)
    
    # Check width/height roughly matches 2*sqrt(chi2 * variance) where variance is 1
    # width = 2 * sqrt(5.991 * 1) = 2 * 2.447 = 4.89
    assert np.isclose(res_95['width'], 4.89, atol=0.1)
    assert np.isclose(res_95['height'], 4.89, atol=0.1)
    
    # Center should be roughly 0, 0
    assert np.isclose(res_95['center'][0], 0, atol=0.1)
    assert np.isclose(res_95['center'][1], 0, atol=0.1)

def test_covariance_ellipse_errors():
    with pytest.raises(ValueError):
        calculate_covariance_ellipse([1], [1], 0.5)
        
    with pytest.raises(ValueError):
        calculate_covariance_ellipse([1, 2], [1, 2, 3], 0.5)
        
    with pytest.raises(ValueError):
        calculate_covariance_ellipse([1, 2], [1, 2], 1.5)
