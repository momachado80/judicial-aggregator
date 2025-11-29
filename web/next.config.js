/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'export',
    // Disable image optimization since we are doing static export
    images: {
        unoptimized: true,
    },
    // Ensure trailing slashes for static export routing
    trailingSlash: true,
}

module.exports = nextConfig
