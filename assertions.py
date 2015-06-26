import numpy as np
import pandas as pd


def num_missing(series):
    return series.isnull().sum()


def assert_none_missing(series):
    missing_count = num_missing(series)
    assert missing_count == 0


def assert_is_zeropadded_string(series):

    # Must be a string
    assert series.dtype in [np.object, np.str]

    # All entries in this column must be same length
    assert (series.str.len().nunique() == 1)


def num_nonmatching_classification_level(series, classification_level):

    assert_is_zeropadded_string(series)
    assert_is_zeropadded_string(classification_level.code)

    is_in_classification = series.isin(classification_level.code)
    num_nonmatching = is_in_classification.value_counts().get(False, 0)
    return num_nonmatching


def assert_matches_classification_level(series, classification_level):
    assert num_nonmatching_classification_level(series, classification_level) == 0


def fillin(df, entities):
    """STATA style "fillin", make sure all permutations of entities in the
    index are in the dataset."""
    df = df.set_index(entities)
    return df.reindex(
        pd.MultiIndex.from_product(df.index.levels, names=df.index.names))


def assert_filled_in(df):
    """Check if all possibilities of all entities have been used"""
    pass

# Somehow make sure that nulls haven't been turned into zeroes. Maybe count the number of zero fields?
