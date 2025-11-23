import './globals.css';

export const metadata = {
  title: 'SSL Certificate Checker',
  description: 'Check SSL certificate expiration for domains',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}

