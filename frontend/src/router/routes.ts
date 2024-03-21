export default [
  {
    path: '/',
    name: 'Home',
    component: () => import('../views/MainPage.vue'),
  },
  {
    path: '/country',
    name: 'Country',
    component: () => import('../views/CountryPage.vue'),
  },
];
