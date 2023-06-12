from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, jwt_required, create_access_token, get_jwt_identity
from flask_cors import CORS

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://username:password@localhost/recipes_db'  # Replace with your PostgreSQL connection URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = 'your-secret-key'  # Replace with a secure secret key
db = SQLAlchemy(app)
jwt = JWTManager(app)
CORS(app)

# User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    recipes = db.relationship('Recipe', backref='author', lazy=True)
    favorite_recipes = db.relationship('FavoriteRecipe', backref='user', lazy=True)
    comments = db.relationship('Comment', backref='user', lazy=True)

# Recipe model
class Recipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    ingredients = db.Column(db.Text, nullable=False)
    instructions = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    comments = db.relationship('Comment', backref='recipe', lazy=True)
    favorites = db.relationship('FavoriteRecipe', backref='recipe', lazy=True)

# Favorite Recipe model
class FavoriteRecipe(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

# Comment model
class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipe.id'), nullable=False)

# Register route
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data['username']
    password = data['password']
    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        return jsonify({'message': 'Username already exists'}), 409
    user = User(username=username, password=password)
    db.session.add(user)
    db.session.commit()
    return jsonify({'message': 'User registered successfully'}), 201

# Login route
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        access_token = create_access_token(identity=user.id)
        return jsonify({'access_token': access_token}), 200
    return jsonify({'message': 'Invalid username or password'}), 401

# Recipe routes
@app.route('/recipes', methods=['GET'])
def get_recipes():
    recipes = Recipe.query.all()
    recipe_list = []
    for recipe in recipes:
        recipe_list.append({
            'id': recipe.id,
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions,
            'author': recipe.author.username
        })
    return jsonify(recipe_list), 200

@app.route('/recipes/<int:recipe_id>', methods=['GET'])
def get_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        return jsonify({
            'id': recipe.id,
            'title': recipe.title,
            'ingredients': recipe.ingredients,
            'instructions': recipe.instructions,
            'author': recipe.author.username
        }), 200
    return jsonify({'message': 'Recipe not found'}), 404

@app.route('/recipes', methods=['POST'])
@jwt_required()
def create_recipe():
    data = request.get_json()
    title = data['title']
    ingredients = data['ingredients']
    instructions = data['instructions']
    user_id = get_jwt_identity()
    recipe = Recipe(title=title, ingredients=ingredients, instructions=instructions, user_id=user_id)
    db.session.add(recipe)
    db.session.commit()
    return jsonify({'message': 'Recipe created successfully'}), 201

@app.route('/recipes/<int:recipe_id>', methods=['PUT'])
@jwt_required()
def edit_recipe(recipe_id):
    data = request.get_json()
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        user_id = get_jwt_identity()
        if recipe.user_id == user_id:
            recipe.title = data['title']
            recipe.ingredients = data['ingredients']
            recipe.instructions = data['instructions']
            db.session.commit()
            return jsonify({'message': 'Recipe updated successfully'}), 200
        return jsonify({'message': 'Unauthorized to edit this recipe'}), 403
    return jsonify({'message': 'Recipe not found'}), 404

@app.route('/recipes/<int:recipe_id>', methods=['DELETE'])
@jwt_required()
def delete_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        user_id = get_jwt_identity()
        if recipe.user_id == user_id:
            db.session.delete(recipe)
            db.session.commit()
            return jsonify({'message': 'Recipe deleted successfully'}), 200
        return jsonify({'message': 'Unauthorized to delete this recipe'}), 403
    return jsonify({'message': 'Recipe not found'}), 404

# Favorite routes
@app.route('/recipes/<int:recipe_id>/favorite', methods=['POST'])
@jwt_required()
def favorite_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        user_id = get_jwt_identity()
        favorite = FavoriteRecipe.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if not favorite:
            favorite = FavoriteRecipe(user_id=user_id, recipe_id=recipe_id)
            db.session.add(favorite)
            db.session.commit()
            return jsonify({'message': 'Recipe added to favorites'}), 201
        return jsonify({'message': 'Recipe already in favorites'}), 409
    return jsonify({'message': 'Recipe not found'}), 404

@app.route('/recipes/<int:recipe_id>/favorite', methods=['DELETE'])
@jwt_required()
def unfavorite_recipe(recipe_id):
    recipe = Recipe.query.get(recipe_id)
    if recipe:
        user_id = get_jwt_identity()
        favorite = FavoriteRecipe.query.filter_by(user_id=user_id, recipe_id=recipe_id).first()
        if favorite:
            db.session.delete(favorite)
            db.session.commit()
            return jsonify({'message': 'Recipe removed from favorites'}), 200
        return jsonify({'message': 'Recipe is not in favorites'}), 404
    return jsonify({'message': 'Recipe not found'}), 404

# Comment routes
@app.route('/recipes/<int:recipe_id>/comments', methods=['GET'])
def get_comments(recipe_id):
    comments = Comment.query.filter_by(recipe_id=recipe_id).all()
    comment_list = []
    for comment in comments:
        comment_list.append({
            'id': comment.id,
            'text': comment.text,
            'user': comment.user.username
        })
    return jsonify(comment_list), 200

@app.route('/recipes/<int:recipe_id>/comments', methods=['POST'])
@jwt_required()
def add_comment(recipe_id):
    data = request.get_json()
    text = data['text']
    user_id = get_jwt_identity()
    comment = Comment(text=text, user_id=user_id, recipe_id=recipe_id)
    db.session.add(comment)
    db.session.commit()
    return jsonify({'message': 'Comment added successfully'}), 201

# Run the app
if __name__ == '__main__':
    db.create_all()
    app.run()
