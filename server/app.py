from flask import Flask, jsonify, request
from flask_migrate import Migrate
from models import db, Restaurant, Pizza, RestaurantPizza

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///app.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
migrate = Migrate(app, db)

@app.errorhandler(ValueError)
def handle_value_error(error):
    response=jsonify({"errors":[str(error)] })
    response.status_code =400
    return response

@app.route("/")
def home():
    return jsonify({"message": "Welcome to the Pizza API!"})

@app.route("/restaurants", methods=["GET"])
def get_restaurants():
    restaurants = Restaurant.query.all()
    return jsonify([restaurant.to_dict() for restaurant in restaurants]), 200

@app.route("/restaurants/<int:id>", methods=["GET"])
def get_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    restaurant_data = restaurant.to_dict()
    restaurant_data["restaurant_pizzas"] = [
        {
            "id": rp.id,
            "price": rp.price,
            "pizza_id": rp.pizza_id,
            "pizza": rp.pizza.to_dict(),
        }
        for rp in restaurant.restaurant_pizzas
    ]

    return jsonify(restaurant_data), 200

@app.route("/restaurants/<int:id>", methods=["DELETE"])
def delete_restaurant(id):
    restaurant = Restaurant.query.get(id)
    if not restaurant:
        return jsonify({"error": "Restaurant not found"}), 404

    restaurant_pizzas = RestaurantPizza.query.filter_by(restaurant_id=id).all()
    for rp in restaurant_pizzas:
        db.session.delete(rp)

    db.session.delete(restaurant)
    db.session.commit()
    return "", 204

@app.route("/pizzas", methods=["GET"])
def get_pizzas():
    pizzas = Pizza.query.all()
    return jsonify([pizza.to_dict() for pizza in pizzas]), 200

@app.route("/restaurant_pizzas", methods=["POST"])
def create_restaurant_pizza():
    data = request.get_json()
    price = data.get("price")
    restaurant_id = data.get("restaurant_id")
    pizza_id = data.get("pizza_id")

    restaurant = Restaurant.query.get(restaurant_id)
    pizza = Pizza.query.get(pizza_id)

    if not restaurant:
        return jsonify({"errors": ["Restaurant not found"]}), 400
    if not pizza:
        return jsonify({"errors": ["Pizza not found"]}), 400

    new_rp = RestaurantPizza(price=price, restaurant_id=restaurant_id, pizza_id=pizza_id)
    db.session.add(new_rp)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({"errors": [str(e)]}), 500

    return jsonify({
        "id": new_rp.id,
        "price": new_rp.price,
        "restaurant_id": new_rp.restaurant_id,
        "pizza_id": new_rp.pizza_id,
        "restaurant": restaurant.to_dict(),
        "pizza": pizza.to_dict(),
    }), 201

if __name__ == "__main__":
    app.run(port=5555, debug=True)
