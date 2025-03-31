from flask import Flask, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, JWTManager, get_jwt_identity
import pyodbc
import bcrypt
from flasgger import Swagger, swag_from
from flask_cors import CORS


app = Flask(__name__)
# Enable CORS for all routes
CORS(app, resources={r"/api/*": {"origins": "http://localhost:5173"}})
app.config["JWT_SECRET_KEY"] = "super-secret-key"  # Change in production
jwt = JWTManager(app)

swagger_template = {
    "swagger": "2.0",
    "info": {
        "title": "Product API",
        "description": "API for managing products, authentication, and pricing optimization",
        "version": "0.0.1",
        "termsOfService": "https://your-terms.com"
    },
    "securityDefinitions": {
        "Bearer": {
            "type": "apiKey",
            "name": "Authorization",
            "in": "header",
            "description": "JWT Token format: 'Bearer YOUR_TOKEN'"
        }
    },
    "security": [{"Bearer": []}]
}

swagger = Swagger(app, template=swagger_template)

# Database Connection
DB_CONFIG = (
    r"DRIVER={SQL Server};"
    r"SERVER=TARUN007\TARUN;"  
    r"DATABASE=TARUN;"  
    r"Trusted_Connection=yes;"
)

def get_db_connection():
    try:
        conn = pyodbc.connect(DB_CONFIG)
        return conn
    except Exception as e:
        return None

# -------------------- User Authentication -------------------- #
@app.route('/api/signup', methods=['POST'])
@swag_from({
    "tags": ["Authentication"],
    "summary": "User Signup",
    "description": "Register a new user and get a JWT token.",
    "parameters": [{
        "name": "body",
        "in": "body",
        "required": True,
        "schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"},
                "role_id": {"type": "integer"}
            }
        }
    }],
    "responses": {
        "201": {"description": "User registered successfully"},
        "400": {"description": "Invalid role_id"},
        "500": {"description": "Server error"}
    }
})
def signup():
    data = request.json
    email = data.get("email")
    password = data.get("password")
    role_id = data.get("role_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM Role WHERE id = ?", (role_id,))
    if not cursor.fetchone():
        return jsonify({"error": "Invalid role_id"}), 400

    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    cursor.execute("INSERT INTO Users (email, password_hash, role_id) VALUES (?, ?, ?)", 
                   (email, hashed_pw, role_id))
    conn.commit()

    cursor.execute("SELECT id FROM Users WHERE email = ?", (email,))
    user_id = cursor.fetchone()[0]
    
    # ✅ Fix: Convert user_id to string
    token = create_access_token(identity=str(user_id))  

    return jsonify({"message": "User registered successfully!", "token": token}), 201

@app.route('/api/login', methods=['POST'])
@swag_from({
    "tags": ["Authentication"],
    "summary": "User Login",
    "description": "Login with email and password to get a JWT token.",
    "parameters": [{
        "name": "body",
        "in": "body",
        "required": True,
        "schema": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"}
            }
        }
    }],
    "responses": {
        "200": {"description": "Login successful"},
        "401": {"description": "Invalid credentials"}
    }
})
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash FROM Users WHERE email=?", (email,))
    row = cursor.fetchone()

    if row and bcrypt.checkpw(password.encode('utf-8'), row[1].encode('utf-8')):
        # ✅ Fix: Convert user_id to string
        token = create_access_token(identity=str(row[0]))  
        return jsonify({"message": "Login successful", "token": token}), 200
    else:
        return jsonify({"error": "Invalid credentials"}), 401

