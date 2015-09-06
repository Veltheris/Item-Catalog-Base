#Item Catalog Application
This is a python-powered Flask Application to display an Item Catalog. Users can log in using Google+. Once logged in they can create, modify, and delete categories and items. Categories can be made private, preventing other users from creating items in them. Category creators can also delete any items in the category.

Table of Contents
- Requirements
  - Vagrant
  - Manual
- Installation/Setup
- Extra Credit
- Changelog
- Comments


##Requirements
This application can be used in two ways. Set up the Vagrant machine, which includes all other required programs, or natively, using the programs listed. See the notes for how to download the programs.

Note for manual - If you have PIP for Python, you can use it to quickly download/install the python modules.
you can find it at https://pypi.python.org/pypi/pip/

###Both:
-Google+ Account [Required for Login] - This website uses Oauth2 Authentication through Google+ for secure logins.
-Google Developers [Optional] - To control the website logins and allow logins from other computers, Google Developers is required.
  -see https://console.developers.google.com and at the --Extras-- under installation below.

###Vagrant:
- VirtualBox [Required]: Provides functions needed by Vagrant.
  - https://www.virtualbox.org/wiki/Downloads for download
- Vagrant [Required]: Virtual Machine System
  - see https://www.vagrantup.com/downloads.html for download
###Manual:
- Python [Required]: Designed for 2.7, though it may work on others.
  - see https://www.python.org/downloads/ for download.
- psycopg2 [Required]: A Python Module to connect with PostgreSQL.
  - see http://initd.org/psycopg/docs/install.html#installation for installation instructions.
- PostgreSQL [Required]: A SQL Implementation.
  - see http://www.postgresql.org/download/ for download
- Flask [Required]: Version 0.10.1 Python Module that provides the webserver
  - see http://flask.pocoo.org/ for download 
- SQLAlchemy [Required]: Version 0.8.4 - Python module to map Databases (SQL in this case) to Objects
  - see http://www.sqlalchemy.org/download.html for download
- Oauth2Client [Required]: Version 1.4.12 Python module to support the login with Google
  - https://github.com/google/oauth2client/
- Flask-SeaSurf [Required]: Version 0.2.0 Python module to reduce CSRF 


##Installation/Setup
Place this folder somewhere where you wish to run it from. Then Follow the instructions below.
If you have the manual requirements fulfilled, you can skip ahead to --From Manual--

###With Vagrant
In the command line/Terminal, navigate to Catalog/vagrant and run `vagrant up`
Once that completes, run `vagrant ssh` to connect to the machine.
inside the vm, run `cd /vagrant/catalog`, and continue the instructions below.
###From Manual
once inside catalog, use `python application.py` to run the Flask Application. the website can be found by opening a web browser and going to `http://localhost:5000/`.
Users on the website can now log in using google+ to create categories and items. Users can create items their own private categories, as well as those marked as public Categories.
Users can edit and delete their own items and categories, as well as deleting items in categories they own.
For an example of how the website can work, go to `http://localhost:5000/catalog/testdata` to create some test data.
The Webserver can be stopped with Ctrl+C on the Vagrant. (Command+C for Mac)
While it stopped, the database can be wiped by deleting `catalog.db` from `Vagrant/catalog`. Make sure to also delete the contents of `Vagrant/catalog/static/pictures/`.
###Extras
To Disable the testdata function, as well as the extra information given on database errors, open up `Vagrant/catalog/application.py`, Navigate to `Server Settings` and change DEBUG to False (no quotes).
To Change the url that can be used to visit the website, open up `Vagrant/catalog/application.py`, Navigate to `Server Settings` and change URL and PORT to the desired values.
With the included files, Google+ will only accept log in attempts from `http://localhost:5000/` or `http://192.168.1.180:5000/`.
To Change these, you will need a Google Developers account.
Go to `https://console.developers.google.com` and create a project.
Than go to APIs & auth and select `Create new Client ID`.
Select `Web Application` as the type, and add in the urls you would like to use under `Javascript origins`. Leave redirects blank.
Once finished, create the ID. On the client ID select `Download JSON`. save the file as `client_secrets.json` and place it in `Vagrant/catalog/`, replacing the one already there.
You can now run the webserver again, and the logins will be done through your new project.


##Extra Credit
This application has been modified to have support for images, increased protection against Cross-Site Request Forgeries (CSRF), and pages for Rich Site Summary (RSS).
 -Requests for the Deletion now check for a randomly generated Token present in the POST request. This token is checked 
  against the one provided for the user upon with the Deletion's GET request, and saved to the users' login_session.
 -RSS Feeds can be Acessed, both site-wide with /catalog/API/RSS/ and category specific with /catalog/API/RSS/<category>.
  They list the items in the catalog, and include timestamps taken from the database and formatted for RSS/XML.


##Changelog
###Version 1.0
- First Submitted Version.
###Version 1.1
- Second Version.
  - Fixed an issue with Flask 0.10
  - Simplified the login requirements accross the functions.
  - Maded the routes more clear to reduce problems.
  - Added some cascades to the database setup.
  - Fixed an issue where a item could be entered without a name.

###Comments
Flask is Awesome! :D
I have been working on side projects using it, and it's a lot better than just using Apache and HTML pages.
While implementing the images, I found conflicting opinions about whether or not to store the images using the database you are using. The general consensus seemed to be no, unless consistency is really important.
