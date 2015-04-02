import glob
import os.path
import re
import sys
import yaml
import pprint

import logging
logging.basicConfig(
    format='%(levelname)s:  %(message)s',
    level=logging.INFO)
logging.addLevelName(logging.INFO, "\033[1;32m%s\033[1;0m" %
                     logging.getLevelName(logging.INFO))
logging.addLevelName(logging.WARNING, "\033[1;33m%s\033[1;0m" %
                     logging.getLevelName(logging.WARNING))
logging.addLevelName(logging.ERROR, "\033[1;41m%s\033[1;0m" %
                     logging.getLevelName(logging.ERROR))


from helpers import GlobFormatter, RegexFormatter
from helpers import (dtype_is_numeric, read_file, has_nulls, canonical_path)

from file_types import file_types


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
    definition_file_path = canonical_path(sys.argv[1])
    base_path = os.path.dirname(definition_file_path)
    config = yaml.load(open(definition_file_path).read())

    file_pattern = config["file_pattern"]
    checker = file_types[config["type"]]
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
    file_pattern = os.path.join(base_path, file_pattern)
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
            df_class = read_file(os.path.join(base_path, classification_config["file"]))
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
            merge_col = df[[thing, "value"]]

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
            value_nonmerged = merged[merged["name"].isnull()].value.sum()
            percent_value_nonmerged = 100.0 * value_nonmerged / merge_col.value.sum()

            nonmerged_codes = merged[merged["name"].isnull()][thing].unique()
            summary = "\nNumber of nonmatching rows {}: {}\n".format(classification_name,
                                                                     num_nonmerged)
            summary += "Percent nonmatching rows {}: {}\n".format(classification_name,
                                                                   percent_nonmerged)
            summary += "Value of nonmatching rows {}: {}\n".format(classification_name,
                                                                   value_nonmerged)
            summary += "Percent value of nonmatching rows {}: {}\n".format(classification_name,
                                                                   percent_value_nonmerged)
            summary += "Nonmatching codes: {}\n".format(nonmerged_codes)
            logging.info(summary)

        # Add current variation field value counts to running sum
        for k, v in variation.items():
            if v in totals:
                totals[v] = totals[v].add(df[k].value_counts(dropna=False), fill_value=0)
            else:
                totals[v] = df[k].value_counts(dropna=False)

    # Counts of locations / entities across files
    for item in totals:
        totals[item].sort(ascending=False)
        logging.info("Value counts across all files for: {}\n{}".format(item, totals[item]))
