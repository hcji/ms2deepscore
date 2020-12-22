import numpy as np
import pytest
from matchms import Spectrum
from ms2deepscore import SpectrumBinner


def test_SpectrumBinner():
    """Test if default initalization works"""
    ms2ds_data = SpectrumBinner(100)
    assert ms2ds_data.mz_max == 1000.0, "Expected different default value."
    assert ms2ds_data.mz_min == 10.0, "Expected different default value."
    assert ms2ds_data.d_bins == 9.9, "Expected different calculated bin size."


def test_SpectrumBinner_set_min_max():
    """Test if other limits work well"""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0)
    assert ms2ds_data.mz_max == 100.0, "Expected different default value."
    assert ms2ds_data.mz_min == 0.0, "Expected different default value."
    assert ms2ds_data.d_bins == 1.0, "Expected different calculated bin size."


def test_SpectrumBinner_collect_binned_spectrums():
    """Test if collect binned spectrums method works."""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0, peak_scaling=1.0)
    spectrum_1 = Spectrum(mz=np.array([10, 50, 100.]),
                          intensities=np.array([0.7, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_01"})
    spectrum_2 = Spectrum(mz=np.array([10, 40, 90.]),
                          intensities=np.array([0.4, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_02"})

    ms2ds_data.collect_binned_spectrums([spectrum_1, spectrum_2])
    assert ms2ds_data.known_bins == [10, 40, 50, 90, 100], "Expected different known bins."
    assert len(ms2ds_data.spectrums_binned) == 2, "Expected 2 binned spectrums."
    assert ms2ds_data.spectrums_binned[0] == {0: 0.7, 2: 0.2, 4: 0.1}, "Expected different binned spectrum."
    assert np.all(ms2ds_data.inchikeys_all == np.array(["test_inchikey_01", "test_inchikey_02"])), \
        "Expected different inchikeys in array."


def test_SpectrumBinner_collect_binned_spectrums_peak_scaling():
    """Test if collect binned spectrums method works with different peak_scaling."""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0, peak_scaling=0.0)
    spectrum_1 = Spectrum(mz=np.array([10, 50, 100.]),
                          intensities=np.array([0.7, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_01"})
    spectrum_2 = Spectrum(mz=np.array([10, 40, 90.]),
                          intensities=np.array([0.4, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_02"})

    ms2ds_data.collect_binned_spectrums([spectrum_1, spectrum_2])
    assert ms2ds_data.known_bins == [10, 40, 50, 90, 100], "Expected different known bins."
    assert len(ms2ds_data.spectrums_binned) == 2, "Expected 2 binned spectrums."
    assert ms2ds_data.spectrums_binned[0] == {0: 1.0, 2: 1.0, 4: 1.0}, "Expected different binned spectrum."
    assert np.all(ms2ds_data.inchikeys_all == np.array(["test_inchikey_01", "test_inchikey_02"])), \
        "Expected different inchikeys in array."


def test_SpectrumBinner_collect_binned_spectrums_missing_inchikey():
    """Test if create binned spectrums method works with missing inchikey."""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0)
    spectrum_1 = Spectrum(mz=np.array([10, 50, 100.]),
                          intensities=np.array([0.7, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_01"})
    spectrum_2 = Spectrum(mz=np.array([10, 40, 90.]),
                          intensities=np.array([0.4, 0.2, 0.1]),
                          metadata={})

    ms2ds_data.collect_binned_spectrums([spectrum_1, spectrum_2])
    assert np.all(ms2ds_data.inchikeys_all == np.array(["test_inchikey_01", None])), \
        "Expected different inchikeys in array."


def test_SpectrumBinner_set_generator_parameters():
    """Test if set_generator_parameters methods works well."""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0)
    assert ms2ds_data.generator_args == {}, "Settings should not yet be set."

    # Pass new setting (rest will be set to default)
    ms2ds_data.set_generator_parameters(batch_size=20, shuffle=False)
    generator_args = ms2ds_data.generator_args
    assert generator_args["batch_size"] == 20, "Expected different setting."
    assert generator_args["shuffle"] == False, "Expected different setting."
    assert generator_args["augment_peak_removal_intensity"] == 0.2, "Expected different setting."

    # Adapt settings a 2nd time
    ms2ds_data.set_generator_parameters(batch_size=10)
    generator_args = ms2ds_data.generator_args
    assert generator_args["batch_size"] == 10, "Expected different setting."
    assert generator_args["shuffle"] == True, "Expected different setting."


def test_SpectrumBinner_create_binned_spectrums():
    """Test if creating binned spectrums method works."""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0, peak_scaling=1.0)
    spectrum_1 = Spectrum(mz=np.array([10, 20, 50, 100.]),
                          intensities=np.array([0.7, 0.6, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_01"})
    spectrum_2 = Spectrum(mz=np.array([10, 30, 40, 90.]),
                          intensities=np.array([0.4, 0.5, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_02"})

    ms2ds_data.collect_binned_spectrums([spectrum_1, spectrum_2])
    assert ms2ds_data.known_bins == [10, 20, 30, 40, 50, 90, 100], "Expected different known bins."

    spectrum_3 = Spectrum(mz=np.array([10, 20, 30, 50.]),
                      intensities=np.array([0.4, 0.5, 0.2, 1.0]),
                      metadata={'inchikey': "test_inchikey_03"})
    spectrum_binned = ms2ds_data.create_binned_spectrums([spectrum_3])
    assert spectrum_binned[0] == {0: 0.4, 1: 0.5, 2: 0.2, 4: 1.0}, \
        "Expected different binned spectrum"


def test_SpectrumBinner_create_binned_spectrums_missing_fraction():
    """Test if creating binned spectrums method works if peaks are unknown."""
    ms2ds_data = SpectrumBinner(100, mz_min=0.0, mz_max=100.0, peak_scaling=1.0)
    spectrum_1 = Spectrum(mz=np.array([10, 20, 50, 100.]),
                          intensities=np.array([0.7, 0.6, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_01"})
    spectrum_2 = Spectrum(mz=np.array([10, 30, 40, 90.]),
                          intensities=np.array([0.4, 0.5, 0.2, 0.1]),
                          metadata={'inchikey': "test_inchikey_02"})

    ms2ds_data.collect_binned_spectrums([spectrum_1, spectrum_2])
    assert ms2ds_data.known_bins == [10, 20, 30, 40, 50, 90, 100], "Expected different known bins."

    spectrum_3 = Spectrum(mz=np.array([10, 20, 30, 80.]),
                      intensities=np.array([0.4, 0.5, 0.2, 1.0]),
                      metadata={'inchikey': "test_inchikey_03"})
    with pytest.raises(AssertionError) as msg:
        _ = ms2ds_data.create_binned_spectrums([spectrum_3])
    assert "weighted spectrum is unknown to the model"in str(msg.value), \
        "Expected different exception."
