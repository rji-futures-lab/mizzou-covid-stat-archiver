import re


NET_CHANGES = re.compile(
    r"\*(Net )?(C|c)hange in active cases [a-z]+ (?P<student_cases_change_since>(\w{6,9}\, [A-z]{3,4}\. \d{1,2})|\w+)\: (?P<student_cases_change>(\+|\-|([A-Z]+ ))?\d+((,\d+)+)?)\."
    )

BOONE_COUNTY_TOTAL = re.compile(
    r"are part of (?P<student_cases_boone_county>\d+((,\d+)+)?) student cases that have been reported in Boone County since Aug\. 19, 2020"
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


def parse_from_pattern(text, pattern, alt_patterns=None):
    if alt_patterns:
        match = pattern.search(text)
        if not match:
            for p in alt_patterns:
                match = p.search(text)
                if match:
                    break
                    print('hi')
    else:
        match = pattern.search(text)

    keys = [k for k in pattern.groupindex.keys()]
    missing_data = {k: None for k in keys}
    
    if match:
        data = {**missing_data, **match.groupdict()}
    else:
        data = missing_data

    return data


def parse(text):
    return {
        **parse_from_pattern(text, NET_CHANGES),
        **parse_from_pattern(
            text, BOONE_COUNTY, alt_patterns=[BOONE_COUNTY_OLD, BOONE_COUNTY_TOTAL]
            ),
        **parse_from_pattern(text, LAST_UPDATE)
    }
