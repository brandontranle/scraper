KEY_WORDS = ['vr', 'android', 'security', 'privacy']

CLIENT_INFO = {
    'client_id': '', 
    'client_secret': '', 
    'username': "", 
    'password': "", 
    'user_agent': '',
}

MAX_POSTS = 110

MAX_RETRIES = 5

# ensure '/' is at the end
CSV_DIR = './output/csv/'
TXT_DIR = './output/txt/'

FILE_TYPE = 'csv'


# topics + .txt filenames
TOPICS_WITH_FILENAMES = [
    ('VR security OR privacy', f'vr_test.{FILE_TYPE}'),
    ('Android security OR privacy', f'andr_test.{FILE_TYPE}')
]
