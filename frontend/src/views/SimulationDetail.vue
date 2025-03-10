<template>
  <div class="simulation-detail">
    <v-container fluid class="content-container">
      <v-row no-gutters class="content-row">
        <!-- 左侧模拟画布区域 -->
        <v-col cols="12" md="8" class="pr-md-2">
          <v-card class="simulation-canvas-card">
            <div class="d-flex align-center px-2">
              <div class="title-section">
                <span class="subtitle-1 font-weight-medium">{{ simulation.name }}</span>
              </div>
              <v-spacer></v-spacer>
              <v-chip x-small :color="statusChipColor" text-color="white" class="mx-1">
                {{ statusChipText }}
              </v-chip>
              <!-- 添加目标捕获进度指示器 -->
              <v-chip x-small :color="getProgressColor" text-color="white" class="ml-1">
                已捕获: {{simulation.captured_targets_count || 0}}/{{getTotalTargets}}
              </v-chip>
            </div>
            
            <!-- 模拟画布 - 传递障碍物信息 -->
            <simulation-canvas
              ref="canvas"
              :hunters="simulation.hunters || []"
              :targets="simulation.targets || []"
              :environment-size="simulation.environment_size || 500"
              :is-running="isRunning"
              :is-captured="isCaptured"
              :escaped="isEscaped"
              :show-trails="showTrails"
              :show-vision-range="showVisionRange"
              :show-communication-range="showCommunicationRange"
              :obstacles="simulation.obstacles || []"
            ></simulation-canvas>
          </v-card>
        </v-col>
        
        <!-- 右侧控制面板和数据分析区域 -->
        <v-col cols="12" md="4">
          <v-card class="control-panel mb-2">
            <v-card-title class="py-1 subtitle-1">控制面板</v-card-title>
            <v-card-text class="py-1">
              <!-- 控制按钮组 -->
              <div class="d-flex mb-3 justify-center">
                <v-btn small color="primary" :disabled="isRunning || isCaptured || isEscaped" @click="startSimulation" class="mx-1">
                  <v-icon small left>mdi-play</v-icon>开始
                </v-btn>
                <v-btn small color="error" :disabled="!isRunning" @click="stopSimulation" class="mx-1">
                  <v-icon small left>mdi-stop</v-icon>停止
                </v-btn>
                <v-btn small color="warning" :disabled="isRunning" @click="resetSimulation" class="mx-1">
                  <v-icon small left>mdi-refresh</v-icon>重置
                </v-btn>
              </div>
              
              <!-- 显示选项 -->
              <div class="display-options mb-2">
                <div class="subtitle-2 mb-1">显示选项</div>
                <v-row dense>
                  <v-col cols="4">
                    <v-switch dense hide-details label="轨迹" v-model="showTrails" class="mt-0"></v-switch>
                  </v-col>
                  <v-col cols="4">
                    <v-switch dense hide-details label="视野范围" v-model="showVisionRange" class="mt-0"></v-switch>
                  </v-col>
                  <v-col cols="4">
                    <v-switch dense hide-details label="通信范围" v-model="showCommunicationRange" class="mt-0"></v-switch>
                  </v-col>
                </v-row>
              </div>
            </v-card-text>
          </v-card>

          <!-- 环境设置面板 -->
          <v-card class="mb-2">
            <environment-settings-panel
              :is-running="isRunning"
              :current-obstacles="simulation.obstacles || []"
              @toggle-obstacles="toggleObstacles"
              @regenerate-obstacles="regenerateObstacles"
            ></environment-settings-panel>
          </v-card>
          
          <!-- 数据分析区域 - 使用标签页组织内容 -->
          <v-card>
            <v-tabs v-model="activeTab" background-color="primary" dark dense>
              <v-tab>模拟信息</v-tab>
              <v-tab>统计图表</v-tab>
            </v-tabs>
            
            <v-tabs-items v-model="activeTab">
              <v-tab-item>
                <simulation-info :simulation="simulation"></simulation-info>
              </v-tab-item>
              <v-tab-item>
                <hunter-statistics-chart
                  :hunters="simulation.hunters || []"
                  :targets="simulation.targets || []"
                  :step-count="simulation.step_count || 0"
                  :is-running="isRunning"
                ></hunter-statistics-chart>
                
                <performance-monitor
                  v-if="simulation.step_count > 0"
                  :render-time="renderTime"
                  :ws-latency="wsLatency"
                ></performance-monitor>
              </v-tab-item>
            </v-tabs-items>
          </v-card>
          
          <!-- 底部操作按钮 -->
          <v-card class="mt-2 pa-2">
            <div class="d-flex justify-space-between">
              <v-btn small text color="primary" @click="navigateToList">
                <v-icon small left>mdi-arrow-left</v-icon>返回列表
              </v-btn>
              <v-btn small text color="error" @click="showDeleteDialog = true">
                <v-icon small left>mdi-delete</v-icon>删除模拟
              </v-btn>
            </div>
          </v-card>
        </v-col>
      </v-row>
    </v-container>
    
    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="headline">确认删除?</v-card-title>
        <v-card-text>此操作将永久删除该模拟及其所有相关数据，无法恢复。</v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn text @click="showDeleteDialog = false">取消</v-btn>
          <v-btn color="error" text @click="deleteSimulation" :loading="deleteLoading">确认删除</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
