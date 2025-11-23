'use client';

import { useState, useEffect, useCallback, useMemo } from 'react';

// Get domains from environment variable (semicolon-separated)
// Default: "google.com;microsoft.com"
const getDomainsToCheck = () => {
    const envDomains = process.env.NEXT_PUBLIC_DOMAINS_TO_CHECK || 'google.com;microsoft.com';
    return envDomains.split(';').map(d => d.trim()).filter(d => d);
};

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

    // Memoize domainsToCheck so it doesn't change on every render
    const domainsToCheck = useMemo(() => getDomainsToCheck(), []);

    const fetchCertificates = useCallback(async () => {
        setLoading(true);
        setError(null);

        if (domainsToCheck.length === 0) {
            setError('No domains configured. Please set NEXT_PUBLIC_DOMAINS_TO_CHECK environment variable.');
            setLoading(false);
            return;
        }

        const queryParam = domainsToCheck.length === 1
            ? `domain=${encodeURIComponent(domainsToCheck[0])}`
            : `domains=${encodeURIComponent(domainsToCheck.join(','))}`;

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
    }, [domainsToCheck]);

    useEffect(() => {
        // Auto-fetch on mount only
        fetchCertificates();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []); // Empty deps array - only run on mount

    return (
        <div className="max-w-4xl mx-auto p-6">
            {loading && certData.length === 0 ? (
                <div className="flex items-center justify-center min-h-screen -mt-20">
                    <p className="text-gray-600 text-lg">checking...</p>
                </div>
            ) : (
                <>
                    <div className="text-center mb-6">
                        <h1 className="text-2xl font-bold text-gray-800">SSL Certificate Checker</h1>
                    </div>

                    <div className="mb-4 flex justify-end">
                        <button
                            className="px-4 py-2 bg-blue-500 text-white font-medium rounded hover:bg-blue-600 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
                            onClick={fetchCertificates}
                            disabled={loading}
                        >
                            {loading ? 'Refreshing...' : 'REFRESH'}
                        </button>
                    </div>

                    {error && (
                        <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
                            {error}
                        </div>
                    )}

                    {certData.length > 0 ? (
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
                </>
            )}
        </div>
    );
}

