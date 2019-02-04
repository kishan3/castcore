web: newrelic-admin run-program gunicorn --pythonpath="$PWD/castjunction" wsgi:application
worker: python castjunction/manage.py rqworker default