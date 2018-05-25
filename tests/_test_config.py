from sqlalchemy.engine.url import make_url


DB_CONN = os.environ['TEST_DATABASE_URL']
DB_OPTS = make_url(DB_CONN).translate_connect_args()
