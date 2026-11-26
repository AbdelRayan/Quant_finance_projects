import numpy as np

from qfp.emd import decompose, imf_table, mean_period


def test_mean_period_of_a_sine():
    t = np.arange(2000)
    assert abs(mean_period(np.sin(2 * np.pi * t / 20 + 0.1)) - 20) < 0.5


def test_emd_separates_two_rhythms():
    t = np.arange(3000)
    x = np.sin(2 * np.pi * t / 8) + np.sin(2 * np.pi * t / 40)
    table = imf_table(decompose(x))
    top = table.sort_values("energy_share", ascending=False).head(2)["period"].sort_values().to_numpy()
    assert abs(top[0] - 8) < 1 and abs(top[1] - 40) < 4


def test_emd_on_noise_gives_roughly_doubling_periods():
    x = np.random.default_rng(0).standard_normal(4000)
    periods = imf_table(decompose(x))["period"].to_numpy()[:5]
    ratios = periods[1:] / periods[:-1]
    assert np.all((ratios > 1.5) & (ratios < 2.6))
