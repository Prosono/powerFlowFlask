from application import Flask, request, jsonify
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)

# Squarespace API credentials
SQUARESPACE_API_KEY = '456318f6-80b3-4dad-865e-ed9b73414d10'
SQUARESPACE_API_URL = 'https://api.squarespace.com/1.0/commerce/orders'


def get_orders():
    """Fetch orders from Squarespace API."""
    headers = {
        'Authorization': f'Bearer {SQUARESPACE_API_KEY}',
        'User-Agent': 'SMARTiApp/1.0',
        'Accept': 'application/json',
    }
    params = {}

    orders = []
    has_more = True
    page_num = 1
    while has_more:
        logging.info(f'Fetching orders page {page_num}')
        response = requests.get(SQUARESPACE_API_URL, headers=headers, params=params)
        if response.status_code == 200:
            data = response.json()
            orders.extend(data.get('result', []))
            has_more = data.get('pagination', {}).get('hasNextPage', False)
            next_cursor = data.get('pagination', {}).get('nextPageCursor')
            if has_more:
                params['cursor'] = next_cursor
            page_num += 1
        else:
            logging.error(f"Error fetching orders: {response.status_code} - {response.text}")
            return []

    return orders


@app.route('/verify-subscription', methods=['POST'])
def verify_subscription():
    """Verify if the customer has purchased the SMARTi PowerFlow™ subscription."""
    try:
        data = request.get_json()
        email = data.get('email')
        if not email:
            return jsonify({'status': 'error', 'message': 'Email is required'}), 400

        logging.info(f"Verifying subscription for email: {email}")
        orders = get_orders()
        if not orders:
            return jsonify({'status': 'error', 'message': 'No orders found'}), 404

        # Check if the email has purchased the SMARTi PowerFlow™ subscription
        for order in orders:
            if order.get('customerEmail') == email:
                for item in order.get('lineItems', []):
                    if item['productName'] == 'SMARTi PowerFlow™':
                        logging.info(f"Subscription found for email: {email}")
                        return jsonify({'status': 'success', 'message': 'Subscription verified.'}), 200

        logging.info(f"No subscription found for email: {email}")
        return jsonify({'status': 'error', 'message': 'Subscription not found.'}), 403

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({'status': 'error', 'message': 'Internal Server Error'}), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5001)
