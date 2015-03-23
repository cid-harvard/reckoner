import glob
import re
import sys
import string
import yaml
import pprint

import pandas as pd

import logging
logging.basicConfig(format='%(levelname)s:\n%(message)s', level=logging.INFO)
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
    file_names = GlobFormatter().format(file_pattern)
    file_names = glob.glob(file_names)
    logging.info("Found files:\n %s", pprint.pformat(file_names))

    # Extract data from filenames
    file_regex = RegexFormatter().format_to_regex(file_pattern)
    variations = [re.compile(file_regex).match(f).groupdict()
                  for f in file_names]
    logging.info("Variations gathered from files: %s", pprint.pformat(variations))


    for variation in variations:

        # Load file
        file_name = file_pattern.format(**variation)
        read_commands = {
            "dta": pd.read_stata,
            "csv": pd.read_csv,
            "tsv": pd.read_table,
            "txt": pd.read_table,
        }
        extension = file_name.rsplit(".", 1)[-1]
        df = read_commands[extension](file_name)

        # Check file has all the fields specified
        field_mappings = dict(config["fields"])
        field_mappings = {k: v.format(**variation) for k, v in field_mappings.items()}
        missing_fields, extra_fields = checker.check_fields(field_mappings, df)
        if len(missing_fields) != 0:
            logging.error("File Name: %s, Missing fields: %s", file_name, missing_fields)
            sys.exit(1)
        if len(extra_fields) != 0:
            logging.warning("File Name: %s, Extra fields: %s", file_name, extra_fields)

        df = df.rename(columns={v:k for k,v in field_mappings.items()})
        print "Locations: ", df.location.nunique()
        print "Entities: ", df.entity.nunique()
