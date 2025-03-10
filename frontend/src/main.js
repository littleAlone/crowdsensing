import Vue from 'vue'
import App from './App.vue'
import router from './router'
import store from './store'
import './assets/styles/global.css';

// 导入Vuetify
import Vuetify from 'vuetify'
import 'vuetify/dist/vuetify.min.css'
Vue.use(Vuetify)

// 导入图表库
import VueApexCharts from 'vue-apexcharts'
Vue.component('apexchart', VueApexCharts)

// 导入通知插件
import VueToast from 'vue-toast-notification'
import 'vue-toast-notification/dist/theme-sugar.css'
Vue.use(VueToast)

// 导入Axios
import axios from 'axios'
import VueAxios from 'vue-axios'

// 配置API基础URL
axios.defaults.baseURL = 'http://localhost:8000/api/v1'
axios.defaults.withCredentials = false;
Vue.use(VueAxios, axios)

// 添加全局响应拦截器，统一处理响应
axios.interceptors.response.use(
  response => response, 
  error => {
    console.error('API错误:', error)
    return Promise.reject(error)
  }
)

Vue.config.productionTip = false

new Vue({
  router,
  store,
  vuetify: new Vuetify({
    theme: {
      dark: false,
      themes: {
        light: {
          primary: '#3f51b5',
          secondary: '#673ab7',
          accent: '#e91e63',
          error: '#f44336',
          warning: '#ff9800',
          info: '#2196f3',
          success: '#4caf50'
        }
      }
    }
  }),
  render: h => h(App)
}).$mount('#app')