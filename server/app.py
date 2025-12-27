import sys
import os

# Add cli directory to path to import shared modules
sys.path.insert(
    0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "cli")
)

from quart import Quart, request, jsonify, Response, send_from_directory
import asyncio
import json
from pathlib import Path
from expiration import get_cert_expiration_no_raise, get_cert_expiration_many
from schema import CertExpirationResult

app = Quart(__name__)

# Configure Quart to use compact JSON formatting
app.json.compact = True


@app.after_request
async def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Accept"
    return response


@app.route("/api/<path:path>", methods=["OPTIONS"])
@app.route("/api/", methods=["OPTIONS"])
@app.route("/api", methods=["OPTIONS"])
async def handle_options():
    return "", 200


# Path to static files (Next.js export)
if Path("/app/static").exists():
    STATIC_DIR = Path("/app/static")
else:
    STATIC_DIR = Path(__file__).parent.parent / "frontend" / "out"


def format_json(data):
    """Format JSON data compactly without pretty printing."""
    return json.dumps(data, separators=(",", ":"))


def _result_to_dict(result: CertExpirationResult) -> dict:
    """Convert CertExpirationResult to dictionary for JSON serialization."""
    result_dict: dict = {"domain": result.domain, "data": None, "error": result.error}

    if result.data:
        result_dict["data"] = {
            "expiry_date": result.data.expiry_date.isoformat(),
            "time_remaining_str": result.data.time_remaining_str,
            "is_expired": result.data.is_expired,
            "days_remaining": result.data.days_remaining,
        }

    return result_dict


def _validate_domain(domain: str) -> tuple[bool, str]:
    """Validate a domain name. Returns (is_valid, error_message)."""
    domain = domain.strip().lower()
    if not domain or "." not in domain:
        return False, f"Invalid domain name: {domain}"
    return True, ""


async def _stream_results(domains: list[str]):
    """Stream results as they come using get_cert_expiration_many."""
    async for result in get_cert_expiration_many(domains):
        result_dict = _result_to_dict(result)
        yield format_json(result_dict) + "\n"


async def _get_all_results(domains: list[str]) -> list[dict]:
    """Get all results and return as a list in the same order as input domains."""
    tasks = [get_cert_expiration_no_raise(domain) for domain in domains]
    results = await asyncio.gather(*tasks)
    return [_result_to_dict(result) for result in results]


@app.route("/api/")
async def get_cert_status():
    """Get SSL certificate expiration information for one or more domains."""
    domain = request.args.get("domain")
    domains_param = request.args.get("domains")

    if not domain and not domains_param:
        return (
            jsonify(
                {
                    "error": "Missing required query parameter: domain or domains",
                    "domain": None,
                    "data": None,
                }
            ),
            400,
        )

    domains = []
    if domain:
        domains.append(domain)
    if domains_param:
        domains.extend([d.strip() for d in domains_param.split(",") if d.strip()])

    # Remove duplicates while preserving order
    seen = set()
    unique_domains = []
    for d in domains:
        if d not in seen:
            seen.add(d)
            unique_domains.append(d)
    domains = unique_domains

    for domain in domains:
        is_valid, error_msg = _validate_domain(domain)
        if not is_valid:
            return jsonify({"error": error_msg, "domain": domain, "data": None}), 400

    accept_header = request.headers.get("Accept", "")
    streaming_mime_types = [
        "application/x-ndjson",
        "application/jsonl",
        "application/x-jsonlines",
    ]
    should_stream = any(
        mime_type in accept_header for mime_type in streaming_mime_types
    )

    if len(domains) == 1 or not should_stream:
        if len(domains) == 1 and domain and not domains_param:
            result = await get_cert_expiration_no_raise(domains[0])
            return jsonify(_result_to_dict(result))
        else:
            results = await _get_all_results(domains)
            return jsonify(results)
    else:

        async def generate():
            async for result_json in _stream_results(domains):
                yield result_json

        return Response(
            generate(),
            mimetype="application/x-ndjson",
            headers={"Transfer-Encoding": "chunked"},
        )


@app.route("/api/status")
async def status():
    """Health check endpoint."""
    return jsonify({"status": "operational", "message": "Service is running correctly"})


@app.route("/")
async def serve_index():
    """Serve the index.html file."""
    if (STATIC_DIR / "index.html").exists():
        return await send_from_directory(STATIC_DIR, "index.html")
    return jsonify({"error": "Frontend not built"}), 404


@app.route("/<path:path>")
async def serve_static(path):
    """Serve static files from Next.js export."""
    if path.startswith("api/"):
        return jsonify({"error": "Not found"}), 404

    file_path = STATIC_DIR / path
    if file_path.is_file() and file_path.exists():
        return await send_from_directory(STATIC_DIR, path)

    if (STATIC_DIR / "index.html").exists():
        return await send_from_directory(STATIC_DIR, "index.html")

    return jsonify({"error": "Not found"}), 404


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    app.run(host="0.0.0.0", port=port, debug=True)
