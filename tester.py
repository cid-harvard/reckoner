from collections import defaultdict
import glob
import re
import sys
import string
import yaml
import pprint

import pandas as pd
import numpy as np

import logging
logging.basicConfig(format='%(levelname)s:  %(message)s', level=logging.INFO)
logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" % logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" % logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" % logging.getLevelName(logging.ERROR))


class GlobFormatter(string.Formatter):
    def get_value(self, key, args, kwargs):
        return "*"


class RegexFormatter(string.Formatter):
    UNIQ = '_UNIQUE_STRING_'

    def get_value(self, key, args, kwargs):
        return self.UNIQ + ('(?P<%s>.*?)' % key) + self.UNIQ

    @staticmethod
    def format_to_regex(pattern):
        parts = RegexFormatter().format(pattern).split(RegexFormatter.UNIQ)
        for i in range(0, len(parts), 2):
            parts[i] = re.escape(parts[i])
        return ''.join(parts)


class Ecomplexity(object):

    REQUIRED = {
        "year": int,
        "location": str,
        "entity": str,
        "value": float,
        "eci": float,
        "pci": float,
        "rca": float,
        "diversity": float,
        "density": float,
        "ubiquity": float,
        "average_ubiquity": float,
        "cog": float,
        "coi": float,
    }

    def check_field_mappings(self, mappings):
        return set(self.REQUIRED) - set(mappings)

    def check_fields(self, field_mappings, df):
        """Returns missing fields, extra fields"""
        return (set(field_mappings.values()) - set(df.columns), set(df.columns) - set(field_mappings.values()))


check_type = {"ecomplexity": Ecomplexity()}


def read_file(file_name):
    read_commands = {
        "dta": pd.read_stata,
        "csv": pd.read_csv,
        "tsv": pd.read_table,
        "txt": pd.read_table,
    }
    extension = file_name.rsplit(".", 1)[-1]
    return read_commands[extension](file_name)


def dtype_is_numeric(thing):
    return thing.dtype in [np.int8, np.int16, np.int32, np.int64, np.float16,
                           np.float32, np.float64]


def convert_column_type(col, digits=None, warnings=True):
    if dtype_is_numeric(col):
        if warnings:
            logging.warning("""The classification code field {} is numeric,
                            going to try to automatically convert it into a
                            string.""".format(col.name))
        if digits:
            col = col.map(lambda x: str(int(x)).zfill(digits))
            if warnings:
                logging.warning("""Zero filling from the left to {}
                                digits""".format(digits))
        else:
            col = col.map(lambda x: str(int(x)))
    return col


def has_nulls(df):
    return df.isnull().any().any()


def process_classification(df_class, classification_config):

    if "code_field" in classification_config:

        # Read config
        code_field = classification_config["code_field"]
        name_field = classification_config["name_field"]
        digits = classification_config.get("digits", None)

        # Get rid of fields and lines we don't need
        df_class = df_class[[code_field, name_field]]

        if has_nulls(df_class):
            logging.error("""Classification mapping {} contains null values in
                          relevant columns""".format(classification_config))
            sys.exit(1)

        # Convert codes to n-digit strings if necessary
        df_class[code_field] = convert_column_type(df_class[code_field], digits)

        df_class = df_class.drop_duplicates()


    elif "code_fields" in classification_config:

        name_field = classification_config["name_field"]

        # Get rid of fields we don't need
        code_fields = [f["name"] for f in classification_config["code_fields"]]
        df_class = df_class[code_fields + [name_field]]

        if has_nulls(df_class):
            logging.error("""Classification mapping {} contains null values in
                          relevant columns""".format(classification_config))
            sys.exit(1)

        # Fix up column types
        for field in classification_config["code_fields"]:
            code_field = field["name"]
            digits = field.get("digits", None)
            df_class[code_field] = convert_column_type(df_class[code_field], digits)

        # Merge all the fields to get the code
        def add_str_fields(field):
            return "".join([field[f] for f in code_fields])
        df_class["generated_classification"] =\
            df_class[code_fields].apply(add_str_fields, axis=1)

        # Return only the code and the name
        df_class = df_class[["generated_classification", name_field]]

    else:
        logging.error("""Classification mapping {} must have a code_field or
                         code_fields.""".format(classification_config))
        sys.exit(1)

    # Rename columns
    df_class.columns = ["code", "name"]

    # Make codes the index
    df_class = df_class.set_index("code")

    return df_class


