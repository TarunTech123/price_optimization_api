# Price Optimization Tool API

This is the backend API for a Price Optimization Tool, built with Flask.

## Features

* **Product Management: And Price Optimization**
    * Create, read, update, and delete products.
    * Product attributes include:
        * Product ID
        * Name
        * Description
        * Cost Price
        * Selling Price
        * Category
        * Stock Available
        * Units Sold
        * Customer Rating
        * Demand Forecast
        * Optimized Price

## Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/TarunTech123/price_optimization_api.git
    cd price_optimization_api
    ```

2.  **Create a virtual environment (recommended):**

    ```bash
    python3 -m venv venv
    source venv/bin/activate   # On Linux/macOS
    venv\Scripts\activate    # On Windows
    ```

3.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

    (You'll need to create a `requirements.txt` file by running `pip freeze > requirements.txt`)

4.  **Run the application:**

    ```bash
    python app.py
    ```

    The API will be accessible at `http://127.0.0.1:5000/`.

## API Endpoints

* `GET /products`:  Get all products.
* `GET /products/<product_id>`:  Get a specific product.
* `POST /products`:  Create a new product.
* `PUT /products/<product_id>`:  Update a product.
* `DELETE /products/<product_id>`:  Delete a product. etc..

## Data Model

The `Product` model has the following attributes:

| Attribute       | Data Type | Description                     |
| :-------------- | :-------- | :------------------------------ |
| `product_id`    | Integer   | Unique identifier               |
| `name`          | String    | Product name                    |
| `description`   | String    | Product description             |
| `cost_price`    | Float     | Cost price                      |
| `selling_price` | Float     | Selling price                   |
| `category`      | String    | Product category                |
| `stock_available` | Integer   | Available stock                 |
| `units_sold`    | Integer   | Units sold                      |
| `customer_rating` | Float     | Customer rating                 |
| `demand_forecast` | Integer   | Demand forecast                 |
| `optimized_price` | Float     | Optimized price                 |

## Example Usage

Created SWagger Documentation

## Database

SQL Server
