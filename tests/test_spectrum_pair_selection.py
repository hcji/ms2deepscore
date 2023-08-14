import numpy as np
import pytest
from scipy.sparse import coo_array
from matchms import Spectrum
from ms2deepscore.spectrum_pair_selection import (
    compute_jaccard_similarity_matrix_cherrypicking,
    compute_spectrum_pairs,
    jaccard_similarity_matrix_cherrypicking,
    select_inchi_for_unique_inchikeys,
    SelectedCompoundPairs
    )


@pytest.fixture
def simple_fingerprints():
    return np.array([
        [1, 1, 0, 0],
        [1, 0, 1, 0],
        [0, 1, 1, 1],
        [0, 0, 1, 1],
    ], dtype=bool)


@pytest.fixture
def fingerprints(): 
    return np.array([
        [1, 1, 0, 0, 1, 1],
        [1, 0, 1, 0, 1, 1],
        [0, 1, 1, 1, 1, 1],
        [0, 0, 1, 1, 1, 1],
        [1, 1, 0, 0, 0, 1],
        [1, 0, 1, 0, 0, 1],
        [0, 1, 1, 1, 1, 0],
        [0, 0, 1, 1, 1, 0],
    ], dtype=bool)


@pytest.fixture
def spectrums():
    metadata = {"precursor_mz": 101.1,
                "inchikey": "ABCABCABCABCAB-nonsense",
                "inchi": "InChI=1/C6H8O6/c7-1-2(8)5-3(9)4(10)6(11)12-5/h2,5,7-10H,1H2/t2-,5+/m0/s1"}
    spectrum_1 = Spectrum(mz=np.array([100.]),
                          intensities=np.array([0.7]),
                          metadata=metadata)
    spectrum_2 = Spectrum(mz=np.array([90.]),
                          intensities=np.array([0.4]),
                          metadata=metadata)
    spectrum_3 = Spectrum(mz=np.array([90.]),
                          intensities=np.array([0.4]),
                          metadata=metadata)
    spectrum_4 = Spectrum(mz=np.array([90.]),
                          intensities=np.array([0.4]),
                          metadata={"inchikey": 14 * "X",
                                    "inchi": "InChI=1S/C8H10N4O2/c1-10-4-9-6-5(10)7(13)12(3)8(14)11(6)2/h4H,1-3H3"})
    return [spectrum_1, spectrum_2, spectrum_3, spectrum_4]


@pytest.fixture
def dummy_data():
    data = np.array([0.5, 0.7, 0.3, 0.9, 0.8, 0.2, 0.6, 1.0])
    row = np.array([0, 1, 1, 1, 3, 4, 5, 6])  # 2 missing on purpose
    col = np.array([0, 2, 3, 4, 6, 5, 2, 6])
    inchikeys = ["Inchikey0", "Inchikey1", "Inchikey2", "Inchikey3", "Inchikey4", "Inchikey5", "Inchikey6"]
    return data, row, col, inchikeys


def test_basic_functionality(simple_fingerprints):
    matrix = jaccard_similarity_matrix_cherrypicking(simple_fingerprints, random_seed=42)
    assert matrix.shape == (4, 4)
    assert np.allclose(matrix.diagonal(), 1.0)
    assert matrix.nnz > 0  # Make sure there are some non-zero entries


def test_exclude_diagonal(simple_fingerprints):
    matrix = jaccard_similarity_matrix_cherrypicking(simple_fingerprints, include_diagonal=False, random_seed=42)
    diagonal = matrix.diagonal()
    assert np.all(diagonal == 0)  # Ensure no non-zero diagonal elements


def test_correct_counts(fingerprints):
    matrix = jaccard_similarity_matrix_cherrypicking(fingerprints)
    expected_histogram = np.array([6,  8,  2, 10,  8, 14,  0,  8,  0,  8])
    assert np.all(np.histogram(matrix.todense(), 10)[0] == expected_histogram)


def test_global_bias(fingerprints):
    bins = np.array([(0, 0.5), (0.5, 0.8), (0.8, 1.0)])
    data, _, _ = compute_jaccard_similarity_matrix_cherrypicking(fingerprints,
                                                                 selection_bins=bins,
                                                                 max_pairs_per_bin=1)
    data = np.array(data)
    assert (data <= 0.5).sum() == ((data>0.5) & (data<=0.8)).sum() == (data>0.8).sum() == 8


