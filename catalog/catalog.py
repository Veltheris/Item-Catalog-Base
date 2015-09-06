#Basic Functionality
import os
import random, string
from functools import wraps
#Flask Imports
from flask import Flask, render_template, make_response, redirect, request, url_for, flash, jsonify
from flask import session as login_session
from werkzeug import secure_filename
from flask.ext.seasurf import SeaSurf
#SQLAlchemy Imports
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Category, Item, User
#Oauth imports for GConnect
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError, OAuth2Credentials
import httplib2
import json
import requests
"""
Server for a Item Catalog Application

Change URL and PORT in Server Settings below to modify IP of server.
Once you have a feel for the application, set DEBUG to False

All Routes
/
/catalog/
/catalog/login
/catalog/new/item 
/catalog/edit/item/<item>/ 
/catalog/delete/item/<item>/ 
/catalog/category/<category>/
/catalog/new/category 
/catalog/edit/category/<category>/ 
/catalog/delete/category/<category>/
/catalog/API/JSON/
/catalog/API/JSON/<category>
/catalog/API/JSON/item/<item>
/catalog/API/RSS/<category>
/catalog/API/RSS/
/gconnect 
/gdisconnect
"""
################
#Server Settings
################
URL = '0.0.0.0' #For server. 0.0.0.0 for all available
PORT = 5000 #Port of server
DEBUG = True #Debug Mode. Allows more in-depth errors from flask as well as the /catalog/testdata url
FullURL = "%s:%s" % (URL,PORT)
CLIENT_ID = json.loads(open('client_secrets.json','r').read())['web']['client_id']
UPLOAD_FOLDER = 'static/pictures/'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

#Configure Flask Application
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
#set up seasurf
csrf = SeaSurf(app)

# Setup for the SQLAlchemy Session
engine = create_engine('sqlite:///catalog.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

#create some basic data for testing
if DEBUG:
 @app.route('/catalog/testdata/')
 def catalogTestData():
    userOne = User(name='Test Data', email='Test@Data', id='1', picture='')
    session.add(userOne)
    session.commit()
    catOne = Category(name='Wargame', user_id='1') 
    session.add(catOne)
    catTwo = Category(name='Roleplaying', user_id='1')
    session.add(catTwo)
    catThree = Category(name='Strategy', user_id='1')
    session.add(catThree)
    catFour = Category(name='Other', user_id='1', public=False)
    session.add(catFour)
    session.commit()
    itemOne = Item(category_id='1',name='Warhammer: Age of Sigmar',description='New Hotness', user_id='1')
    session.add(itemOne)
    itemTwo = Item(category_id='1',name='Warhammer: 40,000',description='In the Grim Darkness...', user_id='1')
    session.add(itemTwo)
    itemThree = Item(category_id='2',name='Dungeons and Dragons Fifth Edition',description='The once and present King.', user_id='1')
    session.add(itemThree)
    itemFour = Item(category_id='3',name='Settlers of Catan',description='Have Sheep, need Wood!', user_id='1')
    session.add(itemFour)
    itemFive = Item(category_id='3',name='Warhammer: Forbidden Stars',description='Buff Ultramarines Pl0x', user_id='1')
    session.add(itemFive)
    itemSix = Item(category_id='4',name='Thing',description='Thing', user_id='1')
    session.add(itemSix)
    session.commit()
    flash('Test Data Added')
    session.delete(itemSix)
    session.commit()
    return redirect(url_for('.catalogListHome'))

#################
### Decorator ###
#################

#Require Logins for some pages
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'username' not in login_session:
            flash('You need to log in to do that')
            return redirect(url_for('catalogLogin', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

######################
### Authentication ###
######################

#Sesion Login
@app.route('/catalog/login')
def catalogLogin():
    next=request.args.get('next', '')
    state= ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    #return "The Current session state is %s" % (login_session['state'],)
    return render_template('signin.html', STATE=state, next=next)

#Google Connection Process
@csrf.exempt
@app.route('/gconnect', methods=['POST'])
def gconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid State'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    code = request.data
    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json',scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'),401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url,'GET')[1])
    #If there was an error.
    if result.get('error'):
        response = make_response(json.dumps(result.get('error')),500)
        response.headers['Content-Type'] = 'application/json'
        return response
    #Verify the token matches.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID does not match given user ID."),401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #Verify the token is valid.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID does not match the app's."),401)
        print "Token's client ID does not match the app's."
        response.headers['Content-Type'] = 'application/json'
        return response
    #check if the user is already logged in.
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('Current user is already connected.'),200)
        response.headers['Content-Type'] = 'application/json'
        return response
    #store the token
    login_session['credentials'] = credentials.to_json()
    print login_session['credentials']
    login_session['gplus_id'] = gplus_id
    #get the user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']

    
    userID = getUserId(login_session['email'])
    if not userID:
        userID = createUser(login_session)
    login_session['user_id'] = userID
    
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

