from function import (
    parse_html, archive_data, get_cached_html,
    S3_CLIENT, PROJECT_NAME
)


def get_cached_keys():
    params = {
        'Bucket': PROJECT_NAME,
        'Prefix': 'cache/'
    }

    objects = S3_CLIENT.list_objects_v2(**params)['Contents']

    return sorted(
        [o['Key'] for o in objects if 'latest' not in o['Key']],
        reverse=True
    )


def main():
    data = []
    
    for key in get_cached_keys():
        html = get_cached_html(key)
        recorded_at = key \
            .lstrip('cache/') \
            .rstrip('.html')

        parsed = parse_html(html, recorded_at=recorded_at)
        data.append(parsed)

    archive_data(data)


if __name__ == '__main__':
    main()
