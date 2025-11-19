import re


def resolve_table_name(class_name: str) -> str:
    name = re.split('(?=[A-Z])', class_name)
    return '_'.join([x.lower() for x in name if x])
