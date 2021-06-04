from google.cloud import datastore

from flask import Blueprint, request, jsonify

import constants
import jwt
client = datastore.Client()
bp = Blueprint('renter', __name__, url_prefix='/renter')

@bp.route('', methods=['GET'])
def get_property():

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    if request.method == 'GET':

        if 'Authorization' in request.headers:

            payload = jwt.verify_jwt(request)

            query = client.query(kind=constants.renter)

            q_limit = int(request.args.get('limit', 5))
            q_offset = int(request.args.get('offset', 0))
            iterator = query.fetch(limit=q_limit, offset=q_offset)

            pages = iterator.pages
            results = list(next(pages))

            if iterator.next_page_token:
                next_offset = q_offset + q_limit
                next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)

            else:
                next_url = None

            renters_list = []

            for e in results:
                if e["user id"] == payload["sub"]:
                    e["user id"] = payload["sub"]
                    renters_list.append(e)

            length_dic = {"total number": len(renters_list)}
            output = {"renters": renters_list}

            if next_url:
                output["next"] = next_url

            return jsonify(length_dic, output), 200


        else:

            query = client.query(kind=constants.renter)
            q_limit = int(request.args.get('limit', 5))
            q_offset = int(request.args.get('offset', 0))
            iterator = query.fetch(limit=q_limit, offset=q_offset)

            pages = iterator.pages
            results = list(next(pages))

            if iterator.next_page_token:
                next_offset = q_offset + q_limit
                next_url = request.base_url + "?limit=" + "&offset=" + str(next_offset)

            else:
                next_url = None

            for e in results:
                e["id"] = e.key.id
                e["self"] = request.url + "/" + str(e.key.id)

            length_dic = {"total number": len(results)}

            output = {"renter": results}
            if next_url:
                output["next"] = next_url

            return jsonify(length_dic, output), 200

    else:
        return jsonify({"Error": "Request type is not accepted"}), 405

@bp.route('', methods=['POST'])
def post_property():

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

            payload = jwt.verify_jwt(request)

            print(f'payload["sub"]: {payload["sub"]}')

            curr_renter = datastore.entity.Entity(key=client.key(constants.renter))
            curr_renter.update({"first name": results["first name"],
                                  "last name": results["last name"],
                                  "phone number": results["phone number"],
                                  "property": None,
                                  "user id": payload["sub"]})

            client.put(curr_renter)
            data = curr_renter
            data["user id"]: payload["sub"]
            data["id"] = str(curr_renter.id)
            data["self"] = f'{constants.APP_URL}'+ "/renter/" + str(curr_renter.id)
            status_code = 201

        return jsonify(data), status_code

    else:
        return jsonify({"Error": "Request type is not accepted"}), 405

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
                    curr_property["available"] = True
                    curr_property["start date"] = ""
                    curr_property["end date"] = ""

            # client.update({"available": True})
            client.put(curr_property)

        client.delete(renter_key)
        return jsonify(""), 204


    else:

        data = {"Error": "Invalid request type"}
        return json(data), 405