# -------------------- Product Management -------------------- #
@app.route('/api/products', methods=['POST'])
@jwt_required()
def create_product():
    """
    Add a new product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
              example: "Electric Scooter"
            description:
              type: string
              example: "Lightweight electric scooter"
            cost_price:
              type: number
              example: 150
            selling_price:
              type: number
              example: 299.99
            category_id:
              type: integer
              example: 3
            stock_available:
              type: integer
              example: 80
            units_sold:
              type: integer
              example: 40
            customer_rating:
              type: number
              example: 4
            demand_forecast:
              type: number
              example: 50
            optimized_price:
              type: number
              example: 285
    responses:
      201:
        description: Product created successfully
      400:
        description: Invalid input
      500:
        description: Database error
    """
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    # Validate category_id exists
    cursor.execute("SELECT id FROM Category WHERE id = ?", (data['category_id'],))
    category_exists = cursor.fetchone()
    if not category_exists:
        conn.close()
        return jsonify({"error": "Invalid category_id. Category does not exist."}), 400

    try:
        query = """
        INSERT INTO Product 
        (name, description, cost_price, selling_price, category_id, stock_available, units_sold, customer_rating, demand_forecast, optimized_price) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(query, (
            data['name'], data.get('description', ''), data['cost_price'], 
            data['selling_price'], data['category_id'], data['stock_available'], 
            data.get('units_sold', 0), data.get('customer_rating', 0), 
            data.get('demand_forecast', 0), data.get('optimized_price', 0)
        ))

        conn.commit()
        conn.close()
        return jsonify({"message": "Product created successfully"}), 201

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/products', methods=['GET'])
@jwt_required()
def get_products():
    """
    Get all products with category name
    ---
    tags:
      - Products
    security:
      - Bearer: []
    responses:
      200:
        description: A list of products with category names
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # ✅ Fetch category name instead of category_id
    query = """
    SELECT p.id, p.name, p.description, p.cost_price, p.selling_price, 
           c.name as category_name, p.stock_available, p.units_sold, 
           p.customer_rating, p.demand_forecast, p.optimized_price
    FROM Product p
    JOIN Category c ON p.category_id = c.id
    """
    cursor.execute(query)
    
    products = [
        {
            "id": row[0], "name": row[1], "description": row[2], "cost_price": row[3],
            "selling_price": row[4], "category_name": row[5], "stock_available": row[6],
            "units_sold": row[7], "customer_rating": row[8], "demand_forecast": row[9],
            "optimized_price": row[10]
        }
        for row in cursor.fetchall()
    ]
    
    conn.close()
    return jsonify(products), 200