def test_global_bias_not_possible(fingerprints):
    bins = np.array([(0, 0.5), (0.5, 0.8), (0.8, 1.0)])
    # Test uncompiled function
    data, _, _ = compute_jaccard_similarity_matrix_cherrypicking.py_func(
        fingerprints,
        selection_bins=bins,
        max_pairs_per_bin=2)
    data = np.array(data)
    assert (data <= 0.5).sum() == ((data>0.5) & (data<=0.8)).sum() == 16
    assert (data>0.8).sum() == 8

    # Test compiled function
    data, _, _ = compute_jaccard_similarity_matrix_cherrypicking(
        fingerprints,
        selection_bins=bins,
        max_pairs_per_bin=2)
    data = np.array(data)
    assert (data <= 0.5).sum() == ((data>0.5) & (data<=0.8)).sum() == 16
    assert (data>0.8).sum() == 8


def test_select_inchi_for_unique_inchikeys(spectrums):
    spectrums[2].set("inchikey", "ABCABCABCABCAB-nonsense2")
    spectrums[3].set("inchikey", "ABCABCABCABCAB-nonsense3")
    (spectrums_selected, inchikey14s) = select_inchi_for_unique_inchikeys(spectrums)
    assert inchikey14s == ['ABCABCABCABCAB']
    assert spectrums_selected[0].get("inchi").startswith("InChI=1/C6H8O6/")


def test_select_inchi_for_unique_inchikeys_two_inchikeys(spectrums):
    # Test for two different inchikeys
    (spectrums_selected, inchikey14s) = select_inchi_for_unique_inchikeys(spectrums)
    assert inchikey14s == ['ABCABCABCABCAB', 'XXXXXXXXXXXXXX']
    assert [s.get("inchi")[:15] for s in spectrums_selected] == ['InChI=1/C6H8O6/', 'InChI=1S/C8H10N']


def test_compute_spectrum_pairs(spectrums):
    scores = compute_spectrum_pairs(spectrums)
    assert np.allclose(scores.row, [0, 0, 1, 1])
    assert np.allclose(scores.col, [1, 0, 0, 1])
    assert np.allclose(scores.data, [0.1665089877010407, 1.0, 0.1665089877010407, 1.0])


def test_compute_spectrum_pairs_vary_parameters(spectrums):
    # max_pairs_per_bin = 1
    scores = compute_spectrum_pairs(spectrums, max_pairs_per_bin=1, nbits=10)
    assert scores.shape == (2, 2)
    assert len(scores.row) == 2
    assert np.allclose(scores.data, [1.0, 1.0])
    # max_pairs_per_bin = 2
    scores = compute_spectrum_pairs(spectrums, max_pairs_per_bin=2, nbits=10)
    assert scores.shape == (2, 2)
    assert len(scores.row) == 4
    assert np.allclose(scores.data, [1.0, 1.0, 1.0, 1.0])


# Test SelectedCompoundPairs class
def test_SCP_initialization(dummy_data):
    data, row, col, inchikeys = dummy_data
    coo = coo_array((data, (row, col)))
    scp = SelectedCompoundPairs(coo, inchikeys)

    assert len(scp._cols) == len(inchikeys)
    assert len(scp._scores) == len(inchikeys)
    assert scp._idx_to_inchikey[0] == "Inchikey0"
    assert scp._inchikey_to_idx["Inchikey0"] == 0


def test_SCP_shuffle(dummy_data):
    data, row, col, inchikeys = dummy_data
    coo = coo_array((data, (row, col)))
    scp = SelectedCompoundPairs(coo, inchikeys, shuffling=False)

    original_cols = [r.copy() for r in scp._cols]
    original_scores = [s.copy() for s in scp._scores]

    scp.shuffle()

    # Check that the data has been shuffled
    assert not all(np.array_equal(o, n) for o, n in zip(original_cols, scp._cols))
    assert not all(np.array_equal(o, n) for o, n in zip(original_scores, scp._scores))


def test_SCP_next_pair_for_inchikey(dummy_data):
    data, row, col, inchikeys = dummy_data
    coo = coo_array((data, (row, col)))
    scp = SelectedCompoundPairs(coo, inchikeys, shuffling=False)

    score, inchikey2 = scp.next_pair_for_inchikey("Inchikey1")
    assert score == 0.7
    assert inchikey2 == "Inchikey2"

    score, inchikey2 = scp.next_pair_for_inchikey("Inchikey1")
    assert scp._row_generator_index[1] == 2
    assert score == 0.3
    assert inchikey2 == "Inchikey3"

    # Test wrap around
    scp._row_generator_index[1] = 0
    score, inchikey2 = scp.next_pair_for_inchikey("Inchikey1")
    assert score == 0.7
    assert inchikey2 == "Inchikey2"
