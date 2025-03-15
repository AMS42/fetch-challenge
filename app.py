import uuid
from flask import Flask, jsonify, request
from flask_restful import Resource, Api

rno = 0
receipts = {}
receipts_cache = {}

class ReceiptProcessor(Resource):
    def post(self):
        global receipts
        
        id = self.__process_receipt()
        receipts[id] = request.json
        return jsonify(
            {
                "id": id
            }
        )
    
    def __process_receipt(self): 
        global rno
        
        rno += 1
        return uuid.uuid5(uuid.NAMESPACE_URL, f"Receipt #{rno}")


class Calculator(Resource):
    def get(self, id):
        global receipts

        try: 
            id = uuid.UUID(id)
        except ValueError:
            return "", 404 

        if id not in receipts: return "", 404

        points = self.__calculate_points(id)
        return jsonify(
            {
                "points": points
            }
        )

    def __calculate_points(self, id: str) -> int:
        global receipts, receipts_cache

        if id in receipts_cache: return jsonify({"points": receipts_cache[id]})

        receipt = receipts[id]
        items = receipt["items"]
        points = len(list(filter(lambda c : c.isalnum(), receipt["retailer"])))
        
        if ".00" in receipt["total"]: points += 50
        if float(receipt["total"]) % .25 == 0: points += 25
        points += 5 * (len(items) // 2)

        for item in items:
            if len(item["shortDescription"].strip()) % 3 == 0:
                points += float.__ceil__(float(item["price"]) * .2)

        if int(receipt["purchaseDate"].rsplit("-", 1)[1]) % 2 == 1: 
            points += 6

        hh, _ = receipt["purchaseTime"].split(":")
        if int(hh) in [14, 15]: points += 10

        return points


def create_app() -> Flask:
    _app: Flask = Flask(__name__)
    _api: Api = Api(_app)

    _api.add_resource(Calculator, "/receipts/<string:id>/points")
    _api.add_resource(ReceiptProcessor, "/receipts/process")

    return _app


if __name__ == "__main__":
    create_app().run(debug=True, port=8080)
