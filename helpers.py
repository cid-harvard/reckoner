import re
import string


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
