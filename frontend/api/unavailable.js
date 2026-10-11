// Replace the /api rewrite with the hosted FastAPI URL when it is provisioned.
export default function handler(request, response) {
  response.setHeader('Cache-Control', 'no-store');
  response.status(503).json({
    detail: 'The online workspace is being set up. Document uploads, the dashboard, assistant, and reports will be available after the backend is connected. You can watch the product demo at /product-demo/Watch-demo.html.',
  });
}