#Disconnect from Google and Wipe the session
@app.route('/gdisconnect')
def gdisconnect():
    credentials = OAuth2Credentials.from_json(login_session.get('credentials'))
    print credentials
    if not credentials:
        response = make_response(json.dumps('Current user is not connected.'),401)
        response.headers['Content-Type'] = 'application/json'
        return response
    #Make a request to revoke the token
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % (access_token,)
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    
    if result['status'] == '200' or result['status'] == '400':
        #reset the session
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        if 'IToken' in login_session: del login_session['IToken']
        if 'CToken' in login_session: del login_session['CToken']
        response = make_response(json.dumps('Success'),200)
        response.headers['Content-Type'] = 'application/json'
        flash('Goodbye')
        return redirect(url_for('.catalogListHome'))
    else:
        #A failure occured
        response = make_response(json.dumps('Failure, Result was %s. Token was %s' % (result['status'],access_token)),400)
        response.headers['Content-Type'] = 'application/json'
        del login_session['credentials']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        if 'IToken' in login_session: del login_session['IToken']
        if 'CToken' in login_session: del login_session['CToken']
        return response

###################
### Main Routes ###
###################

#List the Homepage
@app.route('/')
@app.route('/catalog/')
def catalogListHome():
    #Latest 5 Items
    items = session.query(Item).join('category').order_by(desc(Item.changed)).limit(5)
    category = session.query(Category).all()
    itemcount = session.query(Item)
    return render_template('home.html', items = items, category = category, itemcount = itemcount)

#Create a New Category
@app.route('/catalog/new/category', methods=['GET','POST'])
@login_required
def catalogAddCategory():
    if request.method == 'GET':
        return render_template('newcategory.html')
    else:
        newName = request.form['name']
        setting = request.form.get('public')
        if setting == 'true':
            newSetting = True
        else:
            newSetting = False
        userID = login_session['user_id']
        category = Category(name=newName, user_id=userID, public=newSetting)
        session.add(category)
        session.commit()
        flash('Category %s Created' % (newName,))
        return redirect(url_for('.catalogListCategory', category=newName))

#Edit a Category
@app.route('/catalog/edit/category/<category>/', methods=['GET','POST'])
@login_required
def catalogEditCategory(category):
    category = session.query(Category).filter_by(name = category).first()
    if category.user_id != login_session['user_id']:
        flash("You do not own that Category")
        return redirect(url_for('.catalogListHome'))
    if request.method == 'GET':
        return render_template('editcategory.html', category=category)
    else:
        oldName = category.name
        newName = request.form['name']
        oldSetting = category.public
        if newName: category.name = newName
        setting = request.form.get('public')
        if setting == 'true':
            newSetting = True
        else:
            newSetting = False
        if newSetting != oldSetting:
            category.public = newSetting
        session.add(category)
        session.commit()
        if newName:
            flash('Category %s changed to %s' % (oldName, newName))
            return redirect(url_for('.catalogListCategory', category=newName))
        elif newSetting != oldSetting:
            flash('Category %s Public setting changed to %s' % (oldName, newSetting))
            return redirect(url_for('.catalogListCategory', category=oldName))
        else:
            return redirect(url_for('.catalogListCategory', category=oldName))

