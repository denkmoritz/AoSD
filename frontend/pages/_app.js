import '../styles/globals.css';
import Link from 'next/link';

function MyApp({ Component, pageProps }) {
    return (
        <div>
            <nav style={{ backgroundColor: "#333", padding: "10px" }}>
                <Link href="/" style={{ color: "white", marginRight: "20px" }}>🏠 Home</Link>
                <Link href="/radar" style={{ color: "white" }}>📡 Pollution Radar</Link>
            </nav>
            <Component {...pageProps} />
        </div>
    );
}

export default MyApp;