import random, string, uuid
from datetime import datetime
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from openapi_spec_validator import validate as validate_spec
from openapi_spec_validator.readers import read_from_filename
from openapi_spec_validator.validation.exceptions import OpenAPIValidationError
from openapi_schema_validator import validate as validate_schema, OAS30Validator
from pathlib import Path
from jsonschema import ValidationError
from sys import stderr

"""
TODO:
[ ] make dynamic the receipt schema's reference to item schema (avoid circular references
[X] comment where necessary
[X] update os to Pathlib
"""

class DataInstance(object):
    """ 
    Data Instance (Singleton) for the api. 
    Holds all relevant data to run api for easy use to other modules.
    """
    _instance = None
    PROJECT_DIR = Path(__file__).parent

    receipts = {}
    receipt_points = {}

    try:
        _spec_dict, _ = read_from_filename(Path(PROJECT_DIR, "api.yml"))
        validate_spec(_spec_dict)
    except OSError:
        print(f"No such file: {Path(PROJECT_DIR, 'api.yml')}", flush=stderr)
        exit(1)
    except OpenAPIValidationError: 
        print("'api.yml' is malformed and could not be validated.", flush=stderr)
        exit(1)

    RECEIPT_SCHEMA = _spec_dict["components"]["schemas"]["Receipt"]
    RECEIPT_SCHEMA["components"] = {
        "schemas": { 
            "Item": _spec_dict["components"]["schemas"]["Item"] 
        }
    }
    
    def __new__(cls):
        if not cls._instance:
            cls._instance = super(DataInstance, cls).__new__(cls)
        return cls._instance


class ReceiptProcessor(Resource):
    def post(self):
        if not self.__valid_receipt(request.json):
            return "", 400
        
        id = self.__process_receipt()
        DataInstance.receipts[id] = request.json
        return jsonify(
            {
                "id": id
            }
        )
    
    def __process_receipt(self) -> uuid.UUID:
        _receipt_number = "".join(  # randomly generated alphanumeric string of length 8
            random.choices(string.ascii_uppercase + string.digits, k=8)
        )
        return uuid.uuid5(uuid.NAMESPACE_URL, f"Receipt #{_receipt_number}")
    
    def __valid_receipt(self, receipt) -> bool: 
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
        if id in DataInstance.receipt_points: 
            return jsonify({"points": DataInstance.receipt_points[id]})

        receipt = DataInstance.receipts[id]
        items = receipt["items"]
                    # 1 point for each alphanum in retailer name
        points = len(list(filter(lambda c : c.isalnum(), receipt["retailer"])))
        
        if ".00" in receipt["total"]: points += 50  # 50 pts if total is whole number
        if float(receipt["total"]) % .25 == 0: points += 25  # 25 pts if total is divisible by .25
        points += 5 * (len(items) // 2)  # 5 points for every two items

        for item in items:  # for each item, (price * .2) rounded up pts if length of trimmed short 
            if len(item["shortDescription"].strip()) % 3 == 0:  # description is divisible by 3
                points += float.__ceil__(float(item["price"]) * .2)
        
        purchase_day = datetime.strptime(receipt["purchaseDate"], "%Y-%m-%d").day
        # 6 pts if day of purchase is odd
        if purchase_day % 2 == 1: points += 6

        hh, _ = receipt["purchaseTime"].split(":")  # 10 pts if purchase happens in hours
        if 14 <= int(hh) <= 15: points += 10  # 14 or 15 (namely, between 2pm and 4pm)
        # I think it's worth noting that after 2:00pm is 2:00:01pm; and purchase times are not that granular

        DataInstance.receipt_points[id] = points  # cache the points for easy retrieval
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
