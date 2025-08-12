// Service Worker for PWA functionality
const CACHE_NAME = 'cheque-management-v1.0.0';
const STATIC_CACHE = 'static-v1.0.0';
const DYNAMIC_CACHE = 'dynamic-v1.0.0';

// Resources to cache for offline functionality
const STATIC_ASSETS = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/static/js/performance.js',
  '/static/icons/icon-192x192.png',
  '/static/icons/icon-512x512.png',
  '/auth/login',
  '/cheques',
  '/clients',
  '/depositors',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js'
];

// API endpoints to cache for offline access
const API_CACHE_PATTERNS = [
  /\/api\/charts\//,
  /\/api\/clients\/search/,
  /\/api\/depositors\/search/,
  /\/api\/analytics\//
];

// Install event - cache static assets
self.addEventListener('install', event => {
  console.log('Service Worker installing...');
  
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then(cache => {
        console.log('Caching static assets...');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('Static assets cached successfully');
        return self.skipWaiting();
      })
      .catch(error => {
        console.error('Failed to cache static assets:', error);
      })
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
  console.log('Service Worker activating...');
  
  event.waitUntil(
    caches.keys()
      .then(cacheNames => {
        return Promise.all(
          cacheNames.map(cacheName => {
            if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
              console.log('Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('Service Worker activated');
        return self.clients.claim();
      })
  );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);
  
  // Skip non-GET requests
  if (request.method !== 'GET') {
    return;
  }
  
  // Handle different types of requests
  if (request.url.includes('/api/')) {
    event.respondWith(handleApiRequest(request));
  } else if (request.destination === 'image') {
    event.respondWith(handleImageRequest(request));
  } else {
    event.respondWith(handlePageRequest(request));
  }
});

// Handle API requests with cache-first strategy for specific endpoints
async function handleApiRequest(request) {
  const isApiCacheable = API_CACHE_PATTERNS.some(pattern => pattern.test(request.url));
  
  if (isApiCacheable) {
    try {
      // Try cache first for analytics and search data
      const cachedResponse = await caches.match(request);
      if (cachedResponse) {
        // Fetch update in background
        fetchAndCache(request);
        return cachedResponse;
      }
      
      // If not in cache, fetch and cache
      return await fetchAndCache(request);
    } catch (error) {
      console.error('API request failed:', error);
      return new Response(
        JSON.stringify({ error: 'Service unavailable offline' }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  } else {
    // For other API requests, try network first
    try {
      return await fetch(request);
    } catch (error) {
      return new Response(
        JSON.stringify({ error: 'Network unavailable' }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json' }
        }
      );
    }
  }
}

// Handle image requests with cache-first strategy
async function handleImageRequest(request) {
  try {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    
    // Cache successful image responses
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Return a default offline image if available
    return caches.match('/static/icons/offline-image.png') || 
           new Response('', { status: 404 });
  }
}

// Handle page requests with network-first strategy, fallback to cache
async function handlePageRequest(request) {
  try {
    const networkResponse = await fetch(request);
    
    // Cache successful page responses
    if (networkResponse.ok) {
      const cache = await caches.open(DYNAMIC_CACHE);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    // Try to serve from cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If no cache available, return offline page
    return caches.match('/static/offline.html') || 
           new Response('Offline - Please check your connection', {
             status: 503,
             headers: { 'Content-Type': 'text/html' }
           });
  }
}

// Utility function to fetch and cache responses
async function fetchAndCache(request) {
  const networkResponse = await fetch(request);
  
  if (networkResponse.ok) {
    const cache = await caches.open(DYNAMIC_CACHE);
    cache.put(request, networkResponse.clone());
  }
  
  return networkResponse;
}

// Background sync for form submissions when back online
self.addEventListener('sync', event => {
  if (event.tag === 'cheque-submission') {
    event.waitUntil(syncChequeSubmissions());
  } else if (event.tag === 'client-submission') {
    event.waitUntil(syncClientSubmissions());
  }
});

// Sync queued cheque submissions
async function syncChequeSubmissions() {
  try {
    const submissions = await getQueuedSubmissions('cheques');
    
    for (const submission of submissions) {
      try {
        const response = await fetch('/api/cheques/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submission.data)
        });
        
        if (response.ok) {
          await removeQueuedSubmission('cheques', submission.id);
          console.log('Cheque submission synced:', submission.id);
        }
      } catch (error) {
        console.error('Failed to sync cheque submission:', error);
      }
    }
  } catch (error) {
    console.error('Background sync failed:', error);
  }
}

// Sync queued client submissions
async function syncClientSubmissions() {
  try {
    const submissions = await getQueuedSubmissions('clients');
    
    for (const submission of submissions) {
      try {
        const response = await fetch('/api/clients/sync', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(submission.data)
        });
        
        if (response.ok) {
          await removeQueuedSubmission('clients', submission.id);
          console.log('Client submission synced:', submission.id);
        }
      } catch (error) {
        console.error('Failed to sync client submission:', error);
      }
    }
  } catch (error) {
    console.error('Client sync failed:', error);
  }
}

// IndexedDB operations for queued submissions
async function getQueuedSubmissions(type) {
  // Placeholder - would use IndexedDB for offline storage
  return [];
}

async function removeQueuedSubmission(type, id) {
  // Placeholder - would remove from IndexedDB
  console.log(`Removing queued ${type} submission:`, id);
}

// Push notification handling
self.addEventListener('push', event => {
  const options = {
    body: event.data ? event.data.text() : 'Nouvelle notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-icon.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Voir',
        icon: '/static/icons/checkmark.png'
      },
      {
        action: 'close',
        title: 'Fermer',
        icon: '/static/icons/xmark.png'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification('Gestion des Chèques', options)
  );
});

// Notification click handling
self.addEventListener('notificationclick', event => {
  event.notification.close();
  
  if (event.action === 'explore') {
    // Open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    // Just close the notification
    return;
  } else {
    // Default action - open the app
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

// Periodic background sync for data updates
self.addEventListener('periodicsync', event => {
  if (event.tag === 'data-refresh') {
    event.waitUntil(refreshCachedData());
  }
});

// Refresh cached data in background
async function refreshCachedData() {
  try {
    const cache = await caches.open(DYNAMIC_CACHE);
    
    // Refresh critical data
    const urlsToRefresh = [
      '/api/charts/monthly-trends',
      '/api/charts/risk-distribution',
      '/api/analytics/performance'
    ];
    
    for (const url of urlsToRefresh) {
      try {
        const response = await fetch(url);
        if (response.ok) {
          await cache.put(url, response.clone());
        }
      } catch (error) {
        console.error('Failed to refresh cached data for:', url);
      }
    }
    
    console.log('Background data refresh completed');
  } catch (error) {
    console.error('Background refresh failed:', error);
  }
}