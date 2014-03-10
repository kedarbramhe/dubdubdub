dubdubdub
=========

Home of KLP. Houses *most* of the data and APIs.

### Development Setup

Get Vagrant box.

$vagrant init klp package.box
$vagrant up
$vagrant ssh

Install some additional dependencies:

$sudo apt-get install python2.7-dev

Setup environment:

$cd /vagrant/dubdubdub
$virtualenv .
$source bin/activate
$pip install -r requirements/local.txt

Setup database:

Follow instructions from http://codeinthehole.com/writing/how-to-install-postgis-and-geodjango-on-ubuntu/ to setup postgis template

Then:
$createuser vagrant
(make this user a superuser)

$createdb -T template_postgis -O vagrant dubdubdub

Lastly, copy local_settings.py.sample to local_settings.py in the dubdubdub/ folder.

Sync database:
python manage.py syncdb

Run Dev-Server:
python manage.py runserver 0.0.0.0:8000

