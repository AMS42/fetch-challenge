import os, random, string, uuid, yaml
from datetime import datetime
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from openapi_spec_validator import validate as validate_spec
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
from openapi_schema_validator import validate as validate_schema, OAS30Validator
from jsonschema import ValidationError
from sys import stderr

class DataInstance(object):
    """ 
    Data Instance (Singleton) for the api. 
    Holds all relevant data to run api for easy use to other modules.
    """
    _instance = None
    PROJECT_DIR = __file__.rsplit(os.sep, 1)[0]
    _spec_dict, _base_uri = read_from_filename(os.path.join(PROJECT_DIR, "api.yml"))

    receipts = {}
    receipts_cache = {}

    try:
        validate_spec(_spec_dict)
    except OpenAPIValidationError: 
        print("'api.yml' is malformed and could not be validated.", flush=stderr)
        exit(1)

    RECEIPT_SCHEMA = _spec_dict["components"]["schemas"]["Receipt"]
    RECEIPT_SCHEMA["components"] = {}
    RECEIPT_SCHEMA["components"]["schemas"] = {}
    RECEIPT_SCHEMA["components"]["schemas"] = { 
        "Item": _spec_dict["components"]["schemas"]["Item"] 
    }
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DataInstance, cls).__new__(cls)
        return cls._instance
    

def valid_receipt(receipt) -> bool: 
    try:
        validate_schema(
            receipt, 
            DataInstance.RECEIPT_SCHEMA,
            cls=OAS30Validator,
        )
        return True
    except ValidationError as e:
        print(e, flush=stderr)
    return False


class ReceiptProcessor(Resource):
    def post(self):
        if not valid_receipt(request.json):
            return "", 400
        
        id = self.__process_receipt()
        DataInstance.receipts[id] = request.json
        return jsonify(
            {
                "id": id
            }
        )
    
    def __process_receipt(self): 
        _receipt_number = "".join(  # randomly generated alphanumeric string of length 8
                random.choice(string.ascii_uppercase + string.digits) for _ in range(8)
            )
        return uuid.uuid5(uuid.NAMESPACE_URL, f"Receipt #{_receipt_number}")


class PointsCalculator(Resource):
    def get(self, id):
        try: 
            id = uuid.UUID(id)
        except ValueError:  # id is a malformed UUID; therefore, it is not found
            return "", 404 

        if id not in DataInstance.receipts: return "", 404

        points = self.__calculate_points(id)
        return jsonify(
            {
                "points": points
            }
        )

    def __calculate_points(self, id: str) -> int:
        if id in DataInstance.receipts_cache: 
            return jsonify({"points": DataInstance.receipts_cache[id]})

        receipt = DataInstance.receipts[id]
        items = receipt["items"]
                    # 1 point for each alphanum in retailer name
        points = len(list(filter(lambda c : c.isalnum(), receipt["retailer"])))
        
        if ".00" in receipt["total"]: points += 50 
        if float(receipt["total"]) % .25 == 0: points += 25
        points += 5 * (len(items) // 2)

        for item in items:
            if len(item["shortDescription"].strip()) % 3 == 0:
                points += float.__ceil__(float(item["price"]) * .2)
        
        purchase_day = datetime.strptime(receipt["purchaseDate"], "%Y-%m-%d").day
        if purchase_day % 2 == 1: points += 6

        hh, _ = receipt["purchaseTime"].split(":")
        if 14 <= int(hh) <= 15: points += 10

        return points


def create_app() -> Flask:
    """ 
    Return created Flask app (factory). 
    Sets api Resource objects to respective paths.
    """
    _app: Flask = Flask(__name__)
    _api: Api = Api(_app)

    _api.add_resource(PointsCalculator, "/receipts/<string:id>/points")
    _api.add_resource(ReceiptProcessor, "/receipts/process")

    return _app


if __name__ == "__main__":
    create_app().run(debug=True, port=8080)
