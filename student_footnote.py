import re


NET_CHANGES = re.compile(
    r"\*(Net )?(C|c)hange in active cases from (?P<student_cases_change_since>(\w{6,9}\, [A-z]{3,4}\. \d{1,2})|\w+)\: (?P<student_cases_change>(\+|\-)?\d+((,\d+)+)?)\."
    )

BOONE_COUNTY = re.compile(
    r"(?P<student_cases_change_boone_county>\d+((,\d+)+)?) new cases are part of (?P<student_cases_boone_county>\d+((,\d+)+)?) student cases that have been reported in Boone County since Aug\. 19, 2020"
    )

BOONE_COUNTY_OLD = re.compile(
    r"\*A total of (?P<student_cases_boone_county>\d+((,\d+)+)?) student cases have been reported in Boone County since Aug\. 19, 2020",
    )

LAST_UPDATE = re.compile(
    r"Student case numbers last updated (?P<last_update_date>[A-z]{3,4}\. \d{1,2}) at (?P<last_update_time>.+)\."
)


def parse_from_pattern(text, pattern, alt_pattern=None):
    if alt_pattern:
        match = pattern.search(text) or alt_pattern.search(text)
    else:
        match = pattern.search(text)

    if match:
        data = match.groupdict()
    else:
        keys = [k for k in pattern.groupindex.keys()]
        data = {k: None for k in keys}

    return data


def parse(text):
    return {
        **parse_from_pattern(text, NET_CHANGES),
        **parse_from_pattern(text, BOONE_COUNTY, alt_pattern=BOONE_COUNTY_OLD),
        **parse_from_pattern(text, LAST_UPDATE)
    }
