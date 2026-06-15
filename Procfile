web: python manage.py collectstatic --noinput && python manage.py migrate && gunicorn myproject.wsgi --bind 0.0.0.0:$PORT
