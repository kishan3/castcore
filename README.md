# castcore
A backend for an online auditioning app. Django Rest Framework backend which provides REST APIs to front end clients.

## Prerequisites
- [Virtualenv](https://virtualenv.pypa.io/en/latest/)
- [Postgresql](http://www.postgresql.org/)
- [Redis](http://redis.io/)
- Install Postgresql database:
   - sudo apt-get install postgresql
   - sudo apt-get install python3-dev
   - sudo apt-get install python-psycopg2
   - sudo apt-get install libpq-dev
   - sudo apt-get install libjpeg-dev
   - sudo apt-get install libffi-dev

## Initialize the project
Create and activate a virtualenv:

```bash
virtualenv env
source env/bin/activate
```
Install dependencies:

```bash
pip install -r requirements/local.txt
```
Create the database:

```bash
createdb castjunction
```
Initialize the git repository

```
git init
git remote add origin git@github.com:morsefactory/ cast-core.git
```

Migrate the database and create a superuser:
```bash
python castjunction/manage.py migrate
python castjunction/manage.py createsuperuser
```

Run the development server: 
```bash
python castjunction/manage.py runserver
```

# Create Servers
By default the included fabfile will setup three environments:

- dev -- The bleeding edge of development
- qa -- For quality assurance testing
- prod -- For the live application

Create these servers on Heroku with:

```bash
fab init
```

# Automated Deployment
Deployment is handled via Travis. When builds pass Travis will automatically deploy that branch to Heroku. Enable this with:
```bash
travis encrypt $(heroku auth:token) --add deploy.api_key
```
