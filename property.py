from google.cloud import datastore
from flask import Blueprint, request, jsonify

import constants
import jwt

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

@bp.route('', methods=['GET'])
def get_property():

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    if request.method == 'GET':

        if 'Authorization' in request.headers:

            payload = jwt.verify_jwt(request)

            query = client.query(kind=constants.property)

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

            users_list = []

            for e in results:
                if e["user id"] == payload["sub"]:
                    e["user id"] = payload["sub"]
                    users_list.append(e)

            length_dic = {"total number": len(users_list)}
            output = {"property": users_list}

            if next_url:
                output["next"] = next_url

            return jsonify(length_dic, output), 200

        else:

            query = client.query(kind=constants.property)

            q_limit = int(request.args.get('limit', 5))
            q_offset = int(request.args.get('offset', 0))
            iterator = query.fetch(limit=q_limit, offset=q_offset)

            pages = iterator.pages
            results = list(next(pages))

            length_of_results = len(results)

            if iterator.next_page_token:
                next_offset = q_offset + q_limit
                next_url = request.base_url + "?limit=" + str(q_limit) + "&offset=" + str(next_offset)

            else:
                next_url = None

            for e in results:
                e["id"] = e.key.id
                e["self"] = request.url + "/" + str(e.key.id)
                e["total number"]: length_of_results

            length_dic = {"total number": length_of_results}
            output = {"property": results}

            if next_url:
                output["next"] = next_url

            return jsonify(length_dic, output), 200

    else:
        failure = {"Error": "Request type is not accepted"}
        return jsonify(failure), 405

@bp.route('', methods=['POST'])
def post_property():

    if 'Authorization' not in request.headers:
        return jsonify({"Error:" "Authorization header is needed"}), 401

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

            payload = jwt.verify_jwt(request)

            print(f'payload["sub"]: {payload["sub"]}')

            curr_property = datastore.entity.Entity(key=client.key(constants.property))
            curr_property.update({"street": results["street"],
                                  "city": results["city"],
                                  "state": results["state"],
                                  "country": results["country"],
                                  "available": results["available"],
                                  "start date": results["start date"],
                                  "end date": results["end date"],
                                  "renter": results["renter"],
                                  "user id": payload["sub"]})

            client.put(curr_property)
            data = curr_property
            data["user id"] = payload["sub"]
            data["id"] = str(curr_property.id)
            data["self"] = f'{constants.APP_URL}'+ "/property/" + str(curr_property.id)
            return jsonify(data), 201


    else:
        data = {"Error": "Request type is not accepted"}
        status_code = 405

    return jsonify(data), status_code

@bp.route('/<property_id>', methods=['GET'])
def get_property_id(property_id):

    if 'Authorization' not in request.headers:
        payload = jwt.verify_jwt(request)

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    if curr_property == None:
        data = {"Error": "No property with that property_id exists"}
        return jsonify(data), 404

    if request.method == 'GET':

        data = curr_property
        data["id"] = str(curr_property.id)
        data["self"] = f'{constants.APP_URL}' + "/property/" + str(curr_property.id)
        return jsonify(data), 201

    else:
        failure = {"Error": "Request type is not accepted"}
        return jsonify(failure), 405

@bp.route('/<property_id>', methods=['PATCH'])
def patch_property_id(property_id):

    if 'Authorization' not in request.headers:
        payload = jwt.verify_jwt(request)

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    if request.method == 'PATCH':

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

    else:
        failure = {"Error": "Request type is not accepted"}
        return jsonify(failure), 405

@bp.route('/<property_id>', methods=['PUT'])
def put_property_id(property_id):

    if 'Authorization' not in request.headers:
        payload = jwt.verify_jwt(request)

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    if request.method == "PUT":

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
                                  "renter": results["renter"],
                                  "available": results["available"],
                                  "start date": results["start date"],
                                  "end date": results["end date"]})

            client.put(curr_property)
            data = curr_property
            data["id"] = str(curr_property.id)
            data["self"] = f'{constants.APP_URL}' + "/property/" + str(curr_property.id)
            return jsonify(data), 201

@bp.route('/<property_id>', methods=['DELETE'])
def del_property_id(property_id):

    if 'Authorization' not in request.headers:
        payload = jwt.verify_jwt(request)

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    if request.method == "DELETE":

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

@bp.route('/<property_id>/renter/<renter_id>', methods=['PUT'])
def put_renter_to_property(property_id, renter_id):

    if 'Authorization' not in request.headers:
        payload = jwt.verify_jwt(request)

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

        # Tie the renter -> property
        print(len(curr_property["renter"]))
        if curr_renter["property"] == None and len(curr_property["renter"]) == 0:

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

        else:
            return jsonify({"Error": "Property already assigned or renter isn't associated with this property"}), 403

    else:
        return jsonify({"Error": "Request type is not accepted"}), 405

@bp.route('/<property_id>/renter/<renter_id>', methods=['DELETE'])
def del_renter_from_property(property_id, renter_id):

    if 'Authorization' not in request.headers:
        payload = jwt.verify_jwt(request)

    if 'application/json' not in request.accept_mimetypes or '*/*' not in request.accept_mimetypes:
        failure = {"Error": "request.accept_mimetimes is not accepted"}
        return jsonify(failure), 406

    property_key = client.key(constants.property, int(property_id))
    curr_property = client.get(key=property_key)

    renter_key = client.key(constants.renter, int(renter_id))
    curr_renter = client.get(key=renter_key)

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
        return jsonify({"Error": "Request type is not accepted"}), 405

