from google.cloud import datastore
import json
from flask import Blueprint, request, jsonify
import constants

client = datastore.Client()
bp = Blueprint('renter', __name__, url_prefix='/renter')

@bp.route('', methods=['GET', 'POST'])
def access_property():

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    if request.method == 'POST':

        results = request.get_json()

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
                                  "phone number": results["phone number"],
                                  "property": None})

            client.put(curr_renter)
            data = curr_renter
            data["id"] = str(curr_renter.id)
            data["self"] = f'{constants.APP_URL}'+ "/renter/" + str(curr_renter.id)
            status_code = 201

        return jsonify(data), status_code


    else:
        data = {"Error": "Method Not Allowed"}
        status_code = 405
    return jsonify(data), status_code


@bp.route('/<renter_id>', methods=['GET', "PATCH", "PUT", "DELETE"])
def get_delete_property_id(renter_id):

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    renter_key = client.key(constants.renter, int(renter_id))
    curr_renter = client.get(key=renter_key)

    if curr_renter == None:
        data = {"Error": "No renter with that renter_id exists"}
        return jsonify(data), 404

    elif request.method == 'GET':

        data = curr_renter
        data["id"] = str(curr_renter.id)
        data["self"] = f'{constants.APP_URL}' + "/renter/" + str(curr_renter.id)
        return jsonify(data), 201

    elif request.method == 'PATCH':

        results = request.get_json()

        if "first name" in results.keys():
            curr_renter["first name"] = results["first name"]

        if "last name" in results.keys():
            curr_renter["last name"] = results["last name"]

        if "phone number" in results.keys():
            curr_renter["phone number"] = results["phone number"]


        client.put(curr_renter)

        data = curr_renter
        data["id"] = str(curr_renter.id)
        data["self"] = f'{constants.APP_URL}' + "/renter/" + str(curr_renter.id)
        return jsonify(data), 201


    elif request.method == "PUT":

        results = request.get_json()

        if "first name" not in results.keys() \
                or "last name" not in results.keys() \
                or "phone number" not in results.keys():

            print("Are you in here?")

            data = {"Error": "The request is missing or more attributes"}
            status_code = 400

        elif "first name" in results.keys() \
                and "last name" in results.keys() \
                and "phone number" in results.keys():

            curr_renter = datastore.entity.Entity(key=client.key(constants.renter))
            curr_renter.update({"first name": results["first name"],
                                "last name": results["last name"],
                                "phone number": results["phone number"],
                                "property": None})

            client.put(curr_renter)
            data = curr_renter
            data["id"] = str(curr_renter.id)
            data["self"] = f'{constants.APP_URL}' + "/renter/" + str(curr_renter.id)
            status_code = 201

        return jsonify(data), status_code

    if request.method == 'DELETE':

        if curr_renter["property"] != None:

            curr_property = client.get(key=client.key(constants.property, int(curr_renter["property"]["id"])))

            for renter in curr_property["renter"]:

                if renter["id"] == curr_renter.key.id:
                    curr_property["renter"] = []

            client.put(curr_property)

        client.delete(renter_key)
        return jsonify(""), 204


    else:

        data = {"Error": "Invalid request type"}
        return json(data), 405





