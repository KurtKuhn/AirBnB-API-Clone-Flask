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

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    if request.method == 'POST':
        results = request.get_json()

        if "street" not in results.keys() \
        or "city" not in results.keys() \
        or "state" not in results.keys() \
        or "country" not in results.keys() \
        or "available" not in results.keys() \
        or "start date" not in results.keys() \
        or "end date" not in results.keys():

            data = {"Error": "The request is missing or more attributes"}
            return jsonify(data), 400

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
            return jsonify(data), 201


    else:
        data = {"Error": "Method Not Allowed"}
        status_code = 405

    return jsonify(data), status_code

@bp.route('/<property_id>', methods=['GET', "PATCH", "PUT", "DELETE"])
def get_delete_property_id(property_id):

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    if curr_property == None:
        data = {"Error": "No property with that property_id exists"}
        return jsonify(data), 404

    elif request.method == 'GET':

        data = curr_property
        data["id"] = str(curr_property.id)
        data["self"] = f'{constants.APP_URL}' + "/property/" + str(curr_property.id)
        return jsonify(data), 201

    elif request.method == 'PATCH':

        results = request.get_json()

        if "street" in results.keys():
            curr_property["street"] = results["street"]

        if "city" in results.keys():
            curr_property["city"] = results["city"]

        if "state" in results.keys():
            curr_property["state"] = results["state"]

        if "country" in results.keys():
            curr_property["country"] = results["country"]

        if "available" in results.keys():

                curr_property["available"] = results["available"]

                if curr_property["available"] == True:
                    curr_property["start date"] = ""
                    curr_property["end date"] = ""

                if curr_property["available"] == False:
                    curr_property["start date"] = results["start date"]
                    curr_property["end date"] = results["end date"]

        if "start date" in results.keys():
            curr_property["start date"] = results["start date"]

        if "end date" in results.keys():
            curr_property["end date"] = results["end date"]

        client.put(curr_property)

        data = curr_property
        data["id"] = str(curr_property.id)
        data["self"] = f'{constants.APP_URL}' + "/property/" + str(curr_property.id)
        return jsonify(data), 201

    elif request.method == "PUT":

        results = request.get_json()

        if "street" not in results.keys() \
                or "city" not in results.keys() \
                or "state" not in results.keys() \
                or "country" not in results.keys() \
                or "available" not in results.keys() \
                or "start date" not in results.keys() \
                or "end date" not in results.keys():

            data = {"Error": "The request is missing or more attributes"}
            return jsonify(data), 400

        elif "street" in results.keys() \
                and "city" in results.keys() \
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
            data["self"] = f'{constants.APP_URL}' + "/property/" + str(curr_property.id)
            return jsonify(data), 201

    elif request.method == "DELETE":

        if curr_property["renter"] != None or curr_property["renter"] == []:

            if len(curr_property["renter"]) > 0:

                for renter in curr_property["renter"]:

                    curr_renter = client.get(key=client.key(constants.renter, renter["id"]))
                    curr_renter["property"] = None
                    client.put(curr_renter)

        client.delete(curr_property)
        return jsonify(""), 204

    else:
        failure = {"Error": "Request type is not accepted"}
        return jsonify(failure), 405

@bp.route('/<property_id>/renter/<renter_id>', methods=['PUT', 'DELETE'])
def put_del_renter_from_property(property_id, renter_id):

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    renter_key = client.key(constants.renter, int(renter_id))
    curr_renter = client.get(key=renter_key)

    if request.method == 'PUT':

        if curr_renter == None:
            failure = {"Error": "No renter with that renter_id exists"}
            return jsonify(failure), 404

        if curr_property == None:
            failure = {"Error": "No property with that property_id exists"}
            return jsonify(failure), 404

        results = request.get_json()

        print(results)

        # Tie the renter -> property
        if curr_renter["property"] == None:

            property_self_url = str(request.url_root) + "property/" + str(curr_property.key.id)
            curr_renter.update({"property": { "id": str(curr_property.key.id),
                                              "street": curr_property ["street"],
                                              "city": curr_property ["city"],
                                              "state": curr_property ["state"],
                                              "country": curr_property ["country"],
                                              "available": False,
                                              "start date": results["start date"],
                                              "end date": results["end date"],
                                              "self": property_self_url}})

            curr_property.update({ "id": str(curr_renter.key.id),
                                   "available": False,
                                  "start date": results["start date"],
                                  "end date": results["end date"]})

        else:
            failure = {"Error": "That specified renter assigned to another property"}
            return jsonify(failure), 403

        add_renter = {"id": curr_renter.key.id,
                      "self": str(request.url_root) + "renter/" + str(curr_renter.key.id)}

        # Update the property
        renter_list = []
        renter_list.append(add_renter)
        curr_property.update({"renter": renter_list,
                              "self": f'{constants.APP_URL}' + "/renter/" + str(curr_renter.id)})

        client.put(curr_property)
        client.put(curr_renter)

        data = curr_property
        return jsonify(data), 204

    if request.method == 'DELETE':

        if curr_renter == None:
            failure = {"Error": "No renter with that renter_id exists"}
            return jsonify(failure), 404

        if curr_property == None:
            failure = {"Error": "No property with that property_id exists"}
            return jsonify(failure), 404

        if curr_renter["property"] != None:

            if curr_renter["property"]["id"] == property_id:

                renter_list = curr_property["renter"]
                print(renter_list)
                print(curr_renter.key.id)

                renter_list = []
                # renter_list.remove({"id": curr_renter.key.id})

                curr_property.update({"renter": renter_list,
                                     "available": True,
                                     "start date": "",
                                     "end date": ""})

                curr_renter.update({"property": None})

            else:
                failure = {"Error": "That renter is not associated to this property"}
                status_code = 404
                return jsonify(failure), status_code

        else:
            failure = {"Error": "That renter is not associated to this property"}
            return jsonify(failure), 404

        client.put(curr_property)
        client.put(curr_renter)

        data = ""
        return jsonify(data), 204

    else:
        return jsonify({"Error": "Method isn't recognized"}), 405


        # if curr_property["renter"] == None:
        #     self_url = str(request.url_root) + "property/" + str(curr_property.key.id)
        #     curr_property.update({"renter": {"id": str(curr_property.key.id),
        #                                      "first name": curr_renter["first name"],
        #                                      "last name:": curr_renter["last name"],
        #                                      "phone number": curr_renter["phone number"],
        #                                      "self": self_url}})
        #
        # else:
        #     data = {"Error": "That specified load assigned to another boat"}
        #     status_code = 403

        curr_property.update()