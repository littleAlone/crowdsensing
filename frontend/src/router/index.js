import Vue from 'vue'
import VueRouter from 'vue-router'

// 导入视图组件
import Home from '../views/Home.vue'
import SimulationList from '../views/SimulationList.vue'
import SimulationDetail from '../views/SimulationDetail.vue'
import SimulationCreate from '../views/SimulationCreate.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home
  },
  {
    path: '/simulations',
    name: 'SimulationList',
    component: SimulationList
  },
  {
    path: '/simulations/create',
    name: 'SimulationCreate',
    component: SimulationCreate
  },
  {
    path: '/simulations/:id',
    name: 'SimulationDetail',
    component: SimulationDetail,
    props: route => ({ 
      simulationId: parseInt(route.params.id)
    })
  },
  {
    path: '/about',
    name: 'About',
    component: () => import(/* webpackChunkName: "about" */ '../views/About.vue')
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  routes
})

export default router