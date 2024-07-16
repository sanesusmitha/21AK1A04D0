from flask import Flask, request, jsonify
import requests
import time

app = Flask(__name__)

# Cache to store product data
cache = {}

# Register with test server to access e-commerce companies' APIs
test_server_url = 'https://test-server/register'
response = requests.post(test_server_url, json={'startup': 'your-startup-name'})
if response.status_code == 200:
    api_keys = response.json().get('api_keys', {})
else:
    print('Failed to register with test server')
    exit(1)

# Function to fetch product data from e-commerce companies' APIs
def fetch_products(category, company, api_key):
    url = f'https://{company}.com/api/products?category={category}'
    headers = {'Authorization': f'Bearer {api_key}'}
    response = requests.get(url, headers=headers)
    return response.json().get('products', [])

# Function to update cache with new product data
def update_cache(category, products):
    cache[category] = products

# Function to get top products from cache or fetch from APIs
def get_top_products(category, n, sort, order):
    if category in cache:
        products = cache[category]
    else:
        products = []
        for company, api_key in api_keys.items():
            products.extend(fetch_products(category, company, api_key))
        update_cache(category, products)
    # Sort and paginate products
    sorted_products = sorted(products, key=lambda x: x[sort], reverse=(order == 'desc'))
    return sorted_products[:n]

# API endpoint to retrieve top products
@app.route('/categories/<category>/products', methods=['GET'])
def get_products(category):
    n = int(request.args.get('n', 10))
    page = int(request.args.get('page', 1))
    sort = request.args.get('sort', 'rating')
    order = request.args.get('order', 'asc')
    products = get_top_products(category, n, sort, order)
    # Paginate products
    start = (page - 1) * n
    end = start + n
    paginated_products = products[start:end]
    # Generate unique product IDs
    product_ids = {}
    for product in paginated_products:
        product_ids[product['id']] = f'product-{product["id"]}'
    return jsonify({'products': paginated_products, 'product_ids': product_ids})

# API endpoint to retrieve product details
@app.route('/categories/<category>/products/<product_id>', methods=['GET'])
def get_product(category, product_id):
    product_id = product_id.replace('product-', '')
    products = cache.get(category, [])
    product = next((p for p in products if p['id'] == product_id), None)
    if product:
        return jsonify(product)
    else:
        return jsonify({'error': 'Product not found'}), 404

if __name__ == '__main__':
    app.run()

