from flask import Flask
from cert_info import check_domains

app = Flask(__name__)

@app.route('/')
def get_cert_status():
    domains = [
        "ikriv.com",
        "hodka.net",
        "hodka.ikriv.com",
        "dev.ikriv.com",
        "korov.net"]
    return check_domains(domains)

@app.route('/status')
def status():
    return {'status': 'operational', 'message': 'Service is running correctly'}

if __name__ == '__main__':
    # This is used when running locally only. When deployed to Apache,
    # the application runs using the WSGI configuration
    app.run(host='0.0.0.0', port=5000, debug=True)