import os
from flask import Flask, request, jsonify, abort
from sqlalchemy import exc
import json
from flask_cors import CORS

from .database.models import db_drop_and_create_all, setup_db, Drink
from .auth.auth import AuthError, requires_auth

import sys

app = Flask(__name__)
setup_db(app)
CORS(app)

'''
@TODO: uncomment the following line to initialize the database
!! NOTE THIS WILL DROP ALL RECORDS AND START YOUR DB FROM SCRATCH
!! NOTE THIS MUST BE UNCOMMENTED ON FIRST RUN
!! NOTE Once the db is built and has data, this can be commented again.
'''
# db_drop_and_create_all()

# ROUTES

# -----------------------------------------------------------------------------------------------------------

# Does not need @requires_auth decoartor as it is a public endpoint
@app.route('/drinks')
def get_drinks():
    ''' GET /drinks
        A public endpoint that only contains the drink.short() data representation.
        Returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure. '''

    if request.method != 'GET':
        abort(405)

    all_drinks_from_db = Drink.query.all()

    if len(all_drinks_from_db) == 0:
        abort(404)

    drinks = []

    for drink in all_drinks_from_db:
        drinks.append(drink.short())

    result = {}
    result['success'] = True
    result['drinks'] = drinks

    return jsonify(result)

# -----------------------------------------------------------------------------------------------------------


@app.route('/drinks-detail')
@requires_auth(permission='get:drinks-detail')
def get_detailed_drinks(payload):
    ''' GET /drinks-detail
        Requires the 'get:drinks-detail' permission and contains the drink.long() data representation.
        payload argument comes from the requires_auth decorator as a returned argument from a previous decorator call.
        Returns status code 200 and json {"success": True, "drinks": drinks} where drinks is the list of drinks
        or appropriate status code indicating reason for failure. '''

    if request.method != 'GET':
        abort(405)

    all_drinks_from_db = Drink.query.all()

    if len(all_drinks_from_db) == 0:
        abort(404)

    drinks = []

    for drink in all_drinks_from_db:
        drinks.append(drink.long())

    result = {}
    result['success'] = True
    result['drinks'] = drinks

    return jsonify(result)

# -----------------------------------------------------------------------------------------------------------


@app.route('/drinks', methods=['POST'])
@requires_auth(permission='post:drinks')
def create_drink(payload):
    ''' POST /drinks
        Creates a new row in the drinks table and requires the 'post:drinks' permission.
        payload argument comes from the requires_auth decorator as a returned argument from a previous decorator call.
        It contains the drink.long() data representation.
        Returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the newly created drink
        or appropriate status code indicating reason for failure. '''

    if request.method != 'POST':
        abort(405)

    drink_data = request.get_json()

    if not drink_data:
        abort(400)

    error = False

    try:
        new_drink = Drink(
            title=drink_data['title'],
            recipe=json.dumps(drink_data['recipe'])
        )

        new_drink.insert()

    except:
        error = True
        new_drink.cancel()
        new_drink.close()
        print(sys.exc_info())

    if error:
        abort(422)

    else:
        return jsonify({'success': True, 'drinks': [new_drink.long()]})

# -----------------------------------------------------------------------------------------------------------


@app.route('/drinks/<int:id>', methods=['PATCH'])
@requires_auth(permission='patch:drinks')
def update_drink(payload, id):
    ''' PATCH /drinks/<id>
        payload argument comes from the requires_auth decorator as a returned argument from a previous decorator call.
        <id> is the existing model id (int).
        Responds with a 404 error if <id> is not found.
        Updates the corresponding row for <id>.
        Requires the 'patch:drinks' permission.
        Contains the drink.long() data representation.
        returns status code 200 and json {"success": True, "drinks": drink} where drink an array containing only the updated drink
        or appropriate status code indicating reason for failure. '''

    if request.method != 'PATCH':
        abort(405)

    drink_from_db = Drink.query.get(id)

    if not drink_from_db:
        abort(404)

    drink_data = request.get_json()

    error = False

    try:
        if 'title' in drink_data:
            drink_from_db.title = drink_data['title']

        if 'recipe' in drink_data:
            drink_from_db.recipe = json.dumps(drink_data['recipe'])

        drink_from_db.update()

    except:
        error = True
        drink_from_db.cancel()
        drink_from_db.close()
        print(sys.exc_info())

    if error:
        abort(422)

    else:
        return jsonify({'success': True, 'drinks': [drink_from_db.long()]})

# -----------------------------------------------------------------------------------------------------------


@app.route('/drinks/<int:id>', methods=['DELETE'])
@requires_auth(permission='delete:drinks')
def delete_drink(payload, id):
    ''' DELETE /drinks/<id>
        payload argument comes from the requires_auth decorator as a returned argument from a previous decorator call.
        <id> is the existing model id (int).
        Responds with a 404 error if <id> is not found.
        Deletes the corresponding row for <id>.
        Requires the 'delete:drinks' permission.
        Returns status code 200 and json {"success": True, "delete": id} where id is the id of the deleted record
        or appropriate status code indicating reason for failure. '''

    if request.method != 'DELETE':
        abort(405)

    error = False

    drink_to_delete = Drink.query.get(id)

    if drink_to_delete is not None:

        try:
            drink_to_delete.delete()

        except:
            error = True
            drink_to_delete.cancel()
            drink_to_delete.close()
            print(sys.exc_info())

        if error:
            abort(422)
        else:
            return jsonify({'success': True, 'delete': id})

    else:
        abort(404)


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


@app.errorhandler(AuthError)
def auth_error(error):
    return jsonify({'success': False, 'error': error.status_code, 'message': error.error['description']}), error.status_code

# -----------------------------------------------------------------------------------------------------------
