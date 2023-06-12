# recipes
http://127.0.0.1:5000/register  -- for register
http://127.0.0.1:5000/recipes/1  -- for a view id -- GET /POST/PUT/ DELETE
http://127.0.0.1:5000/recipes/1/favorite' for a favorite  - POST/DELETE
http://127.0.0.1:5000/recipes/1/comments' For a cooment -GET/POST


In Database replace 'your-secret-key' in app.config['JWT_SECRET_KEY'] with a secure secret key and update the database URI in app.config['SQLALCHEMY_DATABASE_URI'] with your PostgreSQL connection URI.


Install venv in the sys and run the below command:
