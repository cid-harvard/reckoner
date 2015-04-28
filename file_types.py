class FileType(object):

    def check_field_mappings(self, mappings):
        return set(self.REQUIRED) - set(mappings)

    def check_fields(self, field_mappings, df):
        """Returns missing fields, extra fields"""
        return (set(field_mappings.values()) - set(df.columns),
                set(df.columns) - set(field_mappings.values()))


class Ecomplexity(FileType):
    """Format dumped out from the `ecomplexity` command in STATA."""

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


class CPY(FileType):
    """Location - entity - year."""

    REQUIRED = {
        "location": str,
        "entity": str,
        "year": int,
        "value": float,
    }

file_types = {
    "ecomplexity": Ecomplexity(),
    "cpy": CPY()
}
