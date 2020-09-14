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
    CURRENT_DETAILS_PATTERN,
    PRE_2020_09_08_DETAILS_PATTERN,
    PRE_2020_09_04_DETAILS_PATTERN,
    PRE_2020_09_02_DETAILS_PATTERN,
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


def get_number(div):
    return div \
        .find('p', class_="renew-case-numbers-card__number") \
        .text \
        .strip()


def get_number_title(div):
    return div \
        .find('p', class_="renew-case-numbers-card__title") \
        .text \
        .strip() \
        .lower() \
        .replace(" ", "_")


def get_details(section):
    return section \
        .find("small", class_="renew-student-numbers__detail") \
        .text \
        .strip()

def get_row_number(row):
    return row \
        .text \
        .strip()


def parse_details(details):

    current_keys = {k: None for k in CURRENT_DETAILS_PATTERN.groupindex.keys()}

    match = (
        CURRENT_DETAILS_PATTERN.match(details)
     or PRE_2020_09_08_DETAILS_PATTERN.match(details)
     or PRE_2020_09_04_DETAILS_PATTERN.match(details)
     or PRE_2020_09_02_DETAILS_PATTERN.match(details)
    )

    if match:    
        parsed = {**current_keys, **match.groupdict()}
    else:
        # TODO: log that parse failed, will need to examine patterns
        parsed = current_keys

    return parsed

def parse_faculty_staff_table(content):
    faculty_staff_table = BeautifulSoup(content, 'html.parser') \
        .find('table', class_='table table-sm')

    faculty_staff_nums = faculty_staff_table \
        .find_all('td')

    faculty_staff_data = {
        'active_faculty_cases': get_row_number(faculty_staff_nums[0]),
        'recovered_faculty_cases': get_row_number(faculty_staff_nums[1]),
        'active_staff_cases': get_row_number(faculty_staff_nums[2]),
        'recovered_staff_cases': get_row_number(faculty_staff_nums[3])
        }

    return faculty_staff_data


def parse_html(content, recorded_at=RECORDED_AT):
    section = BeautifulSoup(content, 'html.parser') \
        .find('section', class_="renew-student-numbers")
    
    numbers_divs = section \
        .find_all('div', class_='renew-case-numbers-card')

    numbers_data = {
        get_number_title(div): get_number(div) for div in numbers_divs
        }

    details = get_details(section)
    details_data = parse_details(details)

    faculty_staff_data = parse_faculty_staff_table(content)

    data = {**numbers_data, **details_data, **faculty_staff_data}

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

def compare_archived(current_html, archived_data):
    current_data = parse_html(current_html)
    has_diffs = False

    most_recent = archived_data[0].items()
    for key, value in most_recent:
        if key == 'recorded_at':
            pass
        elif value != current_data[key]:
            has_diffs == True
            #print('Archived ' + key + ': ' + value + ', Current ' + key + ': ' + current_data[key])

    return has_diffs


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
    
    for key, value in archived_data[0]:
        print(key + ": " + value)
    
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
            if compare_archived(current_html, archived_data):
                data = [parse_html(current_html)] + archived_data

        archive_data(data)
        notify()


def lambda_handler(event, context):
    main()


if __name__ == '__main__':
    main()
