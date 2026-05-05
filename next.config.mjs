/** @type {import('next').NextConfig} */
const configuredApiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.trim();
const backendOrigin = configuredApiBaseUrl
    ? configuredApiBaseUrl.replace(/\/api\/?$/, "")
    : process.env.NODE_ENV === "development"
        ? "http://localhost:8001"
        : "https://capstone-app-hqi3.vercel.app";

const nextConfig = {
    async rewrites() {
        return [
            {
                source: "/api/:path*",
                destination: `${backendOrigin}/api/:path*`,
            },
        ];
    },
    images: {
        remotePatterns: [
            {
                protocol: "https",
                hostname: "images.unsplash.com",
            },
            {
                protocol: "https",
                hostname: "plus.unsplash.com",
            }
        ]
    }
};

export default nextConfig;
