import csv
from datetime import datetime
from operator import itemgetter
import os
import re
import boto3
from bs4 import BeautifulSoup
import requests
from consts import DETAILS_PATTERN


S3_CLIENT = boto3.client('s3')
S3_DEFAULT_PARAMS = {
    'Bucket': os.getenv('PROJECT_NAME'),
    'Key': 'data.csv',
}


class Pipe:
    value = ""
    def write(self, text):
        self.value = self.value + text


def get_html():
    url = "https://renewal.missouri.edu/student-cases/"
    r = requests.get(url)
    r.raise_for_status()

    return r.content


def format_number(number_str):
    if "," in number_str:
        cleaned = number_str.replace(",", "")
        formatted = int(cleaned)
    elif "%" in number_str:
        cleaned = number_str \
            .replace("%", "") \
            .strip()
        formatted = float(cleaned)
    else:
        formatted = int(number_str)

    return formatted


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


def parse_details(details):
    match = DETAILS_PATTERN.match(details)

    if not match:
        raise Exception
    else:
        parsed = match.groupdict()
    
    return parsed


def parse_html(content):
    section = BeautifulSoup(content, "html.parser") \
        .find('section', class_="renew-student-numbers")
    
    numbers_divs = section \
        .find_all('div', class_='renew-case-numbers-card')

    numbers_data = {
        get_number_title(div): get_number(div) for div in numbers_divs
        }

    details = get_details(section)
    details_data = parse_details(details)

    data = {**numbers_data, **details_data}

    return data


def get_archived_data():
    response = S3_CLIENT.get_object(**S3_DEFAULT_PARAMS)
    
    lines = [
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

    params = {
        'ACL': 'public-read',
        'Body': pipe.value,
    }

    return S3_CLIENT.put_object(**S3_DEFAULT_PARAMS, **params)


def main():
    content = get_html()
    current_stats = parse_html(content)
    
    try:
        archived_data = get_archived_data()
    except S3_CLIENT.exceptions.NoSuchKey:
        current_stats['recorded_at'] = datetime.now()
        archive_data([current_stats])
    else:
        last_stats = archived_data[0]
        del last_stats['recorded_at']

        if current_stats != last_stats:
            current_stats['recorded_at'] = datetime.now()
            new_data = [current_stats] + archived_data
            archive_data(new_data)
            # notify


def lambda_handler(event, context):
    main()


if __name__ == '__main__':
    main()
