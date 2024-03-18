export default [
  {
    path: '/',
    name: 'Main',
    sitemap: {
      changefreq: 'daily',
      priority: 1,
    },
    component: () => import('../views/MainPage.vue'),
  },
];
