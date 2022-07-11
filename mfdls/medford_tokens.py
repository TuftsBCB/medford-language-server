"""medford_tokens.py

By: Liam Strand
On: July 2022

Extracts the tokens from the medford parser in a way that is useful for autocompletion
and syntax highlighting.
"""

from typing import Dict, List

# Entity contains all of the information about the possible tokens
from MEDFORD.medford_models import Entity

# These are the tokens that signify that we should treat the apparently minor
# tokens instead as data provenanace extensions to the major token.
_DATA_PROV_NAMES = set(("Ref", "Copy", "Primary"))

# These constants are keys in the Entity schema, we keep them up here in
# constants so that we don't make typos later on.
_SCHEMA_DEFS = "definitions"
_SCHEMA_DEFS_PATH = _SCHEMA_DEFS + "/"
_SCHEMA_ITEMS = "items"
_SCHEMA_PROPS = "properties"
_SCHEMA_TITLE = "title"
_SCHEMA_REF = "$ref"


def get_available_tokens() -> Dict[str, List[str]]:
    """Examines MEDFORD.medford_models.Entity to determine the token structure
    Parameters: None
       Returns: A dict mapping major tokens to their associated minor tokens
       Effects: None
    """
    data = Entity.schema()
    defs = data[_SCHEMA_DEFS]
    majors = data[_SCHEMA_PROPS]

    tokens = {}

    for major in majors.values():
        if major[_SCHEMA_TITLE] != "Freeform":
            some_tokens = _get_minor_tokens(major, defs)
            tokens.update(some_tokens)

    return tokens


def _get_minor_tokens(major: Dict, definitions: Dict) -> Dict[str, List[str]]:
    """Extract and return a major token's associate minor tokens
    Parameters: A major token (from the properties section of the schema)
                The definitions section of the schema
       Returns: A dictionary mapping major tokens to associated minor tokens
       Effects: None
         Notes: For data provenance tokens, there are more than one key/value
                pair in the dictionary.
    """
    major_name = major[_SCHEMA_TITLE]

    def_path = next(
        ref[_SCHEMA_REF]
        for ref in major[_SCHEMA_ITEMS][_SCHEMA_ITEMS]
        if _SCHEMA_REF in ref.keys()
    )
    def_name = def_path.split(_SCHEMA_DEFS_PATH)[-1]

    minors = _extract_minors_from_def(definitions[def_name])

    if major_name == "Medford":
        major_name = "MEDFORD"

    if set(minors) == _DATA_PROV_NAMES:
        return _data_prov_minors(major, definitions)
    else:
        return {major_name: minors}


def _extract_minors_from_def(definition: Dict) -> List[str]:
    """Takes the definition of a major token and extracts the associated minor tokens
    Parameters: A major token's definition
       Returns: A list of minor tokens
       Effects: None
    """
    minors = list(definition[_SCHEMA_PROPS].keys())

    if "desc" in minors:
        minors.remove("desc")
    if ("Destination" in minors or "URI" in minors) and "outpath" in minors:
        minors.remove("outpath")

    return minors


def _data_prov_minors(major: Dict, definitions: Dict) -> Dict[str, List[str]]:
    """Handles the additional dereferencing needed to parse data provenance tokens
    Parameters: A major token (from the properties section of the schema)
                The definitions section of the schema
       Returns: A dict mapping major tokens to their associated minor tokens
       Effects: None
    """

    big_major = major[_SCHEMA_TITLE]

    props = definitions[big_major][_SCHEMA_PROPS].values()

    # This is just the horrible way python makes you find the first occourance
    # of a thing in a list.
    # We are getting a list of references to data provenance token definitions
    paths = [
        next(
            ref[_SCHEMA_REF]
            for ref in prov_token[_SCHEMA_ITEMS][_SCHEMA_ITEMS]
            if _SCHEMA_REF in ref.keys()
        )
        for prov_token in props
    ]

    token_dict = {}

    all_minors = set()

    for path in paths:
        def_name = path.split(_SCHEMA_DEFS_PATH)[-1]
        major_name = _form_data_prov_major_name(big_major, def_name)
        minors = _extract_minors_from_def(definitions[def_name])
        token_dict[major_name] = minors
        all_minors.update(set(minors))

    token_dict[big_major] = list(all_minors)

    return token_dict


def _form_data_prov_major_name(big_major: str, def_name: str) -> str:
    """Rejoins the data provenance tokens' to form the proper major token name
    Parameters: The major token's type and its provenance
       Returns: The name of the major token
       Effects: None
    """
    major_name_parts = def_name.split("_")[1:]
    major_name_parts.insert(0, big_major)
    major_name = "_".join(major_name_parts)
    return major_name


# This is just here for testing, we don't want to run this as a script
if __name__ == "__main__":
    from pprint import pprint

    pprint(get_available_tokens())
