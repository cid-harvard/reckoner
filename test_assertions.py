import pandas as pd
import classification
import assertions


df = pd.read_stata("/Users/makmana/ciddata/PILA_andres/COL_PILA_ecomp-E_yir_2008-2012_rev3_dpto.dta")
df = df[df.i != "."]

industry_classification = classification.load("industry/ISIC/Colombia/out/isic_ac_3.0.csv")
location_classification = classification.load("location/Colombia/DANE/out/locations_colombia_dane.csv")


def test_entities_not_missing():
    for field in ["r", "i"]:
        assertions.assert_none_missing(df[field])


def test_entities_zeropadded_string():
    for field in ["r", "i"]:
        assertions.assert_is_zeropadded_string(df[field])


def test_matching_classifications():
    classifications = {
        "i": industry_classification.level("class"),
        "r": location_classification.level("department")
    }

    for field, level in classifications.items():
        assertions.assert_matches_classification_level(df[field], level)


def test_matching_stats():
    classifications = {
        "i": industry_classification.level("class"),
        "r": location_classification.level("department")
    }

    for field, level in classifications.items():
        (percent_nonmatch_rows, percent_nonmatch_unique, codes_missing,
         codes_unused) = assertions.matching_stats(df[field], level)
        assert percent_nonmatch_rows == 0
        assert percent_nonmatch_unique == 0
        assert codes_missing.empty
        assert codes_unused.empty


def test_rectangularized():
    assertions.assert_filled_in(df, ["i", "r", "year"])
