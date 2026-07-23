from core.features.basis import basis_reading, compute_basis


def test_compute_basis_exact():
    assert compute_basis(future_price=102, spot_price=100) == 2.0
    assert compute_basis(future_price=98, spot_price=100) == -2.0


def test_basis_reading_classification():
    assert basis_reading(0.5) == "premium"
    assert basis_reading(-0.5) == "discount"
    assert basis_reading(0.0) == "flat"
    assert basis_reading(0.01) == "flat"  # within flat_tol
