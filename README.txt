SynBioWorld

Here is a short tutorial on how to setup a fork of SynBioWorld and contribute to SynBioWorld developement.


- Install Python 2.5 (2.5 and no other version, as appengine runs only on python 2.5)

- Install the latest version of the google appengine SDK (http://code.google.com/appengine/downloads.html)

- Create a github account and install git and setup your ssh keys (instructions on github) 
Now fork synbioworld (http://help.github.com/fork-a-repo/) 

	git clone git@github.com:username/SynBioWorld.git


Now run:
manage.py syncdb

There are a few more things you need to install to be able run SynBioWorld properly.


- Install Sass (http://sass-lang.com/download.html) (you might need to install Ruby first http://rubyinstaller.org/downloads/)

- Then we need to prepopulate the database. Go to your SynBioWorld directory and run:

manage.py loaddata cms.json

This should install 3 objects from 1 fixture. Those are the menu, blog and sidebar elements 

manage.py loaddata country.json

This should install 238 objects from 1 fixture. Those are the coutries.

- Create a Site object with the correct SITE_ID. (this is required for the registration system). To do so, follow the instructions bellow

manage.py shell

from django.contrib.sites.models import Site

synbio=Site(pk=34, name=”SynBioWorld”, domain="www.synbioworld.org")
synbio.save()


Finally create a superuser account:

manage.py createsuperuser

(follow the instructions)


You are now all set! Run:

manage.py runserver


And go to localhost:8000 in your browser !!!!


The site should be running, but there is no paper yet in the database. To add papers go to the url:
librarian/add

Then past records from ISI (win-tab delimited full records with citations). 
You need to remove the last carriage return. Import. 

The import can take a while to process. Be patient!


Now you can play with the code.

