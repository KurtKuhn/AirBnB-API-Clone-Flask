from google.cloud import datastore
import json
from flask import Blueprint, request, jsonify
import constants

client = datastore.Client()
bp = Blueprint('renter', __name__, url_prefix='/renter')

@bp.route('', methods=['GET', 'POST'])
def access_property():

    if request.method == 'POST':

        results = request.get_json()

        print(results)

        if "first name" not in results.keys() \
        or "last name" not in results.keys() \
        or "phone number" not in results.keys():

            print("Are you in here?")

            data = {"Error": "The request is missing or more attributes"}
            status_code = 400

        elif "first name" in results.keys() \
        and "last name"  in results.keys() \
        and "phone number" in results.keys():

            curr_renter = datastore.entity.Entity(key=client.key(constants.renter))
            curr_renter.update({"first name": results["first name"],
                                  "last name": results["last name"],
                                  "phone number": results["phone number"]})

            client.put(curr_renter)
            data = curr_renter
            data["id"] = str(curr_renter.id)
            data["self"] = f'{constants.APP_URL}'+ "/renter/" + str(curr_renter.id)
            status_code = 201


        return jsonify(data), status_code


    else:
        data = {"Error": "Method Not Allowed"}
        status_code = 405

    print("leaving")
    return jsonify(data), status_code


@bp.route('/<renter_id>', methods=['GET'])
def get_delete_property_id(renter_id):

    print(renter_id)

    renter_key = client.key(constants.renter, int(renter_id))
    curr_renter = client.get(key=renter_key)

    if curr_renter == None:
        data = {"Error": "No renter with that renter_id exists"}
        status_code = 404

    elif request.method == 'GET':

        data = curr_renter
        data["id"] = str(curr_renter.id)
        data["self"] = f'{constants.APP_URL}' + "/renter/" + str(curr_renter.id)
        status_code = 201

    elif request.method != 'GET' or request.method != 'DELETE':

        data = {"Error": "Invalid request type"}
        status_code = 405

    return jsonify(data), status_code