#Delete a Category
@app.route('/catalog/delete/category/<category>/', methods=['GET','POST'])
@login_required
def catalogDelCategory(category):
    category = session.query(Category).filter_by(name = category).first()
    if category.user_id != login_session['user_id']:
        flash("You do not own that Category")
        return redirect(url_for('.catalogListCategory', category = category))
    if request.method == 'GET':
        #Use the Login Session to store a token to reduce CSRF.
        token= ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['CToken'] = token
        return render_template('deletecategory.html', category=category, token=token)
    else:
        token = request.form['token']
        if not login_session['CToken'] or login_session['CToken'] != token:
            flash('Invalid Request!')
            return redirect(url_for('.catalogListHome'))
        del login_session['CToken']
        items = session.query(Item).filter_by(category_id = category.id).all()
        for item in items:
            if item.picture:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.picture))
            session.delete(item)
        session.commit()
        oldName = category.name
        session.delete(category)
        session.commit()
        flash('Category %s Removed' % (oldName,))
        return redirect(url_for('.catalogListHome'))

#List the Items in a Category
@app.route('/catalog/category/<category>/')
def catalogListCategory(category):
    category = session.query(Category).filter_by(name = category).first()
    if not category:
        flash("That category doesn't exist")
        return redirect(url_for('.catalogListHome'))
    items = session.query(Item).filter_by(category_id = category.id).all()
    creator = getUserInfo(category.user_id)
    sidebar = session.query(Category).all()
    itemcount = session.query(Item)
    return render_template('category.html', category=category, items=items, creator=creator, itemcount=itemcount, sidebar=sidebar)

#Create a new Item
@app.route('/catalog/new/item', methods=['GET','POST'])
@login_required
def catalogAddItem():
    if request.method == 'GET':
        default=request.args.get('category', '')
        category = session.query(Category).all()
        return render_template('newitem.html', category=category, default=default)
    else:
        picture = request.files['picture']
        newName = request.form['name']
        if not newName:
            flash("Name can't be empty")
            return redirect(url_for('.catalogAddItem'))
        newCategory = request.form['category']
        category = session.query(Category).get(newCategory)
        if not category.public and login_session['user_id'] != category.user_id:
            flash("You can't post there")
            return redirect(url_for('.catalogListHome'))
        newDescrip = request.form['description']
        userID = login_session['user_id']
        picName = None
        try:
            if picture:
                assert allowed_file(picture.filename)
                ext = picture.filename.rsplit('.', 1)[1]
                picName = (secure_filename(newName) + '.' + ext)
                picture.save(os.path.join(app.config['UPLOAD_FOLDER'], picName))
            else: picName = None
            item = Item(name=newName, user_id=userID, category_id = newCategory, description=newDescrip, picture=picName)
            session.add(item)
            session.commit()
            flash('Item %s Created' % (newName,))
            return redirect(url_for('.catalogListCategory', category=category.name))
        except:
            session.rollback()
            return redirect(url_for('.catalogAddItem'))

#Edit an Item
@app.route('/catalog/edit/item/<item>/', methods=['GET','POST'])
@login_required
def catalogEditItem(item):
    item = session.query(Item).get(item)
    if item.user_id != login_session['user_id']:
        flash("You do not own that Item")
        return redirect(url_for('.catalogListHome'))
    if request.method == 'GET':
        category = session.query(Category).all()
        return render_template('edititem.html', category=category, item=item)
    else:
        oldName = item.name
        newName = request.form['name']
        newCategory = request.form['category']
        newDescrip = request.form['description']
        oldPicture = item.picture
        picture = request.files['picture']
        if newName: item.name = newName
        if newCategory: item.category_id = newCategory
        if newDescrip: item.description = newDescrip
        if picture:
            assert allowed_file(picture.filename)
            ext = picture.filename.rsplit('.', 1)[1]
            picName = (secure_filename(newName) + '.' + ext)
            if oldPicture: os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.picture))
            picture.save(os.path.join(app.config['UPLOAD_FOLDER'], picName))
            item.picture=picName
        session.add(item)
        session.commit()
        if newName: flash('Menu Item %s Changed to %s' % (oldName, newName))
        else: flash('Menu Item %s Changed' % (oldName,))
        return redirect(url_for('.catalogListCategory', category=session.query(Category).get(newCategory).name))

