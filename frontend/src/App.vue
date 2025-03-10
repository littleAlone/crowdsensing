<template>
    <v-app>
      <v-app-bar app color="primary" dark>
        <v-app-bar-nav-icon @click="drawer = !drawer"></v-app-bar-nav-icon>
        <v-toolbar-title>多智能体围捕系统</v-toolbar-title>
        <v-spacer></v-spacer>
      </v-app-bar>
      
      <v-navigation-drawer v-model="drawer" app temporary>
        <v-list>
          <v-list-item to="/" exact>
            <v-list-item-icon>
              <v-icon>mdi-home</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>首页</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item to="/simulations">
            <v-list-item-icon>
              <v-icon>mdi-view-list</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>模拟列表</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item to="/simulations/create">
            <v-list-item-icon>
              <v-icon>mdi-plus</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>创建模拟</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
          
          <v-list-item to="/about">
            <v-list-item-icon>
              <v-icon>mdi-information</v-icon>
            </v-list-item-icon>
            <v-list-item-content>
              <v-list-item-title>关于</v-list-item-title>
            </v-list-item-content>
          </v-list-item>
        </v-list>
      </v-navigation-drawer>
      
      <v-main>
        <router-view></router-view>
      </v-main>
      
      <v-footer app color="primary" dark>
        <span class="white--text">&copy; {{ new Date().getFullYear() }} - 多智能体围捕系统</span>
      </v-footer>
    </v-app>
  </template>
  
  <script>
  export default {
    name: 'App',
    data() {
      return {
        drawer: false
      }
    }
  }
  </script>
  
  <style>
  /* 全局样式 */
  </style>