<template>
  <div class="about">
    <v-container>
      <v-row justify="center">
        <v-col cols="12" md="10">
          <v-card class="mt-3" elevation="3">
            <v-card-title class="primary white--text py-3">
              关于多智能体围捕系统
            </v-card-title>
            
            <!-- 使用标签页组织内容 -->
            <v-tabs
              v-model="activeTab"
              background-color="primary"
              dark
              grow
            >
              <v-tab>概述</v-tab>
              <v-tab>算法</v-tab>
            </v-tabs>
            
            <v-tabs-items v-model="activeTab">
              <!-- 概述标签页 (包含概述、特性和技术) -->
              <v-tab-item>
                <v-card flat>
                  <v-card-text>
                    <!-- 系统简介部分 -->
                    <h3 class="text-h6 mb-3">系统简介</h3>
                    <p class="text-body-1">
                      多智能体围捕系统是一个用于模拟和分析多个智能体协同工作围捕目标的平台。该系统可以帮助研究人员和学生更好地理解多智能体系统中的协作策略和算法效果。通过直观的可视化界面，用户可以观察不同策略下智能体的行为模式和捕获效率。
                    </p>
                    
                    <v-divider class="my-5"></v-divider>
                    
                    <!-- 特性部分 -->
                    <h3 class="text-h6 mb-3">系统特性</h3>
                    <v-row>
                      <v-col cols="12" sm="6">
                        <v-list-item>
                          <v-list-item-icon>
                            <v-icon color="primary">mdi-eye</v-icon>
                          </v-list-item-icon>
                          <v-list-item-content>
                            <v-list-item-title>实时可视化</v-list-item-title>
                            <v-list-item-subtitle>
                              通过交互式画布实时展示智能体运动轨迹和行为模式
                            </v-list-item-subtitle>
                          </v-list-item-content>
                        </v-list-item>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-list-item>
                          <v-list-item-icon>
                            <v-icon color="primary">mdi-chart-line</v-icon>
                          </v-list-item-icon>
                          <v-list-item-content>
                            <v-list-item-title>数据分析</v-list-item-title>
                            <v-list-item-subtitle>
                              提供智能体距离统计、捕获时间分析等数据指标
                            </v-list-item-subtitle>
                          </v-list-item-content>
                        </v-list-item>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-list-item>
                          <v-list-item-icon>
                            <v-icon color="primary">mdi-cogs</v-icon>
                          </v-list-item-icon>
                          <v-list-item-content>
                            <v-list-item-title>参数配置</v-list-item-title>
                            <v-list-item-subtitle>
                              支持自定义环境大小、智能体数量和算法类型
                            </v-list-item-subtitle>
                          </v-list-item-content>
                        </v-list-item>
                      </v-col>
                      
                      <v-col cols="12" sm="6">
                        <v-list-item>
                          <v-list-item-icon>
                            <v-icon color="primary">mdi-cube-outline</v-icon>
                          </v-list-item-icon>
                          <v-list-item-content>
                            <v-list-item-title>环境设置</v-list-item-title>
                            <v-list-item-subtitle>
                              可添加障碍物，模拟不同环境下的围捕效果
                            </v-list-item-subtitle>
                          </v-list-item-content>
                        </v-list-item>
                      </v-col>
                    </v-row>
                    
                    <v-divider class="my-5"></v-divider>
                    
                    <!-- 技术部分 -->
                    <h3 class="text-h6 mb-3">技术架构</h3>
                    <p class="text-body-1">本系统采用前后端分离架构：</p>
                    
                    <v-row>
                      <v-col cols="12" md="6">
                        <v-card outlined>
                          <v-card-title class="subtitle-1">
                            <v-icon left color="primary">mdi-server</v-icon>
                            后端技术
                          </v-card-title>
                          <v-list dense>
                            <v-list-item>
                              <v-list-item-icon>
                                <v-icon small>mdi-language-python</v-icon>
                              </v-list-item-icon>
                              <v-list-item-content>
                                Python FastAPI
                              </v-list-item-content>
                            </v-list-item>
                            <v-list-item>
                              <v-list-item-icon>
                                <v-icon small>mdi-database</v-icon>
                              </v-list-item-icon>
                              <v-list-item-content>
                                SQLAlchemy, SQLite
                              </v-list-item-content>
                            </v-list-item>
                            <v-list-item>
                              <v-list-item-icon>
                                <v-icon small>mdi-math-compass</v-icon>
                              </v-list-item-icon>
                              <v-list-item-content>
                                Numpy
                              </v-list-item-content>
                            </v-list-item>
                          </v-list>
                        </v-card>
                      </v-col>
                      
                      <v-col cols="12" md="6">
                        <v-card outlined>
                          <v-card-title class="subtitle-1">
                            <v-icon left color="primary">mdi-monitor-dashboard</v-icon>
                            前端技术
                          </v-card-title>
                          <v-list dense>
                            <v-list-item>
                              <v-list-item-icon>
                                <v-icon small>mdi-vuejs</v-icon>
                              </v-list-item-icon>
                              <v-list-item-content>
                                Vue.js, Vuetify
                              </v-list-item-content>
                            </v-list-item>
                            <v-list-item>
                              <v-list-item-icon>
                                <v-icon small>mdi-chart-bar</v-icon>
                              </v-list-item-icon>
                              <v-list-item-content>
                                ApexCharts
                              </v-list-item-content>
                            </v-list-item>
                            <v-list-item>
                              <v-list-item-icon>
                                <v-icon small>mdi-palette</v-icon>
                              </v-list-item-icon>
                              <v-list-item-content>
                                Canvas
                              </v-list-item-content>
                            </v-list-item>
                          </v-list>
                        </v-card>
                      </v-col>
                    </v-row>
                    
                    <div class="mt-4">
                      <p class="text-body-1">
                        <v-icon small>mdi-information-outline</v-icon>
                        <span class="ml-1">如有问题或建议，请联系系统管理员。</span>
                      </p>
                    </div>
                  </v-card-text>
                </v-card>
              </v-tab-item>
              
              <!-- 算法标签页 -->
              <v-tab-item>
                <v-card flat>
                  <v-card-text>
                    <!-- 猎手算法部分 -->
                    <h3 class="text-h6 mb-3">猎手算法详解</h3>
                    <p class="text-body-1 mb-4">
                      猎手智能体采用多种不同的协同策略来实现对目标的有效围捕。每种算法都有其独特的行为特征和适用场景。
                    </p>
                    
                    <v-expansion-panels>
                      <!-- 人工势场法 -->
                      <v-expansion-panel>
                        <v-expansion-panel-header>
                          <div class="d-flex align-center">
                            <v-icon color="primary" class="mr-2">mdi-hexagon-outline</v-icon>
                            <span class="font-weight-medium">人工势场法 (APF)</span>
                          </div>
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                          <v-card-text>
                            <p class="text-body-1">
                              人工势场法(Artificial Potential Field)是一种常用于机器人路径规划的方法，在多智能体围捕中表现出色。
                            </p>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">原理</h4>
                            <p class="text-body-2">
                              该方法将环境中的各个元素建模为产生"力场"的源。目标产生吸引力场，吸引猎手向它靠近；其他猎手和障碍物产生排斥力场，防止碰撞。
                            </p>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">实现细节</h4>
                            <v-card outlined class="my-2 pa-2">
                              <p class="mb-0"><strong>吸引力</strong>: 与目标距离成正比，距离越远，吸引力越大，但有上限</p>
                              <p class="mb-0"><strong>排斥力</strong>: 与障碍物距离成反比，距离越近，排斥力越大</p>
                              <p class="mb-0"><strong>合力计算</strong>: 所有力的向量和决定猎手的运动方向</p>
                            </v-card>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">特点</h4>
                            <v-row>
                              <v-col cols="12" md="6">
                                <v-list dense>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="success" small>mdi-check</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>实现简单，计算效率高</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="success" small>mdi-check</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>对环境变化有较强适应性</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                </v-list>
                              </v-col>
                              <v-col cols="12" md="6">
                                <v-list dense>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="error" small>mdi-close</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>容易陷入局部最优解</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="error" small>mdi-close</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>在复杂环境中效率降低</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                </v-list>
                              </v-col>
                            </v-row>
                          </v-card-text>
                        </v-expansion-panel-content>
                      </v-expansion-panel>
                      
                      <!-- 共识算法 -->
                      <v-expansion-panel>
                        <v-expansion-panel-header>
                          <div class="d-flex align-center">
                            <v-icon color="primary" class="mr-2">mdi-account-group-outline</v-icon>
                            <span class="font-weight-medium">共识算法 (CONSENSUS)</span>
                          </div>
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                          <v-card-text>
                            <p class="text-body-1">
                              共识算法(Consensus Algorithm)是一种基于多智能体通信和信息共享的协作方法，强调团队决策的一致性。
                            </p>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">原理</h4>
                            <p class="text-body-2">
                              猎手通过通信网络共享各自对目标位置的估计，然后通过加权平均等方式形成对目标位置的共识，协调移动策略。
                            </p>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">实现细节</h4>
                            <v-card outlined class="my-2 pa-2">
                              <p class="mb-0"><strong>信息共享</strong>: 每个猎手与通信范围内的其他猎手共享目标信息</p>
                              <p class="mb-0"><strong>共识形成</strong>: 基于收到的信息，更新自身对目标位置的估计</p>
                              <p class="mb-0"><strong>协调行动</strong>: 基于共识后的目标位置，计算最优追捕路径</p>
                            </v-card>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">特点</h4>
                            <v-row>
                              <v-col cols="12" md="6">
                                <v-list dense>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="success" small>mdi-check</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>提高目标定位精度</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="success" small>mdi-check</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>减少追捕所需时间</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                </v-list>
                              </v-col>
                              <v-col cols="12" md="6">
                                <v-list dense>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="error" small>mdi-close</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>通信开销较大</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="error" small>mdi-close</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>依赖稳定的通信网络</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                </v-list>
                              </v-col>
                            </v-row>
                          </v-card-text>
                        </v-expansion-panel-content>
                      </v-expansion-panel>
                      
                      <!-- 包围策略 -->
                      <v-expansion-panel>
                        <v-expansion-panel-header>
                          <div class="d-flex align-center">
                            <v-icon color="primary" class="mr-2">mdi-target</v-icon>
                            <span class="font-weight-medium">包围策略 (ENCIRCLEMENT)</span>
                          </div>
                        </v-expansion-panel-header>
                        <v-expansion-panel-content>
                          <v-card-text>
                            <p class="text-body-1">
                              包围策略(Encirclement Strategy)是一种高级协作方法，智能体通过形成包围圈来限制目标的移动空间。
                            </p>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">原理</h4>
                            <p class="text-body-2">
                              猎手根据目标位置和其他猎手的分布，计算最优的包围位置。这些位置通常均匀分布在目标周围，形成一个完整的包围圈。
                            </p>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">实现细节</h4>
                            <v-card outlined class="my-2 pa-2">
                              <p class="mb-0"><strong>角色分配</strong>: 猎手根据位置和能力分配不同角色</p>
                              <p class="mb-0"><strong>包围点计算</strong>: 在目标周围计算理想包围点</p>
                              <p class="mb-0"><strong>位置调整</strong>: 猎手根据分配的角色移向对应包围点</p>
                            </v-card>
                            
                            <h4 class="subtitle-1 font-weight-bold mt-3">特点</h4>
                            <v-row>
                              <v-col cols="12" md="6">
                                <v-list dense>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="success" small>mdi-check</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>高效限制目标移动</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="success" small>mdi-check</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>适应目标逃跑策略</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                </v-list>
                              </v-col>
                              <v-col cols="12" md="6">
                                <v-list dense>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="error" small>mdi-close</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>算法复杂度高</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                  <v-list-item>
                                    <v-list-item-icon>
                                      <v-icon color="error" small>mdi-close</v-icon>
                                    </v-list-item-icon>
                                    <v-list-item-content>
                                      <v-list-item-title>需要较多猎手数量</v-list-item-title>
                                    </v-list-item-content>
                                  </v-list-item>
                                </v-list>
                              </v-col>
                            </v-row>
                          </v-card-text>
                        </v-expansion-panel-content>
                      </v-expansion-panel>
                    </v-expansion-panels>
                    
                    <!-- 目标算法部分 -->
                    <h3 class="text-h6 mb-3 mt-6">目标智能体算法</h3>
                    <p class="text-body-1 mb-4">
                      目标智能体代表被追捕的对象，采用智能逃避策略来避开猎手的围捕。
                    </p>
                    
                    <v-card outlined class="mb-4">
                      <v-card-title class="subtitle-1">
                        <v-icon left color="error">mdi-run-fast</v-icon>
                        逃避策略
                      </v-card-title>
                      
                      <v-card-text>
                        <h4 class="subtitle-1 font-weight-bold">基本原理</h4>
                        <p class="text-body-2">
                          目标智能体通过感知周围猎手的位置，计算逃离方向。它会优先考虑逃向猎手密度低的区域，同时考虑环境边界和障碍物的影响。
                        </p>
                        
                        <h4 class="subtitle-1 font-weight-bold mt-3">主要策略</h4>
                        <v-row>
                          <v-col cols="12" md="6">
                            <v-list dense>
                              <v-list-item>
                                <v-list-item-icon>
                                  <v-icon color="error" small>mdi-arrow-up-bold</v-icon>
                                </v-list-item-icon>
                                <v-list-item-content>
                                  <v-list-item-title>猎手反向策略</v-list-item-title>
                                  <v-list-item-subtitle>
                                    计算远离所有可见猎手的方向
                                  </v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                              
                              <v-list-item>
                                <v-list-item-icon>
                                  <v-icon color="error" small>mdi-map-marker-path</v-icon>
                                </v-list-item-icon>
                                <v-list-item-content>
                                  <v-list-item-title>路径预测</v-list-item-title>
                                  <v-list-item-subtitle>
                                    预测猎手未来位置并避开
                                  </v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                            </v-list>
                          </v-col>
                          
                          <v-col cols="12" md="6">
                            <v-list dense>
                              <v-list-item>
                                <v-list-item-icon>
                                  <v-icon color="error" small>mdi-wall</v-icon>
                                </v-list-item-icon>
                                <v-list-item-content>
                                  <v-list-item-title>障碍物利用</v-list-item-title>
                                  <v-list-item-subtitle>
                                    利用障碍物阻挡猎手视线和移动
                                  </v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                              
                              <v-list-item>
                                <v-list-item-icon>
                                  <v-icon color="error" small>mdi-exit-run</v-icon>
                                </v-list-item-icon>
                                <v-list-item-content>
                                  <v-list-item-title>边界逃脱</v-list-item-title>
                                  <v-list-item-subtitle>
                                    当接近边界时尝试快速逃出环境
                                  </v-list-item-subtitle>
                                </v-list-item-content>
                              </v-list-item>
                            </v-list>
                          </v-col>
                        </v-row>
                      </v-card-text>
                    </v-card>
                  </v-card-text>
                </v-card>
              </v-tab-item>
            </v-tabs-items>
            
            <v-divider></v-divider>
            
            <v-card-actions>
              <v-spacer></v-spacer>
              <v-btn
                color="primary"
                to="/"
                text
              >
                <v-icon left>mdi-home</v-icon>
                返回首页
              </v-btn>
            </v-card-actions>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
  </div>
</template>

<script>
export default {
  name: 'About',
  data() {
    return {
      activeTab: 0
    }
  }
}
</script>

<style scoped>
.about {
  min-height: 100vh;
  padding: 20px 0;
  background-color: #f5f5f5;
}
</style>