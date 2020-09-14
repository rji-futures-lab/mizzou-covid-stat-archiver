import csv
from datetime import datetime
from operator import itemgetter
import os
from time import sleep
import boto3
from bs4 import BeautifulSoup
from slack import WebClient
import requests
from regex import (
    CURRENT_STUDENT_FOOTNOTE_PATTERN,
    PRE_2020_09_08_STUDENT_FOOTNOTE_PATTERN,
    PRE_2020_09_04_STUDENT_FOOTNOTE_PATTERN,
    PRE_2020_09_02_STUDENT_FOOTNOTE_PATTERN,
)


S3_CLIENT = boto3.client('s3')
RECORDED_AT = datetime.now()
PROJECT_NAME = os.getenv('PROJECT_NAME')


class Pipe:
    value = ""
    def write(self, text):
        self.value = self.value + text


def get_current_html():
    r = requests.get("https://renewal.missouri.edu/student-cases/")
    r.raise_for_status()

    return r.content


def get_cached_html(key='cache/latest.html'):
    params = {
        'Bucket': PROJECT_NAME,
        'Key': key
    }
    response = S3_CLIENT.get_object(**params)

    return response['Body'].read()


def write_to_s3(key, content, content_type):
    params = {
        'Bucket': PROJECT_NAME,
        'ACL': 'public-read',
        'Key': key,
        'Body': content,
        'ContentType': f"{content_type}; charset=UTF-8"
    }
    return S3_CLIENT.put_object(**params)


def cache_html(content):
    write_to_s3(
        'cache/latest.html', content, 'text/html'
        )
    write_to_s3(
        f'cache/{RECORDED_AT}.html', content, 'text/html'
        )


def format_label(label):
    return label \
        .replace(" ", "_") \
        .lower() \
        .strip()


def get_student_stat(div):
    return div \
        .find('p', class_="renew-case-numbers-card__number") \
        .text \
        .strip()


def get_student_stat_title(div):
    title = div \
        .find('p', class_="renew-case-numbers-card__title") \
        .text

    return format_label(title)


def get_student_footnote(section):
    return section \
        .find("small", class_="renew-student-numbers__detail") \
        .text \
        .strip()


def parse_student_footnote(details):

    current_keys = {
        k: None for k in CURRENT_STUDENT_FOOTNOTE_PATTERN.groupindex.keys()
        }

    match = (
        CURRENT_STUDENT_FOOTNOTE_PATTERN.match(details)
     or PRE_2020_09_08_STUDENT_FOOTNOTE_PATTERN.match(details)
     or PRE_2020_09_04_STUDENT_FOOTNOTE_PATTERN.match(details)
     or PRE_2020_09_02_STUDENT_FOOTNOTE_PATTERN.match(details)
    )

    if match:    
        parsed = {**current_keys, **match.groupdict()}
    else:
        # TODO: log that parse failed, will need to examine patterns
        parsed = current_keys

    return parsed


def parse_student_section(section):
    stat_divs = section.find_all('div', class_='renew-case-numbers-card')

    stats_data = {
        get_student_stat_title(div): get_student_stat(div) for div in stat_divs
        }

    footnote = get_student_footnote(section)
    footnote_data = parse_student_footnote(footnote)

    data = {**stats_data, **footnote_data}

    return data


def parse_table_row(row):
    row_label = format_label(row.find('th').text)

    numbers = [td.text.strip() for td in row.find_all('td')]

    return row_label, numbers


def parse_faculty_staff_table(table):
    table_headers = table \
        .find('thead') \
        .find_all('th')

    column_labels = [
        format_label(th.text) for th in table_headers if len(th.text) > 0
        ]

    table_rows = table \
        .find('tbody') \
        .find_all('tr')

    data = {}

    for tr in table_rows:
        row_label, numbers = parse_table_row(tr)

        zipped = zip([f"{row_label}_{cl}" for cl in column_labels], numbers)

        for k, v in zipped:
            data[k] = v

    return data


def parse_html(content, recorded_at=RECORDED_AT):
    
    soup = BeautifulSoup(content, 'html.parser')

    student_section = soup.find('section', class_="renew-student-numbers")
    faculty_staff_table = soup.find('table', class_='table table-sm')
    
    student_data = parse_student_section(student_section)
    faculty_staff_data = parse_faculty_staff_table(faculty_staff_table)

    data = {**student_data, **faculty_staff_data}

    data['recorded_at'] = recorded_at

    return data


def get_archived_data():
    params = {
        'Bucket': PROJECT_NAME,
        'Key': 'data.csv'
    }
    response = S3_CLIENT.get_object(**params)
    
    lines = [
        # check if needed
        l.decode('utf-8') for l in response['Body'].iter_lines()
        ]

    data = [
        d for d in csv.DictReader(lines)
        ]

    return sorted(data, key=itemgetter('recorded_at'), reverse=True)


def archive_data(data):
    pipe = Pipe()
    
    headers = data[0].keys()
    writer = csv.DictWriter(pipe, headers)
    writer.writeheader()
    
    for row in data:
        writer.writerow(row)

    return write_to_s3('data.csv', pipe.value, 'text/csv')


def notify():
    slack_client = WebClient(token=os.getenv('SLACK_BOT_TOKEN'))
    csv_url = f"https://{PROJECT_NAME}.s3.{S3_CLIENT.meta.region_name}.amazonaws.com/data.csv"
    text = f"Mizzou just dropped new Covid stats. Download the archived data 👉 {csv_url}."
    params = {
        'channel': "#mizzoucollab",
        'text': text
    }

    return slack_client.chat_postMessage(**params)


def main():
    current_html = get_current_html()
    
    try:
        cached_html = get_cached_html()
    except S3_CLIENT.exceptions.NoSuchKey:
        has_diffs = True
    else:
        has_diffs = current_html != cached_html
    
    if has_diffs:
        cache_html(current_html)
        
        try:
            archived_data = get_archived_data()
        except S3_CLIENT.exceptions.NoSuchKey:
            data = [parse_html(current_html)]
        else:
            data = [parse_html(current_html)] + archived_data

        archive_data(data)
        notify()


def lambda_handler(event, context):
    main()


if __name__ == '__main__':
    main()