if __name__ == "__main__":

    logging.info("Loading config file: %s", sys.argv[1])
    config = yaml.load(open(sys.argv[1]).read())

    file_pattern = config["file_pattern"]
    checker = check_type[config["type"]]
    logging.info("Using file pattern: %s", file_pattern)

    # Verify we have enough field mappings defined for a data file of the given
    # type
    field_mappings = dict(config["fields"])
    field_mappings.update(config["generated_fields"])
    missing_fields = checker.check_field_mappings(field_mappings)
    if len(missing_fields) != 0:
        logging.error("Field mapping unspecified for: %s", missing_fields)
        sys.exit(1)

    # Find files that match
    file_names = glob.glob(GlobFormatter().format(file_pattern))
    logging.info("Found %d files:\n %s",
                 len(file_names), pprint.pformat(file_names))

    # Extract data from filenames
    file_regex = RegexFormatter().format_to_regex(file_pattern)
    variations = [re.compile(file_regex).match(f).groupdict()
                  for f in file_names]
    logging.info("Variations gathered from files:\n %s",
                 pprint.pformat(variations))

    totals = {}

    # Check that all Location and Entity fields have mappings
    # {"location": ["est", "mun"], "entity": ["hs4_4digit"]}
    classifications = {}
    for field in ["location", "entity"]:
        if field not in config["classifications"]:
            logging.error("Please supply a classification for {} called {}."
                          .format(field, field))
            sys.exit(1)
        for classification, classification_config in config["classifications"][field].items():
            df_class = read_file(classification_config["file"])
            df_class = process_classification(df_class, classification_config)
            logging.info("Classification system for {}:\n {}"
                         .format(classification, df_class))
            if field not in classifications:
                classifications[field] = {}
            classifications[field][classification] = df_class

    for variation in variations:

        # Load file
        file_name = file_pattern.format(**variation)
        df = read_file(file_name)

        # Check file has all the fields specified
        field_mappings = dict(config["fields"])
        field_mappings = {k: v.format(**variation) for k, v in field_mappings.items()}
        missing_fields, extra_fields = checker.check_fields(field_mappings, df)
        if len(missing_fields) != 0:
            logging.error("File Name: %s, Missing fields: %s", file_name, missing_fields)
            sys.exit(1)
        if len(extra_fields) != 0:
            logging.warning("File Name: %s, Extra fields: %s", file_name, extra_fields)

        # Standardize column names
        df = df.rename(columns={v:k for k,v in field_mappings.items()})

        # TODO: standardize types?

        # Generate generated columns
        for k, v in config["generated_fields"].items():
            df[k] = v.format(**variation)

        # Get summary stats
        summary = "\nNumber of rows: {}\n".format(len(df.index))
        summary += "Number of locations: {}\n".format(df.location.nunique())
        summary += "Number of entities: {}\n".format(df.entity.nunique())
        summary += "Number of null locations: {}\n".format(df.location.isnull().sum())
        summary += "Number of null entities: {}\n".format(df.entity.isnull().sum())
        summary += "Number of null values: {}".format(df.value.isnull().sum())
        logging.info(summary)

        def get_classification_name(thing, variation, classifications):
            if thing not in variation:
                return classifications[thing].items()[0][0]
            else:
                return variation[thing]

        def get_classification(thing, variation, classifications):
            # if not in variations, get default one (e.g. hs4_4digit)
            if thing not in variation:
                return classifications[thing].items()[0][1]
            else:
                return classifications[thing][variation[thing]]

        def get_classification_configuration(thing, variation, classifications):
            if thing not in variation:
                return config["classifications"][thing].items()[0][1]
            else:
                return config["classifications"][thing][variation[thing]]


        # Calculate match percentages to classifications
        for thing in ["location", "entity"]:

            # Select only one col
            merge_col = df[[thing]]

            # Convert types
            digits = get_classification_configuration(
                thing,
                variation,
                classifications)["digits"]
            merge_col[thing] = convert_column_type(
                merge_col[thing],
                digits=digits,
                warnings=False
            )

            classification_name = get_classification_name(thing, variation,
                                                          classifications)
            classification = get_classification(thing, variation,
                                                classifications)

            merged = merge_col.merge(classification, left_on=thing,
                                     right_index=True, how="left")

            num_nonmerged = merged["name"].isnull().sum()

            # If everything merges perfectly, no need to tell
            if num_nonmerged == 0:
                continue

            percent_nonmerged = 100.0 * num_nonmerged / merge_col.shape[0]

            nonmerged_codes = merged[merged["name"].isnull()][thing].unique()
            summary = "\nNumber of nonmatching rows {}: {}\n".format(classification_name,
                                                                     num_nonmerged)
            summary = "\nPercent nonmatching rows {}: {}\n".format(classification_name,
                                                                   percent_nonmerged)
            summary += "Nonmatching codes: {}\n".format(nonmerged_codes)
            logging.info(summary)

            # Codes missing
            # Match percentage


        # Add current variation field value counts to running sum
        for k, v in variation.items():
            if v in totals:
                totals[v] = totals[v].add(df[k].value_counts(), fill_value=0)
            else:
                totals[v] = df[k].value_counts()

    # Counts of locations / entities across files
    for item in totals:
        totals[item].sort(ascending=False)
        logging.info("Value counts across all files for: {}\n{}".format(item, totals[item]))
