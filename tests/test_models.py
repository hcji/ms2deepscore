import numpy as np
from tensorflow import keras

from ms2deepscore.data_generators import DataGeneratorAllInchikeys
from ms2deepscore.models import SiameseModel
from tests.test_data_generators import create_test_data


def get_test_generator():
    # Get test data
    spectrums_binned, score_array, inchikey_score_mapping, inchikeys_all = create_test_data()

    dimension = 101
    same_prob_bins = [(0, 0.5), (0.5, 1)]
    inchikey_ids = list(np.arange(0, 80))

    # Create generator
    test_generator = DataGeneratorAllInchikeys(spectrums_binned, score_array, inchikey_ids,
                                               inchikey_score_mapping, inchikeys_all,
                                               dim=dimension,
                                               same_prob_bins=same_prob_bins)
    return test_generator


def test_siamese_model():
    test_generator = get_test_generator()
    model = SiameseModel(input_dim=101, base_dims=(200, 200, 200), embedding_dim=200,
                         dropout_rate=0.2)
    model.compile(loss='mse', optimizer=keras.optimizers.Adam(lr=0.001))
    model.summary()
    x, y = zip(*test_generator)
    model.fit(x=x, y=y,
              validation_data=(x, y),
              epochs=2)