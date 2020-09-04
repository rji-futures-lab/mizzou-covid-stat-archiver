import re


PRE_2020_09_02_DETAILS_PATTERN = re.compile(
    r"^\*A total of (?P<student_cases_boone_county>\d+((,\d+)+)?) student cases have been reported in Boone County since Aug\. 19, 2020, the first date the university began receiving data from the public health department \(approximately one week after student move-in\)\. This information is based on cases tested and confirmed at the MU Student Health Center and other testing locations in Boone County, as identified by the Columbia\/Boone County Public Health Department and shared with the university\. If a student tests positive in Boone County, but isolates or quarantines outside of the county, they are no longer tracked as active or recovered cases within Boone County\. Likewise, if a student tests positive in another county, but chooses to isolate in Boone County, that student will not be reflected in cumulative cases\. Student case numbers last updated (?P<last_update_date>[A-z]{3,4}\. \d{1,2}) at (?P<last_update_time>.+)\.$"
    )


CURRENT_DETAILS_PATTERN = re.compile(
    r"^\*(Net )?(C|c)hange in active cases from yesterday\: (?P<student_cases_change>\d+((,\d+)+)?)\. (?P<student_cases_change_boone_county>\d+((,\d+)+)?) new cases are part of (?P<student_cases_boone_county>\d+((,\d+)+)?) student cases that have been reported in Boone County since Aug\. 19, 2020, the first date the university began receiving data from the public health department \(approximately one week after student move-in\)\. This information is based on cases tested and confirmed at the MU Student Health Center and other testing locations in Boone County, as identified by the Columbia\/Boone County Public Health Department and shared with the university\. If a student tests positive in Boone County, but isolates or quarantines outside of the county, they are no longer tracked as active or recovered cases within Boone County\. Likewise, if a student tests positive in another county, but chooses to isolate in Boone County, that student will not be reflected in cumulative cases\. Student case numbers last updated (?P<last_update_date>[A-z]{3,4}\. \d{1,2}) at (?P<last_update_time>.+)\.$"
    )
