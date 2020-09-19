from function import (
    parse_html, archive_data, get_cached_html,
    S3_CLIENT, PROJECT_NAME
)


EXCLUDED = (
    'cache/latest.html',
    'cache/2020-09-17 15:36:09.587198.html',
)


def get_cached_keys():
    params = {
        'Bucket': PROJECT_NAME,
        'Prefix': 'cache/'
    }

    objects = S3_CLIENT.list_objects_v2(**params)['Contents']

    return sorted(
        [o['Key'] for o in objects if o['Key'] not in EXCLUDED],
        reverse=True
    )


def main():
    data = []

    unique_rows = set()
    
    for key in get_cached_keys():
        html = get_cached_html(key)
        recorded_at = key \
            .lstrip('cache/') \
            .rstrip('.html')

        parsed = parse_html(html, recorded_at=recorded_at)

        values = '|'.join([str(v) for k, v in parsed.items() if k != 'recorded_at'])

        if values not in unique_rows:
            unique_rows.add(values)
            data.append(parsed)

    archive_data(data)


if __name__ == '__main__':
    main()
