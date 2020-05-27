from flask import Flask, jsonify, request, redirect
from flask_jwt_extended import JWTManager, jwt_required, create_access_token
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'my_name'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///worker.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
jwt = JWTManager(app)


class User(db.Model):
    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(30), nullable=False)
    password = db.Column(db.String(30), nullable=False)

    def __init__(self, name, password):
        self.name = name
        self.password = password

    def __str__(self):
        return self.name


class Worker(db.Model):
    id_worker = db.Column(db.Integer, primary_key=True, nullable=False)
    name = db.Column(db.String(30), nullable=False)
    id_salary = db.Column(db.String, db.ForeignKey('salary.id_salary'), nullable=True)

    def __init__(self, name, id_salary):
        self.name = name
        self.id_salary = id_salary

    def __str__(self):
        return self.name


class Salary(db.Model):
    id_salary = db.Column(db.String(10), primary_key=True, nullable=False)
    main = db.Column(db.Integer, nullable=False)
    bonuses = db.Column(db.Integer, nullable=True)
    fine = db.Column(db.Integer, nullable=True)
    worker = db.relationship('Worker', backref='worker', lazy=True)

    def __init__(self, id_salary, main, bonuses, fine):
        self.id_salary = id_salary
        self.main = main
        self.bonuses = bonuses
        self.fine = fine

    def __str__(self):
        return self.id_salary


@app.route("/api/get_access", methods=["POST"])
def get_access():
    if not request.is_json:
        return jsonify({'msg': 'JSON not found'}), 400

    name = request.json['name']
    password = request.json['password']

    if not name and password:
        return jsonify({'msg': 'JSON Parameter is missing'}), 400

    found_user = User.query.filter_by(name=name).first()
    if not found_user:
        return jsonify({'msg': 'User not found'}), 400
    elif found_user.password != password:
        return jsonify({'msg': 'Password is wrong'}), 400
    else:
        return jsonify({'token': create_access_token(identity=name)}), 200


@app.errorhandler(404)
def not_found(e):
    return jsonify({'msg': 'Endpoint not found'}), 404


@app.errorhandler(405)
def not_allowed(e):
    return jsonify({'msg': 'Method not allowed for this endpoint'}), 405


@app.route("/api/<model>", methods=["GET", "POST"])
@jwt_required
def non_specific_method(model):
    data = []
    if request.method == "GET":
        if model == "worker":
            found = Worker.query.all()
            data = [
                {
                    'id_worker': x.id_worker,
                    'name': x.name,
                    'id_salary': x.id_salary
                }
                for x in found
            ]
        elif model == "salary":
            found = Salary.query.all()
            data = [
                {
                    'id_salary': x.id_salary,
                    'main': x.main,
                    'bonuses': x.bonuses,
                    'fine': x.fine
                }
                for x in found
            ]
        else:
            return jsonify({'msg': 'API Endpoint not found'}), 400
        return jsonify(data), 200
    else:
        if not request.is_json:
            return jsonify({'msg': "JSON not found"}), 400
        if model == "worker":
            name = request.json['name']
            id_salary = request.json['id_salary']
            if not name and id_salary:
                return jsonify({'msg': 'Some parameter is missing'}), 400

            worker = Worker(name, id_salary)
            db.session.add(worker)
            db.session.commit()
            data = {
                'id_worker': worker.id_worker,
                'name': worker.name,
                'id_salary': worker.id_salary
            }
            return jsonify(data), 200
        elif model == "salary":
            id_salary = request.json['id_salary']
            main = request.json['main']
            bonuses = request.json['bonuses']
            fine = request.json['fine']
            if not id_salary and main and bonuses and fine:
                return jsonify({'msg': 'Some parameter is missing'}), 400
            found = Salary.query.filter_by(id_salary=id_salary).first()

            if found:
                return jsonify({'msg': 'Current id salary already exist'})

            salary = Salary(id_salary, main, bonuses, fine)
            db.session.add(salary)
            db.session.commit()
            data = {
                'id_salary': id_salary,
                'main': main,
                'bonuses': bonuses,
                'fine': fine
            }
            return jsonify(data), 200
        else:
            return jsonify({'msg': 'API Endpoint not found'}), 404


@app.route("/api/<model>/<record_id>", methods=["PUT", "GET", "DELETE"])
@jwt_required
def specific_method(model, record_id):
    if request.method == "GET":
        if model == "worker":
            found = Worker.query.filter_by(id_worker=record_id).first()
            if not found:
                return jsonify({'msg': 'Record not found'}), 400
            data = {
                'id_worker': found.id_worker,
                'name': found.name,
                'id_salary': found.id_salary
            }
            return jsonify(data), 200
        elif model == "salary":
            found = Salary.query.filter_by(id_salary=record_id).first()
            if not found:
                return jsonify({'msg': 'Record not found'}), 400
            data = {
                'id_salary': found.id_salary,
                'main': found.main,
                'bonuses': found.bonuses,
                'fine': found.fine
            }
            return jsonify(data), 200
        else:
            return jsonify({'msg': 'Model not found'})
    elif request.method == "PUT":
        if model == "worker":
            if not request.is_json:
                return jsonify({'msg': 'Missing JSON in request'})
            name = request.json['name']
            id_salary = request.json['id_salary']

            if not name and id_salary:
                return jsonify({'msg': 'Some parameter is missing'})

            found = Worker.query.filter_by(id_worker=record_id).first()
            found.name = name
            found.id_salary = id_salary
            db.session.commit()

            data = {
                'id_worker': found.id_worker,
                'name': found.name,
                'id_salary': found.id_salary
            }

            return jsonify(data), 200
        elif model == "salary":
            if not request.is_json:
                return jsonify({'msg': 'Missing JSON in request'})
            id_salary = request.json['id_salary']
            main = request.json['main']
            bonuses = request.json['bonuses']
            fine = request.json['fine']

            if not id_salary and main and bonuses and fine:
                return jsonify({'msg': 'Some parameter is missing'})

            found = Worker.query.filter_by(id_salary=id_salary).first()
            found.main = main
            found.bonuses = bonuses
            found.fine = fine
            db.session.commit()

            data = {
                'id_salary': found.id_salary,
                'main': found.main,
                'bonuses': found.bonuses,
                'fine': found.fine
            }

            return jsonify(data), 200
        else:
            return jsonify({'msg': 'Model not found'}), 400
    elif request.method == "DELETE":
        if not request.is_json:
            return jsonify({'msg': 'Missing JSON'}), 400
        if model == "worker":
            found = Worker.query.filter_by(id_worker=record_id).first()
            if not found:
                return jsonify({'msg': 'Record not found'}), 400

            data = {
                'id_worker': found.id_worker,
                'name': found.name,
                'id_salary': found.id_salary
            }

            db.session.delete(found)
            db.session.commit()
            return jsonify(data), 200
        elif model == "salary":
            found = Salary.query.filter_by(id_salary=record_id).first()
            worker = Worker.query.filter_by(id_salary=record_id).first()
            if not found:
                return jsonify({'msg': 'Record not found'}), 400
            elif found and worker:
                return jsonify({'msg': 'Some worker still have this ID'}), 400
            data = {
                'id_salary': found.id_salary,
                'main': found.main,
                'bonuses': found.bonuses,
                'fine': found.fine
            }

            db.session.delete(found)
            db.session.commit()

            return jsonify(data), 200


if __name__ == "__main__":
    app.run(debug=True)