// 导入组件
import SimulationCanvas from '../components/SimulationCanvas.vue';
import SimulationInfo from '../components/simulation/SimulationInfo.vue';
import HunterStatisticsChart from '../components/simulation/HunterStatisticsChart.vue';
import PerformanceMonitor from '../components/simulation/PerformanceMonitor.vue';
import EnvironmentSettingsPanel from '../components/simulation/EnvironmentSettingsPanel.vue';
import { setupWebSocket, closeWebSocket } from '../components/simulation/WebSocketManager.js';
import { mapState, mapGetters } from 'vuex';

export default {
  name: 'SimulationDetail',
  components: {
    SimulationCanvas,
    SimulationInfo,
    HunterStatisticsChart,
    PerformanceMonitor,
    EnvironmentSettingsPanel
  },
  props: {
    simulationId: {
      type: Number,
      required: true
    }
  },
  data() {
    return {
      simulation: {},
      isRunning: false,
      isCaptured: false,
      isEscaped: false,
      socket: null,
      showTrails: true,
      showVisionRange: false,
      showCommunicationRange: false,
      showDeleteDialog: false,
      deleteLoading: false,
      
      // 添加缺失的响应式属性
      activeTab: 0,
      
      // WebSocket相关状态
      wsLatency: 0,
      lastMessageTime: 0,
      
      // 连接状态提示
      showConnectionStatus: false,
      connectionStatusText: '',
      connectionStatusColor: 'info',
      
      // 性能监控
      renderTime: 0,
      lastRenderTimestamp: 0,
      
      // 数据处理相关
      dataUpdateTimer: null,
      
      // 连接状态标记
      isConnecting: false,
      
      // 捕获状态跟踪
      partialCaptureNotified: false,
      obstacleCount: 3 // 默认障碍物数量
    }
  },
  computed: {
    ...mapState({
      storeCurrentSimulation: state => state.currentSimulation,
      simulationsLoading: state => state.loading
    }),
    ...mapGetters([
      'getSimulationById'
    ]),
    statusChipColor() {
      if (this.isCaptured) return 'success';
      if (this.isEscaped) return 'warning';
      if (this.isRunning) return 'primary';
      return 'grey';
    },
    statusChipText() {
      if (this.isCaptured) return '已捕获';
      if (this.isEscaped) return '已逃脱';
      if (this.isRunning) return '进行中';
      return '已停止';
    },
    getTotalTargets() {
      // 如果有明确的总数则使用，否则计算当前剩余+已捕获
      return this.simulation.total_targets_count || 
             ((this.simulation.targets ? this.simulation.targets.length : 0) + 
              (this.simulation.captured_targets_count || 0) +
              (this.simulation.escaped_targets_count || 0));
    },
    getProgressColor() {
      const captured = this.simulation.captured_targets_count || 0;
      const total = this.getTotalTargets;
      
      if (captured === 0) return 'grey';
      if (captured < total) return 'info';
      return 'success';
    }
  },
  created() {
    // 注册错误处理事件监听
    this.$root.$on('api-error', this.handleApiError);
  },
  mounted() {
    console.log('SimulationDetail mounted');
    // 监听页面可见性变化
    document.addEventListener('visibilitychange', this.handleVisibilityChange);
    window.addEventListener('focus', this.handleWindowFocus);
    window.addEventListener('blur', this.handleWindowBlur);
    
    // 初始化组件
    this.initializeComponent();
  },
  beforeDestroy() {
    console.log('SimulationDetail beforeDestroy');
    // 清理资源
    this.closeWebSocketConnection();
    this.cleanupTimers();
    
    // 移除事件监听
    this.$root.$off('api-error', this.handleApiError);
    document.removeEventListener('visibilitychange', this.handleVisibilityChange);
    window.removeEventListener('focus', this.handleWindowFocus);
    window.removeEventListener('blur', this.handleWindowBlur);
  },
  methods: {
    // 初始化组件
    async initializeComponent() {
      console.log('初始化组件...');
      try {
        // 从API获取模拟数据
        await this.fetchSimulation();
        console.log('模拟数据获取成功:', this.simulation.id);

        // 检查障碍物数量，如果为0但输入值不为0，则生成障碍物
        if ((!this.simulation.obstacles || this.simulation.obstacles.length === 0) && 
            this.obstacleCount > 0) {
          console.log('初始化障碍物...');
          await this.regenerateObstacles(this.obstacleCount);
        }
          
        // 设置捕获状态和逃脱状态
        this.isRunning = this.simulation.is_running;
        this.isCaptured = this.simulation.is_captured;
        this.isEscaped = this.simulation.escaped || false;
        
        // 确保数据格式正确
        if (typeof this.simulation.hunters === 'string') {
          try {
            this.simulation.hunters = JSON.parse(this.simulation.hunters);
          } catch (e) {
            console.error('解析hunters失败:', e);
            this.simulation.hunters = [];
          }
        }
        
        if (typeof this.simulation.targets === 'string') {
          try {
            this.simulation.targets = JSON.parse(this.simulation.targets);
          } catch (e) {
            console.error('解析targets失败:', e);
            this.simulation.targets = [];
          }
        }
        
        // 仅在模拟正在运行且未被捕获/未逃脱时建立WebSocket连接
        if (this.isRunning && !this.isCaptured && !this.isEscaped) {
          this.setupWebSocketConnection();
        } else if (this.isCaptured || this.isEscaped) {
          // 如果模拟已经完成，显示完成状态
          console.log('模拟已完成，显示最终状态');
          
          // 确保画布知道模拟已完成
          this.$nextTick(() => {
            if (this.$refs.canvas) {
              this.$refs.canvas.needsRender = true;
              // 强制最终状态
              if (this.$refs.canvas.lastRenderState) {
                this.$refs.canvas.lastRenderState = {
                  isCaptured: this.isCaptured,
                  isEscaped: this.isEscaped
                };
              }
              // 强制重绘一次
              this.$refs.canvas.drawSimulation(true);
            }
          });
          
          // 加载最终快照数据
          this.loadFinalSnapshot();
        }
      } catch (error) {
        console.error('初始化组件失败:', error);
        this.showErrorStatus('初始化失败，请刷新页面重试');
      }
    },

    // 添加加载最终快照的方法
    async loadFinalSnapshot() {
      try {
        // 尝试加载捕获时的快照
        const response = await this.axios.get(`/simulations/${this.simulationId}/final-snapshot`);
        if (response.data) {
          console.log('获取到最终快照数据:', response.data);
          
          // 更新模拟状态
          if (response.data.is_captured !== undefined) {
            this.isCaptured = response.data.is_captured;
          }
          
          // 更新步数
          if (response.data.step !== undefined) {
            this.simulation.step_count = response.data.step;
          }
          
          // 更新捕获时间
          if (response.data.capture_time !== undefined && response.data.capture_time !== null) {
            this.simulation.capture_time = response.data.capture_time;
          }
          
          // 更新显示数据
          if (response.data.hunters) {
            // 确保hunters是数组
            this.simulation.hunters = Array.isArray(response.data.hunters) ? 
              response.data.hunters : JSON.parse(response.data.hunters);
          }
          
          if (response.data.targets) {
            // 确保targets是数组
            this.simulation.targets = Array.isArray(response.data.targets) ? 
              response.data.targets : JSON.parse(response.data.targets);
          }
          
          // 更新捕获目标数量
          if (response.data.captured_targets_count !== undefined) {
            this.simulation.captured_targets_count = response.data.captured_targets_count;
          }
          
          // 更新创建时间
          if (response.data.creation_time) {
            this.simulation.created_at = response.data.creation_time;
          }
          
          // 强制重绘画布
          this.$nextTick(() => {
            if (this.$refs.canvas) {
              this.$refs.canvas.drawSimulation(true);
            }
          });
        }
      } catch (e) {
        console.warn('加载最终快照失败:', e);
        // 加载失败时不中断流程，使用默认显示
      }
    },
    
    // 获取模拟数据
    async fetchSimulation() {
      try {
        console.log('获取模拟数据, ID:', this.simulationId);
        // 尝试从store获取数据
        let storeSimulation = this.getSimulationById(this.simulationId);
        
        // 如果store中没有数据，从API获取
        if (!storeSimulation) {
          console.log('从API获取模拟数据');
          const response = await this.$store.dispatch('fetchSimulation', this.simulationId);
          this.simulation = response;
        } else {
          console.log('从Store获取模拟数据');
          this.simulation = storeSimulation;
        }
        
        // 更新状态
        this.isRunning = this.simulation.is_running;
        this.isCaptured = this.simulation.is_captured;
        this.isEscaped = this.simulation.escaped || false;
        
        console.log('模拟数据获取完成:', this.simulation.name);
        return this.simulation;
      } catch (error) {
        console.error('获取模拟数据失败:', error);
        this.$toast.error('获取模拟数据失败');
        throw error;
      }
    },
    
    // 设置WebSocket连接
    setupWebSocketConnection() {
      // 连接创建中标记，防止重复创建
      if (this.isConnecting) {
        console.log('WebSocket连接已在创建中，避免重复创建');
        return;
      }
      
      this.isConnecting = true;
      
      // 确保先关闭已有连接
      if (this.socket) {
        console.log('关闭已有WebSocket连接，准备创建新连接');
        this.closeWebSocketConnection();
        
        // 添加短延迟确保连接完全关闭
        setTimeout(() => {
          this.createNewWebSocketConnection();
        }, 300);
      } else {
        this.createNewWebSocketConnection();
      }
    },
    
    // 提取创建连接的逻辑为单独方法
    createNewWebSocketConnection() {
      console.log(`创建WebSocket连接，模拟ID: ${this.simulationId}`);
      
      this.socket = setupWebSocket(this.simulationId, {
        onOpen: () => {
          console.log(`WebSocket连接已建立，模拟ID: ${this.simulationId}`);
          this.showSuccessStatus('WebSocket连接已建立');
          this.isConnecting = false; // 重置连接状态
        },
        onMessage: (data) => {
          this.handleWebSocketMessage(data);
        },
        onClose: (event) => {
          // 如果是正常关闭，不显示错误
          if (event.code !== 1000 && event.code !== 1001) {
            this.showWarningStatus('WebSocket连接已关闭');
          }
          this.isConnecting = false; // 重置连接状态
        },
        onError: () => {
          this.showErrorStatus('WebSocket连接错误');
          this.isConnecting = false; // 重置连接状态
        },
        onReconnect: (newSocket) => {
          this.socket = newSocket;
          this.showInfoStatus('WebSocket已重新连接');
        }
      });
    },
    
    // 改进closeWebSocketConnection方法
    closeWebSocketConnection() {
      if (this.socket) {
        console.log(`关闭WebSocket连接，模拟ID: ${this.simulationId}，原因: ${new Error().stack}`);
        try {
          closeWebSocket(this.socket);
        } catch (e) {
          console.error('关闭WebSocket时出错:', e);
        } finally {
          this.socket = null;
          this.isConnecting = false;
        }
      }
    },
    
    // 处理WebSocket消息
    handleWebSocketMessage(data) {
      try {
        // 记录接收到的消息内容，便于调试
        console.log('收到WebSocket消息:', {
          isRunning: data?.is_running,
          isCaptured: data?.is_captured,
          isEscaped: data?.escaped,
          targetCount: data?.targets?.length || 0,
          capturedCount: data?.captured_targets_count || 0,
          escapedCount: data?.escaped_targets_count || 0,
          totalTargets: data?.total_targets_count || 0
        });
        
        // 如果模拟已完成，忽略后续消息
        if (this.isCaptured || this.isEscaped) {
          console.log('模拟已完成，忽略WebSocket消息');
          return;
        }
        
        // 计算WebSocket延迟
        this.calculateWsLatency();
        
        // 数据有效性检查
        if (!data || typeof data !== 'object') {
          console.error('收到无效WebSocket消息:', data);
          return; // 不关闭连接，只忽略此消息
        }
        
        // 处理错误消息
        if (data.error) {
          console.error('WebSocket错误:', data.error);
          this.$toast.error(`WebSocket错误: ${data.error}`);
          return;
        }
        
        // 创建安全的数据对象，替换所有undefined值
        const safeData = {
          id: data.id || this.simulationId,
          is_running: data.is_running === undefined ? this.isRunning : data.is_running,
          is_captured: data.is_captured === undefined ? this.isCaptured : data.is_captured,
          escaped: data.escaped === undefined ? this.isEscaped : data.escaped,
          hunters: Array.isArray(data.hunters) ? data.hunters : [],
          targets: Array.isArray(data.targets) ? data.targets : [],
          step_count: Number.isFinite(data.step_count) ? data.step_count : 0,
          captured_targets_count: Number.isFinite(data.captured_targets_count) ? data.captured_targets_count : 0,
          escaped_targets_count: Number.isFinite(data.escaped_targets_count) ? data.escaped_targets_count : 0,
          total_targets_count: Number.isFinite(data.total_targets_count) ? data.total_targets_count : 0,
          obstacles: Array.isArray(data.obstacles) ? data.obstacles : this.simulation?.obstacles || []
        };
        
        // 检查模拟是否刚完成
        const allCaptured = safeData.is_captured && (!safeData.targets || safeData.targets.length === 0);
        const allEscaped = safeData.escaped && (!safeData.targets || safeData.targets.length === 0);
        
        // 检查是否有新捕获的目标
        const capturedCount = safeData.captured_targets_count || 0;
        const previousCapturedCount = this.simulation?.captured_targets_count || 0;
        const newCaptures = capturedCount > previousCapturedCount;
        
        // 检查是否有新逃脱的目标
        const escapedCount = safeData.escaped_targets_count || 0;
        const previousEscapedCount = this.simulation?.escaped_targets_count || 0;
        const newEscapes = escapedCount > previousEscapedCount;
        
        // 使用防抖更新数据
        this.updateSimulationDataDebounced(safeData);
        
        // 处理目标捕获/逃脱提示
        if (newCaptures) {
          const newlyCaptured = capturedCount - previousCapturedCount;
          this.$toast.success(`成功捕获${newlyCaptured}个目标！`);
        }
        
        if (newEscapes) {
          const newlyEscaped = escapedCount - previousEscapedCount;
          this.$toast.warning(`${newlyEscaped}个目标成功逃脱！`);
        }
        
        // 显示部分完成状态
        const totalTargets = safeData.total_targets_count || 
                            (capturedCount + escapedCount + (safeData.targets ? safeData.targets.length : 0));
        
        if ((capturedCount > 0 || escapedCount > 0) && 
            safeData.targets && safeData.targets.length > 0 && 
            !this.partialCaptureNotified) {
          this.$toast.info(`已处理${capturedCount + escapedCount}/${totalTargets}个目标`);
          this.partialCaptureNotified = true;
        }
        
        // 如果模拟刚完成，处理完成状态
        if ((allCaptured && !this.isCaptured) || (allEscaped && !this.isEscaped)) {
          console.log('模拟刚刚完成，关闭连接并最终更新');
          
          this.isCaptured = allCaptured;
          this.isEscaped = allEscaped;
          this.isRunning = false;
          
          // 更新Vuex Store
          this.$store.dispatch('updateSimulationStatus', {
            simulationId: this.simulationId,
            isRunning: false,
            isCaptured: allCaptured,
            isEscaped: allEscaped
          });
          
          // 显示完成消息
          if (allCaptured) {
            this.$toast.success(`模拟完成：成功捕获所有${capturedCount}个目标!`);
          } else if (allEscaped) {
            this.$toast.warning(`模拟完成：所有${escapedCount}个目标成功逃脱!`);
          }
          
          // 关闭WebSocket连接
          this.closeWebSocketConnection();
          
          // 通知Canvas最终渲染
          if (this.$refs.canvas) {
            this.$refs.canvas.needsRender = true;
          }
          
          return;
        }
        
        // 如果运行状态改变但非完成，更新状态
        if (this.isRunning !== safeData.is_running) {
          this.isRunning = safeData.is_running;
          
          // 更新Store
          this.$store.dispatch('updateSimulationProperty', {
            simulationId: this.simulationId,
            property: 'is_running',
            value: safeData.is_running
          });
          
          // 如果模拟停止但未完成，提示用户
          if (!this.isRunning && !this.isCaptured && !this.isEscaped) {
            this.$toast.info('模拟已停止');
            this.closeWebSocketConnection();
          }
        }
      } catch (error) {
        // 捕获所有可能的异常，防止中断WebSocket连接
        console.error('处理WebSocket消息时出错:', error);
        console.error('错误详情:', error.stack);
        this.$toast.error('处理模拟数据时出错，请刷新页面重试');
        
        // 尝试继续保持连接
        // 不要在此处关闭WebSocket连接，让心跳机制决定是否需要重连
      }
    },
    
    // 计算WebSocket延迟
    calculateWsLatency() {
      const now = performance.now();
      if (this.lastMessageTime) {
        this.wsLatency = Math.round(now - this.lastMessageTime);
      }
      this.lastMessageTime = now;
    },
    
    // 防抖更新数据
    updateSimulationDataDebounced(data) {
      if (this.dataUpdateTimer) {
        clearTimeout(this.dataUpdateTimer);
      }
      
      this.dataUpdateTimer = setTimeout(() => {
        try {
          const startTime = performance.now();
          
          // 安全地更新模拟数据
          if (data) {
            this.simulation = { ...this.simulation, ...data };
            this.isRunning = !!data.is_running;
            this.isCaptured = !!data.is_captured;
            this.isEscaped = !!data.escaped;
          }
          
          // 计算渲染时间
          this.renderTime = Math.round(performance.now() - startTime);
        } catch (error) {
          console.error('更新模拟数据时出错:', error);
          // 继续正常运行，不中断模拟
        }
      }, 50);
    },
    
    // 模拟控制方法
    async startSimulation() {
      try {
        // 先关闭可能存在的旧连接
        console.log('启动模拟，关闭已有WebSocket连接');
        this.closeWebSocketConnection();
        
        // 添加短延迟确保连接完全关闭
        await new Promise(resolve => setTimeout(resolve, 200));
        
        // 重置部分捕获通知标志
        this.partialCaptureNotified = false;
        
        // 发送启动请求到API
        await this.$store.dispatch('startSimulation', this.simulationId);
        this.isRunning = true;
        
        // 重新建立WebSocket连接以接收实时更新
        console.log('模拟已启动，创建新WebSocket连接');
        this.setupWebSocketConnection();
        
        this.$toast.success('模拟已启动');
      } catch (error) {
        console.error('启动模拟失败:', error);
        this.$toast.error('启动模拟失败');
        this.isConnecting = false; // 确保重置连接状态
      }
    },
    
    async stopSimulation() {
      try {
        await this.$store.dispatch('stopSimulation', this.simulationId);
        this.isRunning = false;
        
        // 关闭WebSocket连接
        this.closeWebSocketConnection();
        
        this.$toast.success('模拟已停止');
      } catch (error) {
        console.error('停止模拟失败:', error);
        this.$toast.error('停止模拟失败');
      }
    },
    
    async resetSimulation() {
      try {
        // 关闭现有连接
        this.closeWebSocketConnection();
        
        // 重置状态
        this.isCaptured = false;
        this.isEscaped = false;
        this.partialCaptureNotified = false;
        
        const data = await this.$store.dispatch('resetSimulation', this.simulationId);
        this.simulation = data;
        this.isRunning = false;
        
        // 确保画布重绘
        this.$nextTick(() => {
          if (this.$refs.canvas) {
            this.$refs.canvas.drawSimulation(true);
          }
        });
        
        this.$toast.success('模拟已重置');
      } catch (error) {
        console.error('重置模拟失败:', error);
        this.$toast.error('重置模拟失败');
      }
    },
    
    async deleteSimulation() {
      this.deleteLoading = true;
      try {
        // 确保关闭WebSocket连接
        this.closeWebSocketConnection();
        
        await this.$store.dispatch('deleteSimulation', this.simulationId);
        this.$toast.success('模拟已删除');
        this.$router.push('/simulations');
      } catch (error) {
        console.error('删除模拟失败:', error);
        this.$toast.error('删除模拟失败');
      } finally {
        this.deleteLoading = false;
        this.showDeleteDialog = false;
      }
    },
    
    // 优化页面可见性变化处理
    handleVisibilityChange() {
      if (document.hidden) {
        // 页面隐藏时关闭WebSocket
        console.log('页面隐藏，关闭WebSocket连接');
        this.closeWebSocketConnection();
      } else {
        // 页面可见时，只在需要时重新连接
        if (this.isRunning && !this.isCaptured && !this.isEscaped && !this.socket && !this.isConnecting) {
          console.log('页面可见，模拟运行中，重新连接WebSocket');
          this.setupWebSocketConnection();
        }
      }
    },
    
    // 优化窗口焦点变化处理
    handleWindowFocus() {
      if (this.isRunning && !this.isCaptured && !this.isEscaped && !this.socket && !this.isConnecting) {
        console.log('窗口获得焦点，模拟运行中，重新连接WebSocket');
        this.setupWebSocketConnection();
      }
    },
    
    handleWindowBlur() {
      // 窗口失去焦点时无需处理
    },
    
    // 导航方法
    navigateToList() {
      // 清理资源后再导航
      this.closeWebSocketConnection();
      this.cleanupTimers();
      this.$router.push('/simulations');
    },
    
    // 状态提示显示方法
    showInfoStatus(message) {
      this.connectionStatusText = message;
      this.connectionStatusColor = 'info';
      this.showConnectionStatus = true;
    },
    
    showSuccessStatus(message) {
      this.connectionStatusText = message;
      this.connectionStatusColor = 'success';
      this.showConnectionStatus = true;
    },
    
    showWarningStatus(message) {
      this.connectionStatusText = message;
      this.connectionStatusColor = 'warning';
      this.showConnectionStatus = true;
    },
    
    showErrorStatus(message) {
      this.connectionStatusText = message;
      this.connectionStatusColor = 'error';
      this.showConnectionStatus = true;
    },
    
    // 错误处理
    handleApiError(error) {
      console.error('API错误:', error);
      
      // 特定错误处理
      if (error.status === 404 && error.message.includes('Simulation not found')) {
        this.$toast.error('模拟不存在或已被删除');
        this.$router.push('/simulations');
      }
    },
    
    // 清理定时器
    cleanupTimers() {
      if (this.dataUpdateTimer) {
        clearTimeout(this.dataUpdateTimer);
        this.dataUpdateTimer = null;
      }
    },

    // 环境设置方法
    toggleObstacles(show) {
      // 控制障碍物显示/隐藏
      if (this.$refs.canvas) {
        this.$refs.canvas.showObstacles = show;
        // 通知画布需要重绘
        this.$refs.canvas.needsRender = true;
      }
    },
    
    async regenerateObstacles(count) {
      try {
        // 显示加载状态
        this.$toast.info(`正在生成${count}个障碍物...`);
        console.log(`请求生成${count}个障碍物`);
        
        // 调用API
        const response = await this.axios.post(
          `/simulations/${this.simulationId}/regenerate-obstacles`, 
          { count: count },
          { headers: { 'Content-Type': 'application/json' } }
        );
        
        console.log('障碍物生成响应:', response);
        
        if (response.data && response.data.obstacles) {
          // 确保obstacles是数组格式
          const obstacles = Array.isArray(response.data.obstacles) 
            ? response.data.obstacles 
            : [];
            
          console.log(`收到${obstacles.length}个障碍物:`, obstacles);
          
          // 更新模拟对象中的障碍物
          this.simulation.obstacles = obstacles;
          
          // 更新障碍物计数器
          if (this.simulation.obstacle_count !== undefined) {
            this.simulation.obstacle_count = obstacles.length;
          }
          
          this.$toast.success(`成功生成${obstacles.length}个障碍物`);
          
          // 强制重绘画布
          this.$nextTick(() => {
            if (this.$refs.canvas) {
              console.log('更新画布组件的障碍物数据');
              
              // 确保显示开关打开
              if (Object.prototype.hasOwnProperty.call(this.$refs.canvas, 'showObstacles')) {
                this.$refs.canvas.showObstacles = true;
              }
              
              // 通知画布需要重绘
              this.$refs.canvas.needsRender = true;
              
              // 强制重绘
              this.$refs.canvas.drawSimulation(true);
              
              console.log('画布重绘完成');
            } else {
              console.warn('画布组件引用不可用');
            }
          });
          
          // 更新Vuex存储
          this.$store.commit('UPDATE_SIMULATION_PROPERTY', {
            simulationId: this.simulationId,
            property: 'obstacles',
            value: obstacles
          });
          this.$store.commit('UPDATE_SIMULATION_PROPERTY', {
            simulationId: this.simulationId,
            property: 'obstacle_count',
            value: obstacles.length
          });
        } else {
          throw new Error('响应中缺少障碍物数据');
        }
      } catch (error) {
        console.error('生成障碍物失败:', error);
        this.$toast.error('生成障碍物失败: ' + (error.message || '未知错误'));
      }
    },
  },
  watch: {
    simulationId: {
      handler(newId, oldId) {
        if (newId !== oldId) {
          console.log(`模拟ID变更: ${oldId} -> ${newId}`);
          // 重新初始化组件
          this.closeWebSocketConnection();
          this.cleanupTimers();
          this.initializeComponent();
        }
      },
      immediate: false
    },
    
    // 监视store中的当前模拟数据变化
    storeCurrentSimulation: {
      handler(newSimulation) {
        if (newSimulation && newSimulation.id === this.simulationId) {
          // 仅在首次加载或重要属性变化时更新本地数据
          if (!this.simulation.id || 
              newSimulation.is_running !== this.simulation.is_running ||
              newSimulation.is_captured !== this.simulation.is_captured ||
              newSimulation.escaped !== this.simulation.escaped) {
            this.simulation = newSimulation;
            this.isRunning = newSimulation.is_running;
            this.isCaptured = newSimulation.is_captured;
            this.isEscaped = newSimulation.escaped || false;
          }
        }
      },
      deep: true
    },
    
    // 监视运行状态
    isRunning: {
      handler(newVal, oldVal) {
        if (newVal === false && oldVal === true) {
          // 模拟停止时，确保WebSocket关闭
          this.closeWebSocketConnection();
        }
      }
    },
    
    // 监视捕获状态
    isCaptured: {
      handler(newVal) {
        if (newVal === true) {
          // 捕获成功时关闭WebSocket连接
          this.closeWebSocketConnection();
          
          // 通知画布需要最终渲染
          if (this.$refs.canvas && Object.prototype.hasOwnProperty.call(this.$refs.canvas, 'needsRender')) {
            this.$refs.canvas.needsRender = true;
          }
        }
      }
    },
    
    // 监视逃脱状态
    isEscaped: {
      handler(newVal) {
        if (newVal === true) {
          // 逃脱成功时关闭WebSocket连接
          this.closeWebSocketConnection();
          
          // 通知画布需要最终渲染
          if (this.$refs.canvas && Object.prototype.hasOwnProperty.call(this.$refs.canvas, 'needsRender')) {
            this.$refs.canvas.needsRender = true;
          }
        }
      }
    }
  }
}
</script>

<style scoped>
.simulation-detail {
  height: 100%;
  overflow-y: auto;
}

/* 控制内容区域的最大宽度和居中 */
.content-container {
  max-width: 1200px !important;
  margin: 0 auto !important;
  padding: 12px !important; /* 修改为四周都有padding */
}

.content-row {
  justify-content: center;
}

.simulation-canvas-card {
  height: calc(100vh - 100px);
  display: flex;
  flex-direction: column;
  margin-top: 16px; /* 添加顶部边距 */
}

.control-panel {
  height: auto;
}

/* 控制元素样式优化 */
:deep(.v-input--switch) {
  margin-top: 0;
}

:deep(.v-messages) {
  min-height: 0;
}

:deep(.v-card__title) {
  padding: 8px 12px;
}

:deep(.v-card__text) {
  padding: 8px 12px;
}

.title-section {
  padding: 8px 4px;
}

/* 响应式设计优化 */
@media (max-width: 960px) {
  .simulation-canvas-card {
    height: 60vh;
  }
}
</style>