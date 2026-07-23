"""Futures basis (premium/discount vs spot)."""
from __future__ import annotations


def compute_basis(future_price: float, spot_price: float) -> float:
    """Basis as a percentage of spot; positive = futures premium."""
    return (future_price - spot_price) / spot_price * 100


def basis_reading(basis_pct: float, flat_tol: float = 0.02) -> str:
    if basis_pct > flat_tol:
        return "premium"
    if basis_pct < -flat_tol:
        return "discount"
    return "flat"
