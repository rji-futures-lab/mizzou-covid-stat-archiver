from function import S3_CLIENT, PROJECT_NAME
from re_parse import get_cached_keys


def delete_from_s3(key):
    params = {
        'Bucket': PROJECT_NAME,
        'Key': key,
    }
    return S3_CLIENT.delete_object(**params)


def main():
    
    latest_timestamped = get_cached_keys()[0]
    delete_from_s3('cache/latest.html')
    delete_from_s3(latest_timestamped)


if __name__ == '__main__':
    main()
