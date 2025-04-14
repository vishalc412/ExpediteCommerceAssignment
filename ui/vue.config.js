// vue.config.js
module.exports = {
  devServer: {
    port: 8081, // Match your current port
    proxy: {
      '/api': {
        target: 'https://a68p2cnnk2.execute-api.us-east-2.amazonaws.com',
        changeOrigin: true,
        pathRewrite: {
          '^/api': '/demo'
        },
        logLevel: 'debug',
        onProxyReq(proxyReq, req, res) {
          // Log outgoing request for debugging
          console.log('Proxying request:', req.method, req.path);
        },
        onProxyRes(proxyRes, req, res) {
          // Log incoming response for debugging
          console.log('Proxy response status:', proxyRes.statusCode);
          console.log('Proxy response headers:', proxyRes.headers);
        }
      }
    }
  }
}