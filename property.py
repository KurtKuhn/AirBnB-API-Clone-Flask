from google.cloud import datastore
import json
from flask import Blueprint, request, jsonify
import constants
import datetime
import re

client = datastore.Client()
bp = Blueprint('property', __name__, url_prefix='/property')

@bp.route("/delete_all", methods=['GET'])
def delete_all():

    properties = list(client.query(kind=constants.property).fetch())
    for property in properties:

        client.delete(property)
        to_be_returned = ""
        status_code = 202

    return jsonify(to_be_returned), status_code

@bp.route('', methods=['GET', 'POST'])
def access_property():

    if request.method == 'POST':


        results = request.get_json()

        print(results)

        if "street" not in results.keys() \
        or "city" not in results.keys() \
        or "state" not in results.keys() \
        or "country" not in results.keys() \
        or "available" not in results.keys() \
        or "start date" not in results.keys() \
        or "end date" not in results.keys():

            print("Are you in here?")

            data = {"Error": "The request is missing or more attributes"}
            status_code = 400

        elif "street" in results.keys() \
        and "city"  in results.keys() \
        and "state" in results.keys() \
        and "country" in results.keys() \
        and "available" in results.keys() \
        and "start date" in results.keys() \
        and "end date" in results.keys():

            curr_property = datastore.entity.Entity(key=client.key(constants.property))
            curr_property.update({"street": results["street"],
                                  "city": results["city"],
                                  "state": results["state"],
                                  "country": results["country"],
                                  "available": results["available"],
                                  "start date": results["start date"],
                                  "end date": results["end date"]})

            client.put(curr_property)
            data = curr_property
            data["id"] = str(curr_property.id)
            data["self"] = f'{constants.APP_URL}'+ "/property/" + str(curr_property.id)
            status_code = 201


        return jsonify(data), status_code


    else:
        data = {"Error": "Method Not Allowed"}
        status_code = 405

    print("leaving")
    return jsonify(data), status_code

@bp.route('/<property_id>', methods=['GET'])
def get_delete_property_id(property_id):

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    if curr_property == None:
        data = {"Error": "No property with that property_id exists"}
        status_code = 404

    elif request.method == 'GET':

        data = curr_property
        data["id"] = str(curr_property.id)
        data["self"] = f'{constants.APP_URL}' + "/property/" + str(curr_property.id)
        status_code = 201

    return jsonify(data), status_code


