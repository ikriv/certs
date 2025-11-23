'use client';

import { useState, useEffect } from 'react';

// Default domains to check (can be moved to config or env)
const DEFAULT_DOMAINS = [
  'google.com',
  'github.com',
  'example.com'
];

function getLocalDateStr(isoDateStr) {
  const options = {
    timeZoneName: 'short',
  };
  const date = new Date(isoDateStr);
  return date.toLocaleString(undefined, options);
}

export default function CertificateChecker() {
  const [certData, setCertData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [domainsInput, setDomainsInput] = useState(DEFAULT_DOMAINS.join(', '));

  const fetchCertificates = async (domains) => {
    setLoading(true);
    setError(null);

    // Build query string
    const domainsList = domains.split(',').map(d => d.trim()).filter(d => d);
    if (domainsList.length === 0) {
      setError('Please enter at least one domain');
      setLoading(false);
      return;
    }

    const queryParam = domainsList.length === 1 
      ? `domain=${encodeURIComponent(domainsList[0])}`
      : `domains=${encodeURIComponent(domainsList.join(','))}`;

    const apiUrl = `/api/?${queryParam}`;

    try {
      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const data = await response.json();
      
      // Handle both single result and array of results
      const results = Array.isArray(data) ? data : [data];
      
      // Transform API response to match component expectations
      const transformedData = results.map(result => ({
        domain: result.domain,
        expiry_date: result.data?.expiry_date || null,
        time_remaining: result.data?.time_remaining_str || null,
        error: result.error || null,
        is_expired: result.data?.is_expired || false,
        days_remaining: result.data?.days_remaining || null,
      }));

      setCertData(transformedData);
    } catch (err) {
      if (err.message.includes('Failed to fetch')) {
        setError(`Unable to access ${apiUrl}: ${err.message}. Make sure the backend server is running on port 5000.`);
      } else {
        setError(`Failed to fetch certificate data: ${err.message}`);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => {
    fetchCertificates(domainsInput);
  };

  useEffect(() => {
    // Auto-fetch on mount with default domains
    fetchCertificates(domainsInput);
  }, []);

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="items-center mb-6">
        <h1 className="text-2xl font-bold text-gray-800">SSL Certificate Checker</h1>
      </div>

      <div className="mb-4">
        <label htmlFor="domains" className="block text-sm font-medium text-gray-700 mb-2">
          Domains (comma-separated):
        </label>
        <div className="flex gap-2">
          <input
            id="domains"
            type="text"
            value={domainsInput}
            onChange={(e) => setDomainsInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !loading) {
                handleRefresh();
              }
            }}
            className="flex-1 px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            placeholder="google.com, github.com, example.com"
            disabled={loading}
          />
          <button
            className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
            onClick={handleRefresh}
            disabled={loading}
          >
            {loading ? 'Checking...' : 'Check'}
          </button>
        </div>
      </div>

      {error && (
        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
          {error}
        </div>
      )}

      {loading && certData.length === 0 ? (
        <div className="text-center py-10">
          <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-solid border-blue-500 border-r-transparent"></div>
          <p className="mt-2 text-gray-600">Loading certificate data...</p>
        </div>
      ) : certData.length > 0 ? (
        <div className="overflow-x-auto p-6">
          <table className="min-w-full bg-white border border-gray-300 rounded-lg shadow-sm">
            <thead className="bg-gray-200">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300">
                  Domain
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300">
                  Expiry Date
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300">
                  Time Remaining
                </th>
                <th className="px-6 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-b border-gray-300">
                  Status
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {certData.map((cert, index) => (
                <tr key={index} className={cert.error ? "bg-red-50" : cert.is_expired ? "bg-yellow-50" : "hover:bg-gray-100"}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900 border-b border-gray-200">
                    {cert.domain}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 border-b border-gray-200">
                    {cert.expiry_date ? getLocalDateStr(cert.expiry_date) : '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-700 border-b border-gray-200">
                    {cert.time_remaining || '-'}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm border-b border-gray-200">
                    {cert.error ? (
                      <span className="text-red-600 font-semibold">{cert.error}</span>
                    ) : cert.is_expired ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-800">
                        Expired
                      </span>
                    ) : cert.days_remaining !== null && cert.days_remaining < 30 ? (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-yellow-100 text-yellow-800">
                        Expiring Soon
                      </span>
                    ) : (
                      <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-800">
                        Valid
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}

