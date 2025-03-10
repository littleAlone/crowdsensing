<template>
    <div class="home-container">
      <v-container class="pa-0 ma-0 fill-height" fluid>
        <v-row justify="center" align="center" class="ma-0 fill-height">
          <v-col cols="12" md="8" lg="6" xl="5" class="pa-0">
            <v-card class="mx-auto overflow-hidden" elevation="6" shaped>
              <!-- 标题区域 -->
              <v-card-title class="text-h4 font-weight-bold white--text text-center d-block pa-5" style="background-color: #3949AB;">
                多智能体围捕系统
                <v-icon color="white" class="ml-2" small>mdi-sync</v-icon>
              </v-card-title>
              
              <v-card-text class="pa-6">
                <p class="text-body-1 text-center mb-6">
                  欢迎使用多智能体围捕系统。该系统用于模拟猎手智能体如何协同合作追捕目标智能体的过程。
                </p>
                
                <!-- 算法展示 -->
                <v-row justify="center" class="my-4">
                  <v-col cols="auto">
                    <v-chip
                      color="indigo"
                      outlined
                      class="pa-2"
                    >
                      <v-icon left small>mdi-hexagon-outline</v-icon>
                      人工势场法 (APF)
                    </v-chip>
                  </v-col>
                  <v-col cols="auto">
                    <v-chip
                      color="indigo"
                      outlined
                      class="pa-2"
                    >
                      <v-icon left small>mdi-account-group-outline</v-icon>
                      共识算法 (CONSENSUS)
                    </v-chip>
                  </v-col>
                  <v-col cols="auto">
                    <v-chip
                      color="indigo"
                      outlined
                      class="pa-2"
                    >
                      <v-icon left small>mdi-target</v-icon>
                      包围策略 (ENCIRCLEMENT)
                    </v-chip>
                  </v-col>
                </v-row>
                
                <!-- 模拟示意图 -->
                <div class="simulation-preview my-6 mx-auto">
                  <div class="hunter" style="top: 30%; left: 25%;"></div>
                  <div class="hunter" style="top: 70%; left: 30%;"></div>
                  <div class="hunter" style="top: 50%; left: 70%;"></div>
                  <div class="target"></div>
                  <div class="capture-radius"></div>
                </div>
                
                <!-- 操作按钮 -->
                <v-row justify="center" class="mt-6">
                  <v-col cols="12" sm="auto" class="px-2">
                    <v-btn
                      color="indigo darken-1"
                      dark
                      rounded
                      to="/simulations"
                      elevation="2"
                      class="px-6"
                    >
                      <v-icon left>mdi-view-list</v-icon>
                      查看模拟列表
                    </v-btn>
                  </v-col>
                  <v-col cols="12" sm="auto" class="px-2">
                    <v-btn
                      color="light-green darken-1"
                      dark
                      rounded
                      to="/simulations/create"
                      elevation="2"
                      class="px-6"
                    >
                      <v-icon left>mdi-plus</v-icon>
                      创建新模拟
                    </v-btn>
                  </v-col>
                </v-row>
              </v-card-text>
              
              <!-- 底部信息栏 -->
              <v-card-actions class="indigo lighten-5 py-3">
                <v-btn
                  text
                  small
                  color="indigo darken-1"
                  to="/about"
                >
                  <v-icon left small>mdi-information-outline</v-icon>
                  关于系统
                </v-btn>
                <v-spacer></v-spacer>
                <span class="caption text-subtitle-2 grey--text text--darken-1">技术支持: FastAPI + Vue + Vuetify</span>
              </v-card-actions>
            </v-card>
          </v-col>
        </v-row>
      </v-container>
    </div>
  </template>
  
  <script>
  export default {
    name: 'Home'
  }
  </script>
  
  <style>
  /* 全局样式，覆盖默认的body和html样式 */
  html, body {
    margin: 0;
    padding: 0;
    overflow: hidden !important;
    height: 100% !important;
    width: 100% !important;
  }
  
  .v-application {
    min-height: 100vh !important;
    display: flex !important;
    flex-direction: column !important;
  }
  
  /* 确保内容区域不会导致滚动 */
  .v-content__wrap {
    overflow-y: hidden !important;
  }
  </style>
  
  <style scoped>
  .home-container {
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    position: fixed;
    top: 0;
    left: 0;
    background-color: #f5f7fa;
  }
  
  .fill-height {
    height: 100%;
  }
  
  .simulation-preview {
    position: relative;
    height: 200px;
    width: 100%;
    max-width: 500px;
    border: 1px dashed #9fa8da;
    border-radius: 8px;
    background-color: #f5f7fa;
  }
  
  .hunter {
    position: absolute;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: #3949AB;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
  }
  
  .target {
    position: absolute;
    width: 25px;
    height: 25px;
    border-radius: 50%;
    background-color: #e53935;
    top: 45%;
    left: 50%;
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
    animation: float 3s ease-in-out infinite;
  }
  
  .capture-radius {
    position: absolute;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    border: 2px dashed rgba(76, 175, 80, 0.5);
    top: calc(45% - 27.5px);
    left: calc(50% - 27.5px);
    animation: pulse 2s infinite;
  }
  
  @keyframes float {
    0% { transform: translateY(0px); }
    50% { transform: translateY(-8px); }
    100% { transform: translateY(0px); }
  }
  
  @keyframes pulse {
    0% { transform: scale(1); opacity: 0.5; }
    50% { transform: scale(1.1); opacity: 0.3; }
    100% { transform: scale(1); opacity: 0.5; }
  }
  
  /* 确保在小屏幕上按钮正确对齐 */
  @media (max-width: 600px) {
    .v-col {
      padding-top: 8px;
      padding-bottom: 8px;
    }
  }
  </style>