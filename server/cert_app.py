from quart import Quart, request, jsonify
from get_cert_expiration import get_cert_expiration_no_raise
from schema import CertExpirationResult

app = Quart(__name__)

@app.route('/')
async def get_cert_status():
    """
    Get SSL certificate expiration information for a domain.
    
    Query Parameters:
        domain (str): The domain name to check (e.g., 'google.com', 'example.com')
    
    Returns:
        JSON response containing CertExpirationResult data:
        {
            "domain": "example.com",
            "data": {
                "expiry_date": "2024-12-31T23:59:59+00:00",
                "time_remaining_str": "2 months, 15 days",
                "is_expired": false,
                "days_remaining": 75
            },
            "error": null
        }
        
        Or if there's an error:
        {
            "domain": "invalid-domain.com",
            "data": null,
            "error": "Error message describing what went wrong"
        }
    """
    domain = request.args.get('domain')
    
    if not domain:
        return jsonify({
            'error': 'Missing required query parameter: domain',
            'domain': None,
            'data': None
        }), 400
    
    # Clean up the domain parameter
    domain = domain.strip().lower()
    
    # Basic validation
    if not domain or '.' not in domain:
        return jsonify({
            'error': f'Invalid domain name: {domain}',
            'domain': domain,
            'data': None
        }), 400
    
    # Get certificate expiration data
    result = await get_cert_expiration_no_raise(domain)
    
    # Convert the result to a dictionary for JSON serialization
    result_dict = {
        'domain': result.domain,
        'data': None,
        'error': result.error
    }
    
    # Convert CertExpirationData to dict if present
    if result.data:
        result_dict['data'] = {
            'expiry_date': result.data.expiry_date.isoformat(),
            'time_remaining_str': result.data.time_remaining_str,
            'is_expired': result.data.is_expired,
            'days_remaining': result.data.days_remaining
        }
    
    return jsonify(result_dict)

@app.route('/status')
async def status():
    """Health check endpoint."""
    return jsonify({
        'status': 'operational', 
        'message': 'Service is running correctly'
    })

if __name__ == '__main__':
    # This is used when running locally only
    app.run(host='0.0.0.0', port=5000, debug=True)
