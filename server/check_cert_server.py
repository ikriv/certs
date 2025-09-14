from quart import Quart, request, jsonify, Response
import asyncio
import json
from get_cert_expiration import get_cert_expiration_no_raise, get_cert_expiration_many
from schema import CertExpirationResult

app = Quart(__name__)

# Configure Quart to use compact JSON formatting
app.json.compact = True

def format_json(data):
    """Format JSON data compactly without pretty printing."""
    return json.dumps(data, separators=(',', ':'))

def _result_to_dict(result: CertExpirationResult) -> dict:
    """Convert CertExpirationResult to dictionary for JSON serialization."""
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
    
    return result_dict

def _validate_domain(domain: str) -> tuple[bool, str]:
    """Validate a domain name. Returns (is_valid, error_message)."""
    domain = domain.strip().lower()
    if not domain or '.' not in domain:
        return False, f'Invalid domain name: {domain}'
    return True, ""

async def _stream_results(domains: list[str]):
    """Stream results as they come using get_cert_expiration_many."""
    async for result in get_cert_expiration_many(domains):
        result_dict = _result_to_dict(result)
        yield format_json(result_dict) + '\n'

async def _get_all_results(domains: list[str]) -> list[dict]:
    """Get all results and return as a list in the same order as input domains."""
    # Create tasks for all domains
    tasks = [get_cert_expiration_no_raise(domain) for domain in domains]
    
    # Wait for all results
    results = await asyncio.gather(*tasks)
    
    # Convert to dictionaries
    return [_result_to_dict(result) for result in results]

@app.route('/')
async def get_cert_status():
    """
    Get SSL certificate expiration information for one or more domains.
    
    Query Parameters:
        domain (str): Single domain name to check (e.g., 'google.com')
        domains (str): Comma-separated list of domains (e.g., 'google.com,github.com,example.com')
    
    HTTP Headers:
        Accept: If set to 'application/x-ndjson', 'application/jsonl', or 'application/x-jsonlines',
                and multiple domains are specified, results are streamed as newline-delimited JSON.
                Otherwise, results are returned as a JSON array.
    
    Returns:
        For single domain or non-streaming multiple domains:
        JSON response containing CertExpirationResult data or array of results.
        
        For streaming multiple domains:
        Newline-delimited JSON stream with chunked encoding.
    """
    domain = request.args.get('domain')
    domains_param = request.args.get('domains')
    
    # Check if we have any domain parameters
    if not domain and not domains_param:
        return jsonify({
            'error': 'Missing required query parameter: domain or domains',
            'domain': None,
            'data': None
        }), 400
    
    # Parse domains
    domains = []
    if domain:
        domains.append(domain)
    if domains_param:
        domains.extend([d.strip() for d in domains_param.split(',') if d.strip()])
    
    # Remove duplicates while preserving order
    seen = set()
    unique_domains = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            unique_domains.append(d)
    domains = unique_domains
    
    # Validate all domains
    for domain in domains:
        is_valid, error_msg = _validate_domain(domain)
        if not is_valid:
            return jsonify({
                'error': error_msg,
                'domain': domain,
                'data': None
            }), 400
    
    # Check Accept header for streaming
    accept_header = request.headers.get('Accept', '')
    streaming_mime_types = [
        'application/x-ndjson',
        'application/jsonl', 
        'application/x-jsonlines'
    ]
    should_stream = any(mime_type in accept_header for mime_type in streaming_mime_types)
    
    # Handle single domain or non-streaming multiple domains
    if len(domains) == 1 or not should_stream:
        if len(domains) == 1 and domain and not domains_param:
            # Single domain via ?domain= parameter - return single result
            result = await get_cert_expiration_no_raise(domains[0])
            return jsonify(_result_to_dict(result))
        else:
            # Multiple domains or single domain via ?domains= parameter - return array
            results = await _get_all_results(domains)
            return jsonify(results)
    
    # Handle streaming multiple domains
    else:
        async def generate():
            async for result_json in _stream_results(domains):
                yield result_json
        
        return Response(
            generate(),
            mimetype='application/x-ndjson',
            headers={'Transfer-Encoding': 'chunked'}
        )

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