#Delete an item.
@app.route('/catalog/delete/item/<item>/', methods=['GET','POST'])
@login_required
def catalogDelItem(item):
    item = session.query(Item).get(item)
    category = session.query(Category).get(item.category_id)
    if item.user_id != login_session['user_id'] and category.user_id != login_session['user_id']:
        flash("You do not own that Item")
        return redirect(url_for('.catalogListCategory', category=category.name))
    if request.method == 'GET':
        #Use the Login Session to store a token to reduce CSRF.
        token= ''.join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
        login_session['IToken'] = token
        return render_template('deleteitem.html', item=item, category=category, token=token)
    else:
        token = request.form['token']
        if not login_session['IToken'] or login_session['IToken'] != token:
            flash('Invalid Request!')
            return redirect(url_for('.catalogListHome'))
        del login_session['IToken']
        oldName = item.name
        if item.picture:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], item.picture))
        session.delete(item)
        session.commit()
        flash('Menu Item %s Removed' % (oldName,))
        return redirect(url_for('.catalogListCategory', category=category.name))

#####################
### API ENDPOINTS ###
#####################

#Return JSON for all Items
@app.route('/catalog/API/JSON/')
def catalogJSONAll():
    categories = session.query(Category).all()
    output = []
    for category in categories:
        items = session.query(Item).filter_by(category_id=category.id).all()
        itemoutput = []
        for item in items:
            itemoutput.append({"category_id":item.category_id,"name":item.name,
                           "description":item.description,"picture":item.picture,"user_id":item.user_id})
        output.append({"id":category.id, "name":category.name, "user_id":category.user_id,"items":itemoutput})
    return jsonify({'Categories':output})

#Return JSON for one category
@app.route('/catalog/API/JSON/<category>')
def catalogJSONCategory(category):
    category = session.query(Category).filter_by(name = category).first()
    items = session.query(Item).filter_by(category_id = category.id).all()
    output = []
    for item in items:
        output.append({"category_id":item.category_id,"name":item.name,"description":item.description,
                       "picture":item.picture,"user_id":item.user_id})
    return jsonify({'Items':output})

#Return JSON for one item
@app.route('/catalog/API/JSON/item/<item>')
def catalogJSONItem(item):
    item = session.query(Item).get(item)
    output.append({"category_id":item.category_id,"name":item.name,"description":item.description,
                   "picture":item.picture,"user_id":item.user_id})
    return jsonify({'Item':output})

#RSS Feed of all items
@app.route('/catalog/API/RSS/')
@app.route('/catalog/API/RSS/rss.xml')
def catalogRSSAll():
  items = session.query(Item).order_by(desc(Item.changed)).all()
  url = "192.168.1.180:5000"
  latest = items[0].changed.strftime('%d %B %Y %X')
  return render_template('rsscatalog.rss', items=items, url=url, latest=latest)

#RSS Feed of one category
@app.route('/catalog/API/RSS/<category>')
def catalogRSSCategory(category):
  category = session.query(Category).filter_by(name = category).first()
  items = session.query(Item).filter_by(category_id=category.id).order_by(desc(Item.changed)).all()
  url = FullURL
  latest = items[0].changed.strftime('%d %B %Y %X')
  return render_template('rsscategory.rss', category=category, items=items, url=url, latest=latest)

##########################
### User/Image Backend ###
##########################

#create a new user
def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

#get a user's information
def getUserInfo(user_id):
    user = session.query(User).get(user_id)
    return user

#Find a user's id.
def getUserId(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

#check a file
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS

### Start the Application ###

if __name__ == '__main__':
    app.secret_key = 'HEY_YOU_I_GOT_A_SECRET_TO_KEEP'
    app.debug = DEBUG
    app.run(host = URL, port = PORT)
