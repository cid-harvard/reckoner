import re
import string

import numpy as np
import pandas as pd


class GlobFormatter(string.Formatter):
    """Formats strings as a glob.glob pattern with a * instead of each format
    element like {foo}"""
    def get_value(self, key, args, kwargs):
        return "*"


class RegexFormatter(string.Formatter):
    """Formats strings like a regex - replaces each {foo} with a regex that
    captures .* in that gap and assigns it the name foo."""

    UNIQ = '_UNIQUE_STRING_'

    def get_value(self, key, args, kwargs):
        return self.UNIQ + ('(?P<%s>.*?)' % key) + self.UNIQ

    @staticmethod
    def format_to_regex(pattern):
        parts = RegexFormatter().format(pattern).split(RegexFormatter.UNIQ)
        for i in range(0, len(parts), 2):
            parts[i] = re.escape(parts[i])
        return ''.join(parts)


def dtype_is_numeric(thing):
    return thing.dtype in [np.int8, np.int16, np.int32, np.int64, np.float16,
                           np.float32, np.float64]


def read_file(file_name):
    read_commands = {
        "dta": pd.read_stata,
        "csv": pd.read_csv,
        "tsv": pd.read_table,
        "txt": pd.read_table,
    }
    extension = file_name.rsplit(".", 1)[-1]
    return read_commands[extension](file_name)


def has_nulls(df):
    return df.isnull().any().any()