# ✅ UPDATE product (Allows full updates)
@app.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    """
    Update an existing product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: product_id
        in: path
        required: true
        type: integer
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            name:
              type: string
            description:
              type: string
            cost_price:
              type: number
            selling_price:
              type: number
            category_id:
              type: integer
            stock_available:
              type: integer
            units_sold:
              type: integer
            customer_rating:
              type: number
            demand_forecast:
              type: number
            optimized_price:
              type: number
    responses:
      200:
        description: Product updated successfully
      404:
        description: Product not found
    """
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute("SELECT id FROM Product WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        return jsonify({"error": "Product not found"}), 404

    query = """
    UPDATE Product 
    SET name=?, description=?, cost_price=?, selling_price=?, category_id=?, 
        stock_available=?, units_sold=?, customer_rating=?, 
        demand_forecast=?, optimized_price=?
    WHERE id=?
    """
    cursor.execute(query, (
        data['name'], data.get('description', ''), data['cost_price'], data['selling_price'],
        data['category_id'], data['stock_available'], data.get('units_sold', 0),
        data.get('customer_rating', 0), data.get('demand_forecast', 0), 
        data.get('optimized_price', 0), product_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Product updated successfully"}), 200

# ✅ DELETE Product
@app.route('/api/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    """
    Delete a product
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: product_id
        in: path
        required: true
        type: integer
    responses:
      200:
        description: Product deleted successfully
      404:
        description: Product not found
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if product exists
    cursor.execute("SELECT id FROM Product WHERE id = ?", (product_id,))
    if not cursor.fetchone():
        return jsonify({"error": "Product not found"}), 404

    cursor.execute("DELETE FROM Product WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({"message": "Product deleted successfully"}), 200


@app.route('/api/products/search', methods=['GET'])
@jwt_required()
def search_product():
    """
    Search for a product by name
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: name
        in: query
        type: string
        required: true
        description: "Product name or partial match"
        example: "Scooter"
    responses:
      200:
        description: Products found
      400:
        description: Missing query parameter
      500:
        description: Database error
    """
    product_name = request.args.get('name')

    if not product_name:
        return jsonify({"error": "Missing 'name' query parameter"}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    try:
        query = """
        SELECT p.id, p.name, p.description, p.cost_price, p.selling_price, 
               c.name as category_name, p.stock_available, p.units_sold, 
               p.customer_rating, p.demand_forecast, p.optimized_price
        FROM Product p
        JOIN Category c ON p.category_id = c.id
        WHERE LOWER(p.name) LIKE ?
        """
        cursor.execute(query, (f"%{product_name.lower()}%",))
        products = cursor.fetchall()
        conn.close()

        if not products:
            return jsonify({"message": "No products found"}), 404

        result = []
        for row in products:
            result.append({
                "id": row[0],
                "name": row[1],
                "description": row[2],
                "cost_price": row[3],
                "selling_price": row[4],
                "category_name": row[5],
                "stock_available": row[6],
                "units_sold": row[7],
                "customer_rating": row[8],
                "demand_forecast": row[9],
                "optimized_price": row[10]
            })

        return jsonify(result), 200

    except Exception as e:
        conn.close()
        return jsonify({"error": str(e)}), 500

@app.route('/api/demand-forecast', methods=['GET'])
def get_demand_forecast():
    """
    Get Demand Forecast for Selected Products
    ---
    parameters:
      - name: product_ids
        in: query
        type: array
        items:
          type: integer
        required: true
        description: List of product IDs to fetch demand forecast
    responses:
      200:
        description: A list of product demand forecasts
        schema:
          type: array
          items:
            type: object
            properties:
              product_id:
                type: integer
                example: 101
              product_name:
                type: string
                example: "Laptop"
              category_name:
                type: string
                example: "Electronics"
              cost_price:
                type: string
                example: "$500"
              selling_price:
                type: string
                example: "$750"
              stock_available:
                type: string
                example: "100"
              units_sold:
                type: string
                example: "50"
              calculated_demand_forecast:
                type: number
                example: 375.0
    """
    product_ids_str = request.args.get('product_ids')
    if not product_ids_str:
        return jsonify({'error': 'product_ids parameter is required'}), 400

    try:
        product_ids = []
        for pid in product_ids_str.split(','):
            product_ids.append(int(pid.strip()))  # Remove extra spaces
    except ValueError:
        return jsonify({'error': 'Invalid product IDs provided'}), 400

    print('product_ids', product_ids)

    conn = get_db_connection()
    if not conn:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = conn.cursor()

    query = """
        SELECT p.id, p.name, c.name as category_name, p.cost_price, p.selling_price, 
               p.stock_available, p.units_sold, p.demand_forecast 
        FROM Product p 
        INNER JOIN Category c ON p.category_id = c.id
        WHERE p.id IN ({})
        """.format(",".join(["?"] * len(product_ids)))

    try:
        cursor.execute(query, product_ids)
        products = cursor.fetchall()
    except Exception as e:
        conn.close()
        return jsonify({"error": f"Database query error: {str(e)}"}), 500

    result = []
    for p_id, p_name, cat_name, c_price, s_price, stock, sold, d_forecast in products:
        calculated_forecast = (sold * s_price) / (stock + 1)
        result.append({
            "product_id": p_id,
            "product_name": p_name,
            "category_name": cat_name,
            "cost_price": f"${c_price}",
            "selling_price": f"${s_price}",
            "stock_available": f"{stock:,}",
            "units_sold": f"{sold:,}",
            "calculated_demand_forecast": round(calculated_forecast, 2)
        })

    conn.close()
    return jsonify(result)

@app.route('/api/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """
    Get all categories
    ---
    tags:
      - Categories
    security:
      - Bearer: []
    responses:
      200:
        description: A list of all product categories
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, name FROM Category")
    categories = [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

    conn.close()
    return jsonify(categories), 200

@app.route('/api/products/category', methods=['GET'])
@jwt_required()
def get_products_by_category():
    """
    Get all products or filter by category_id
    ---
    tags:
      - Products
    security:
      - Bearer: []
    parameters:
      - name: category_id
        in: query
        required: false
        type: integer
    responses:
      200:
        description: A list of products with optional filtering by category
    """
    category_id = request.args.get("category_id")

    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
    SELECT p.id, p.name, p.description, p.cost_price, p.selling_price, 
           c.name as category_name, p.stock_available, p.units_sold, 
           p.customer_rating, p.demand_forecast, p.optimized_price
    FROM Product p
    JOIN Category c ON p.category_id = c.id
    """
    
    params = []
    if category_id:
        query += " WHERE p.category_id = ?"
        params.append(category_id)

    cursor.execute(query, params)

    products = [
        {
            "id": row[0], "name": row[1], "description": row[2], "cost_price": row[3],
            "selling_price": row[4], "category_name": row[5], "stock_available": row[6],
            "units_sold": row[7], "customer_rating": row[8], "demand_forecast": row[9],
            "optimized_price": row[10]
        }
        for row in cursor.fetchall()
    ]

    conn.close()
    return jsonify(products), 200

# -------------------- Running Flask App -------------------- #
if __name__ == '__main__':
    app.run(debug=True)