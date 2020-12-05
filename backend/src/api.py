import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
'''
db_drop_and_create_all()

# ROUTES
'''
@TODO implement endpoint
    GET /drinks
        it should be a public endpoint
        it should contain only the drink.short() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks')
# @requires_auth('')
def get_drinks():

    if request.method != 'GET':
        abort(405)

    all_drinks_from_db = Drink.query.all()

    if len((all_drinks_from_db) == 0):
        abort(404)

    drinks = []

    for drink in all_drinks_from_db:
        drinks.append(drink.short())

    result = {}
    result['success'] = True
    result['drinks'] = drinks

    return jsonify(result)


'''
@TODO implement endpoint
    GET /drinks-detail
        it should require the 'get:drinks-detail' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure
'''


@app.route('/drinks-detail')
# @requires_auth('get:drinks-detail')
def get_detailed_drinks():

    if request.method != 'GET':
        abort(405)

    all_drinks_from_db = Drink.query.all()

    if len((all_drinks_from_db) == 0):
        abort(404)

    drinks = []

    for drink in all_drinks_from_db:
        drinks.append(drink.long())

    result = {}
    result['success'] = True
    result['drinks'] = drinks

    return jsonify(result)


'''
@TODO implement endpoint
    POST /drinks
        it should create a new row in the drinks table
        it should require the 'post:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure
'''


@app.route('drinks', methods=['POST'])
# @requires_auth('post:drinks')
def create_drink():

    if request.method != 'POST':
        abort(405)

    drink_data = request.get_json()

    if not drink_data:
        abort(400)

    new_recipe = []

    for ingredient in drink_data['recipe']:
        new_recipe.append(
            {'color': ingredient['color'], 'name': ingredient['name'], 'parts': ingredient['parts']})

    error = False

    try:
        new_drink = Drink(
            title=drink_data['title'],
            recipe=new_recipe
        )

        new_drink.insert()

    except:
        error = True
        # TODO: implement and activate
        # new_drink.cancel()
        print(sys.exc_info())

    finally:
        # TODO: implement and activate
        # new_drink.close()
        pass

    if error:
        abort(422)

    else:
        return jsonify({'success': True, 'drinks': [new_drink.long()]})


'''
@TODO implement endpoint
    PATCH /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should update the corresponding row for <id>
        it should require the 'patch:drinks' permission
        it should contain the drink.long() data representation
    returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure
'''


'''
@TODO implement endpoint
    DELETE /drinks/<id>
        where <id> is the existing model id
        it should respond with a 404 error if <id> is not found
        it should delete the corresponding row for <id>
        it should require the 'delete:drinks' permission
    returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure
'''


# Error Handling
# -----------------------------------------------------------------------------------------------------------

@app.errorhandler(400)
def bad_request(error):
    return jsonify({'success': False, 'error': 400, 'message': 'Bad request'}), 400


@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 404, 'message': 'Not found'}), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'success': False, 'error': 405, 'message': 'Method not allowed'}), 405


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({'success': False, 'error': 422, 'message': 'Not processable'}), 422


'''
@TODO implement error handler for AuthError
    error handler should conform to general task above 
'''

# -----------------------------------------------------------------------------------------------------------
