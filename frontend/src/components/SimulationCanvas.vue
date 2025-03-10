<template>
  <div class="simulation-canvas">
    <canvas 
      ref="canvas" 
      :width="canvasSize" 
      :height="canvasSize" 
      class="simulation-canvas__area"
    ></canvas>
    
    <!-- 捕获成功提示覆盖层 -->
    <div 
      v-if="isCaptured" 
      class="capture-overlay"
    >
      <div class="capture-message">
        <v-icon large color="success">mdi-check-circle</v-icon>
        <span>目标已捕获!</span>
      </div>
    </div>
    
    <!-- 逃脱成功提示覆盖层 -->
    <div 
      v-if="escaped" 
      class="escape-overlay"
    >
      <div class="escape-message">
        <v-icon large color="warning">mdi-run-fast</v-icon>
        <span>目标成功逃脱!</span>
      </div>
    </div>
  </div>
</template>
  
<script>
export default {
  name: 'SimulationCanvas',
  props: {
    hunters: {
      type: [Array, String],
      required: true,
      validator: function(value) {
        // 如果是字符串，尝试解析为JSON
        if (typeof value === 'string') {
          try {
            JSON.parse(value);
            return true;
          } catch(e) {
            console.error('Invalid JSON string for hunters prop:', e);
            return false;
          }
        }
        // 如果是数组，直接返回true
        return Array.isArray(value);
      }
    },
    targets: {
      type: [Array, String],
      required: true,
      validator: function(value) {
        // 如果是字符串，尝试解析为JSON
        if (typeof value === 'string') {
          try {
            JSON.parse(value);
            return true;
          } catch(e) {
            console.error('Invalid JSON string for targets prop:', e);
            return false;
          }
        }
        // 如果是数组，直接返回true
        return Array.isArray(value);
      }
    },
    environmentSize: {
      type: Number,
      default: 500
    },
    isRunning: {
      type: Boolean,
      default: false
    },
    isCaptured: {
      type: Boolean,
      default: false
    },
    escaped: {
      type: Boolean,
      default: false
    },
    showTrails: {
      type: Boolean,
      default: true
    },
    showVisionRange: {
      type: Boolean,
      default: false
    },
    showCommunicationRange: {
      type: Boolean,
      default: false
    },
    obstacles: {
      type: Array,
      default: () => [] // 确保默认为空数组
    }
  },
  data() {
    return {
      canvasSize: 600,
      canvas: null,
      ctx: null,
      scale: 1,
      colorMap: {
        hunter: '#3949AB', // 更深的蓝色
        target: '#e53935', // 更鲜艳的红色
        vision: 'rgba(57, 73, 171, 0.1)', // 半透明蓝色
        communication: 'rgba(57, 73, 171, 0.05)', // 更透明的蓝色
        trail: 'rgba(57, 73, 171, 0.4)', // 半透明蓝色
        captureRange: 'rgba(76, 175, 80, 0.4)', // 更明显的绿色
        captured: 'rgba(244, 67, 54, 0.25)', // 半透明红色
        obstacle: 'rgba(100, 100, 110, 0.8)' // 障碍物颜色
      },
      // 跟踪之前的位置，用于优化渲染
      previousPositions: {
        hunters: [],
        targets: []
      },
      // 本地obstacles引用，防止未定义错误
      localObstacles: Array.isArray(this.obstacles) ? [...this.obstacles] : [],
      showObstacles: true,  // 默认显示障碍物
      // 防抖渲染计时器
      renderTimer: null,
      // 帧率控制
      lastRenderTime: 0,
      targetFPS: 30,
      // 渲染计数，用于降低非必要渲染的频率
      renderCount: 0,
      // 动画相关
      animationFrameId: null,
      animationFrames: 0,
      pulseDirection: 1,
      pulseState: 0,
      floatOffset: 0,
      // 是否显示标签
      showLabels: false,
      // 记录前一次运行状态
      previousIsRunning: false,
      previousIsCaptured: false,
      previousEscaped: false,
      // 新增：需要重新渲染标志
      needsRender: false,
      // 最后一次渲染状态
      lastRenderState: {
        isCaptured: false,
        isEscaped: false
      },
      // 缓存数据
      huntersCache: null,
      targetsCache: null
    };
  },
  mounted() {
    this.initCanvas();
    // 初始化本地obstacles
    this.localObstacles = Array.isArray(this.obstacles) ? [...this.obstacles] : [];
    this.drawSimulation();
    
    // 添加窗口大小变化监听
    window.addEventListener('resize', this.handleResize);
    
    // 使用requestAnimationFrame实现高效渲染循环
    this.startRenderLoop();
  },
  beforeDestroy() {
    // 清理事件监听器
    window.removeEventListener('resize', this.handleResize);
    
    // 停止渲染循环
    this.stopRenderLoop();
    
    // 清理计时器
    if (this.renderTimer) {
      clearTimeout(this.renderTimer);
    }
    
    // 清理缓存
    this.huntersCache = null;
    this.targetsCache = null;
  },
  methods: {
    // 初始化画布
    initCanvas() {
      this.canvas = this.$refs.canvas;
      this.ctx = this.canvas.getContext('2d');
      this.scale = this.canvasSize / this.environmentSize;
      
      // 初始化previousPositions
      this.updatePreviousPositions();
    },
    
    // 处理窗口大小变化
    handleResize() {
      // 防抖处理
      if (this.renderTimer) {
        clearTimeout(this.renderTimer);
      }
      
      this.renderTimer = setTimeout(() => {
        // 重新计算画布大小（可选，如果需要响应式调整画布大小）
        // this.canvasSize = Math.min(window.innerWidth * 0.7, 600);
        this.scale = this.canvasSize / this.environmentSize;
        this.needsRender = true;
        this.drawSimulation(true); // 强制完全重绘
      }, 200);
    },
    
    // 启动渲染循环
    startRenderLoop() {
      if (!this.animationFrameId) {
        this.lastRenderTime = performance.now();
        this.animationFrameId = requestAnimationFrame(this.renderLoop);
      }
    },
    
    // 停止渲染循环
    stopRenderLoop() {
      if (this.animationFrameId) {
        cancelAnimationFrame(this.animationFrameId);
        this.animationFrameId = null;
      }
    },
    
    // 渲染循环
    renderLoop(timestamp) {
      try {
        // 判断模拟状态是否变化
        const stateChanged = this.isCaptured !== this.lastRenderState.isCaptured || 
                           this.escaped !== this.lastRenderState.isEscaped;
        
        // 如果模拟已结束且状态未变化，减少渲染频率
        if ((this.isCaptured || this.escaped) && !stateChanged && !this.needsRender) {
          // 模拟已结束，使用低频率更新
          setTimeout(() => {
            this.animationFrameId = requestAnimationFrame(this.renderLoop);
          }, 1000); // 降低为每秒一帧
          return;
        }
        
        // 更新最后渲染状态
        if (stateChanged) {
          this.lastRenderState.isCaptured = this.isCaptured;
          this.lastRenderState.isEscaped = this.escaped;
          this.needsRender = true;
        }
        
        // 正常渲染逻辑
        const elapsed = timestamp - this.lastRenderTime;
        const frameTime = 1000 / this.targetFPS;
        
        if (elapsed >= frameTime || this.needsRender) {
          this.lastRenderTime = timestamp;
          
          // 更新动画状态
          this.updateAnimationState();
          
          // 仅在需要时渲染
          if (this.needsRender || this.isRunning || this.animationFrames % 15 === 0) {
            this.drawOptimizedSimulation();
            this.needsRender = false;
          }
        }
        
        // 设置下一帧
        this.animationFrameId = requestAnimationFrame(this.renderLoop);
      } catch (error) {
        console.error('渲染循环错误:', error);
        // 错误恢复：停止当前循环，稍后重试
        if (this.animationFrameId) {
          cancelAnimationFrame(this.animationFrameId);
          this.animationFrameId = null;
        }
        
        // 延迟后尝试重启循环
        setTimeout(() => {
          this.startRenderLoop();
        }, 2000);
      }
    },
    
    // 更新动画状态
    updateAnimationState() {
      this.animationFrames++;
      if (this.animationFrames % 3 === 0) {
        // 更新脉冲效果
        this.pulseState += 0.05 * this.pulseDirection;
        if (this.pulseState >= 1) {
          this.pulseState = 1;
          this.pulseDirection = -1;
        } else if (this.pulseState <= 0) {
          this.pulseState = 0;
          this.pulseDirection = 1;
        }
        
        // 更新浮动效果
        this.floatOffset += 0.1;
      }
    },
    
    // 处理hunters数据
    ensureHuntersArray() {
      // 如果模拟已完成且有缓存，使用缓存
      if ((this.isCaptured || this.escaped) && this.huntersCache) {
        return this.huntersCache;
      }
      
      // 正常处理逻辑
      let result = [];
      if (typeof this.hunters === 'string') {
        try {
          result = JSON.parse(this.hunters);
        } catch (e) {
          console.error('无法解析hunters数据:', e);
        }
      } else if (Array.isArray(this.hunters)) {
        result = [...this.hunters]; // 创建浅拷贝以避免直接操作原始数据
      }
      
      // 如果模拟已完成，缓存结果
      if (this.isCaptured || this.escaped) {
        this.huntersCache = result;
      }
      
      return result;
    },
    
    // 处理targets数据
    ensureTargetsArray() {
      // 如果模拟已完成且有缓存，使用缓存
      if ((this.isCaptured || this.escaped) && this.targetsCache) {
        return this.targetsCache;
      }
      
      // 正常处理逻辑
      let result = [];
      if (typeof this.targets === 'string') {
        try {
          result = JSON.parse(this.targets);
        } catch (e) {
          console.error('无法解析targets数据:', e);
        }
      } else if (Array.isArray(this.targets)) {
        result = [...this.targets]; // 创建浅拷贝以避免直接操作原始数据
      }
      
      // 如果模拟已完成，缓存结果
      if (this.isCaptured || this.escaped) {
        this.targetsCache = result;
      }
      
      return result;
    },
    
    // 检查位置是否有变化
    hasPositionsChanged() {
      // 优化：快速检查数组长度变化
      if (this.hunters.length !== this.previousPositions.hunters.length ||
          this.targets.length !== this.previousPositions.targets.length) {
        return true;
      }
      
      // 检查运行状态变化
      if (this.isRunning !== this.previousIsRunning ||
          this.isCaptured !== this.previousIsCaptured ||
          this.escaped !== this.previousEscaped) {
        this.previousIsRunning = this.isRunning;
        this.previousIsCaptured = this.isCaptured;
        this.previousEscaped = this.escaped;
        return true;
      }
      
      // 渲染计数，每5帧强制完全重绘一次（避免累积误差）
      this.renderCount++;
      if (this.renderCount >= 5) {
        this.renderCount = 0;
        return true;
      }
      
      // 只有在运行中或首次渲染时，才进行位置变化检查
      if (!this.isRunning && this.previousPositions.hunters.length > 0) {
        return false;
      }
      
      // 智能体位置变化检测
      const threshold = 0.5; // 位置变化阈值
      
      // 确保数据格式正确
      const huntersArray = this.ensureHuntersArray();
      const targetsArray = this.ensureTargetsArray();
      
      // 检查猎手位置变化
      for (let i = 0; i < huntersArray.length; i++) {
        const hunter = huntersArray[i];
        const prevHunter = this.previousPositions.hunters[i];
        
        if (!prevHunter || !hunter) return true;
        if (!Array.isArray(hunter.position) || !Array.isArray(prevHunter.position)) return true;
        
        if (Math.abs(hunter.position[0] - prevHunter.position[0]) > threshold ||
            Math.abs(hunter.position[1] - prevHunter.position[1]) > threshold) {
          return true;
        }
      }
      
      // 检查目标位置变化
      for (let i = 0; i < targetsArray.length; i++) {
        const target = targetsArray[i];
        const prevTarget = this.previousPositions.targets[i];
        
        if (!prevTarget || !target) return true;
        if (!Array.isArray(target.position) || !Array.isArray(prevTarget.position)) return true;
        
        if (Math.abs(target.position[0] - prevTarget.position[0]) > threshold ||
            Math.abs(target.position[1] - prevTarget.position[1]) > threshold) {
          return true;
        }
      }
      
      return false;
    },
    
    // 更新之前的位置
    updatePreviousPositions() {
      // 确保数据格式正确
      const huntersArray = this.ensureHuntersArray();
      const targetsArray = this.ensureTargetsArray();
      
      // 深拷贝位置数据，确保防御性检查
      this.previousPositions.hunters = huntersArray.map(hunter => {
        if (hunter && Array.isArray(hunter.position)) {
          return {
            id: hunter.id,
            position: [...hunter.position]
          };
        }
        return { id: -1, position: [0, 0] }; // 默认值，防止错误
      });
      
      this.previousPositions.targets = targetsArray.map(target => {
        if (target && Array.isArray(target.position)) {
          return {
            id: target.id,
            position: [...target.position]
          };
        }
        return { id: -1, position: [0, 0] }; // 默认值，防止错误
      });
    },
    
    // 优化的绘制方法
    drawOptimizedSimulation() {
      if (!this.ctx) return;
      
      try {
        // 清除画布
        this.ctx.clearRect(0, 0, this.canvasSize, this.canvasSize);
        this.drawBackground();
        
        // 绘制环境边界
        this.ctx.strokeStyle = '#ccc';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(0, 0, this.canvasSize, this.canvasSize);
        
        // 绘制障碍物 - 只在必要时绘制
        if (this.obstacles && Array.isArray(this.obstacles) && this.obstacles.length > 0 && this.showObstacles) {
          this.drawObstacles();
        }
        
        // 绘制捕获或逃脱状态
        if (this.isCaptured) {
          this.ctx.fillStyle = this.colorMap.captured;
          this.ctx.fillRect(0, 0, this.canvasSize, this.canvasSize);
        } else if (this.escaped) {
          this.ctx.fillStyle = 'rgba(255, 248, 225, 0.5)'; // 逃脱背景色
          this.ctx.fillRect(0, 0, this.canvasSize, this.canvasSize);
        }
        
        // 绘制轨迹
        if (this.showTrails) {
          this.drawTrails();
        }
        
        // 绘制视野和通信范围
        if (this.showVisionRange || this.showCommunicationRange) {
          this.drawRanges();
        }
        
        // 获取处理后的数据
        const huntersArray = this.ensureHuntersArray();
        const targetsArray = this.ensureTargetsArray();
        
        // 使用安全的方式绘制猎手
        if (Array.isArray(huntersArray)) {
          for (let i = 0; i < huntersArray.length; i++) {
            const hunter = huntersArray[i];
            if (hunter && Array.isArray(hunter.position)) {
              this.drawAgent(hunter, 'hunter');
            }
          }
        }
        
        // 使用安全的方式绘制目标
        if (Array.isArray(targetsArray)) {
          for (let i = 0; i < targetsArray.length; i++) {
            const target = targetsArray[i];
            if (target && Array.isArray(target.position)) {
              this.drawAgent(target, 'target');
            }
          }
        }
        
        // 更新位置缓存，用于下次渲染比较
        if (!this.isCaptured && !this.escaped) {
          this.updatePreviousPositions();
        }
      } catch (error) {
        console.error('绘制模拟时出错:', error);
        // 不中断渲染循环
      }
    },
    
    // 绘制障碍物
    drawObstacles() {
      let obstaclesToRender = null;
      
      // 首先检查本地障碍物数组
      if (Array.isArray(this.localObstacles) && this.localObstacles.length > 0) {
        obstaclesToRender = this.localObstacles;
      } 
      // 然后检查props障碍物数组
      else if (Array.isArray(this.obstacles) && this.obstacles.length > 0) {
        obstaclesToRender = this.obstacles;
        // 同步更新本地数据
        this.localObstacles = [...this.obstacles];
      } 
      else {
        return;
      }

      // 遍历绘制每个障碍物
      for (let i = 0; i < obstaclesToRender.length; i++) {
        const obstacle = obstaclesToRender[i];
        
        // 检查障碍物数据完整性
        if (!obstacle) {
          continue;
        }

        // 确保position数据存在并格式正确
        let position = obstacle.position;
        if (!position) {
          continue;
        }

        // 处理position可能的不同格式
        let pos;
        try {
          if (Array.isArray(position)) {
            pos = this.transformPosition(position);
          } else if (typeof position === 'object') {
            // 对象格式 {x, y}
            if ('x' in position && 'y' in position) {
              pos = {
                x: position.x * this.scale,
                y: position.y * this.scale
              };
            } else {
              continue;
            }
          } else {
            continue;
          }
        } catch (e) {
          console.error(`处理障碍物[${i}]位置时出错:`, e);
          continue;
        }

        // 获取并检查半径
        const radius = obstacle.radius * this.scale;
        if (!radius || isNaN(radius) || radius <= 0) {
          continue;
        }

        // 绘制障碍物
        try {
          // 设置样式
          this.ctx.fillStyle = 'rgba(100, 100, 110, 0.8)';
          this.ctx.strokeStyle = 'rgba(80, 80, 90, 0.9)';
          this.ctx.lineWidth = 2;
          
          // 绘制圆形
          this.ctx.beginPath();
          this.ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
          this.ctx.fill();
          this.ctx.stroke();
          
          // 添加编号标签（便于调试）
          this.ctx.fillStyle = 'white';
          this.ctx.font = '12px Arial';
          this.ctx.textAlign = 'center';
          this.ctx.textBaseline = 'middle';
          this.ctx.fillText(`${i}`, pos.x, pos.y);
        } catch (e) {
          console.error(`绘制障碍物[${i}]时出错:`, e);
        }
      }
    },

    drawBackground() {
      const gridSize = 25 * this.scale;
      const width = this.canvasSize;
      const height = this.canvasSize;
      
      // 填充背景色
      this.ctx.fillStyle = '#f5f7fa';
      this.ctx.fillRect(0, 0, width, height);
      
      this.ctx.strokeStyle = 'rgba(200, 200, 220, 0.3)';
      this.ctx.lineWidth = 1;
      
      // 绘制网格线
      for (let x = 0; x <= width; x += gridSize) {
        this.ctx.beginPath();
        this.ctx.moveTo(x, 0);
        this.ctx.lineTo(x, height);
        this.ctx.stroke();
      }
      
      for (let y = 0; y <= height; y += gridSize) {
        this.ctx.beginPath();
        this.ctx.moveTo(0, y);
        this.ctx.lineTo(width, y);
        this.ctx.stroke();
      }
      
      // 添加坐标轴
      this.ctx.strokeStyle = 'rgba(150, 150, 180, 0.4)';
      this.ctx.lineWidth = 2;
      
      // x轴
      this.ctx.beginPath();
      this.ctx.moveTo(0, height/2);
      this.ctx.lineTo(width, height/2);
      this.ctx.stroke();
      
      // y轴
      this.ctx.beginPath();
      this.ctx.moveTo(width/2, 0);
      this.ctx.lineTo(width/2, height);
      this.ctx.stroke();
    },
    
    // 完整重绘方法
    drawSimulation(forceFullRedraw = false) {
      if (!this.ctx) return;
      
      // 如果不需要强制重绘，使用优化版本
      if (!forceFullRedraw && this.previousPositions.hunters.length > 0) {
        return this.drawOptimizedSimulation();
      }
      
      // 设置完全重绘所需的标记
      this.needsRender = true;
      
      // 清除画布
      this.ctx.clearRect(0, 0, this.canvasSize, this.canvasSize);

      this.drawBackground();
      
      // 绘制环境边界
      this.ctx.strokeStyle = '#ccc';
      this.ctx.lineWidth = 2;
      this.ctx.strokeRect(0, 0, this.canvasSize, this.canvasSize);
      
      // 绘制障碍物 - 添加防御性检查
      if (this.obstacles && Array.isArray(this.obstacles) && this.obstacles.length > 0 && this.showObstacles) {
        this.drawObstacles();
      }
      
      // 绘制捕获状态
      if (this.isCaptured) {
        this.ctx.fillStyle = this.colorMap.captured;
        this.ctx.fillRect(0, 0, this.canvasSize, this.canvasSize);
      }
      
      // 绘制逃脱状态
      if (this.escaped) {
        this.ctx.fillStyle = 'rgba(255, 248, 225, 0.5)'; // 逃脱背景色
        this.ctx.fillRect(0, 0, this.canvasSize, this.canvasSize);
      }
      
      // 绘制轨迹（如果启用）
      if (this.showTrails) {
        this.drawTrails();
      }
      
      // 绘制视野和通信范围（如果启用）
      if (this.showVisionRange || this.showCommunicationRange) {
        this.drawRanges();
      }
      
      // 获取处理后的数据
      const huntersArray = this.ensureHuntersArray();
      const targetsArray = this.ensureTargetsArray();
      
      // 使用安全的方式绘制猎手
      if (Array.isArray(huntersArray)) {
        for (let i = 0; i < huntersArray.length; i++) {
          const hunter = huntersArray[i];
          if (hunter && Array.isArray(hunter.position)) {
            this.drawAgent(hunter, 'hunter');
          }
        }
      }
      
      // 使用安全的方式绘制目标
      if (Array.isArray(targetsArray)) {
        for (let i = 0; i < targetsArray.length; i++) {
          const target = targetsArray[i];
          if (target && Array.isArray(target.position)) {
            this.drawAgent(target, 'target');
          }
        }
      }
      
      // 更新之前的位置
      this.updatePreviousPositions();
      this.previousIsRunning = this.isRunning;
      this.previousIsCaptured = this.isCaptured;
      this.previousEscaped = this.escaped;
    },
    
    // 单独绘制轨迹
    drawTrails() {
      // 获取处理后的数据
      const huntersArray = this.ensureHuntersArray();
      const targetsArray = this.ensureTargetsArray();
      
      // 绘制猎手轨迹
      for (let i = 0; i < huntersArray.length; i++) {
        const hunter = huntersArray[i];
        if (hunter && hunter.history && Array.isArray(hunter.history) && hunter.history.length > 1) {
          this.ctx.beginPath();
          const startPos = this.transformPosition(hunter.history[0]);
          this.ctx.moveTo(startPos.x, startPos.y);
          
          for (let j = 1; j < hunter.history.length; j++) {
            if (Array.isArray(hunter.history[j])) {
              const histPos = this.transformPosition(hunter.history[j]);
              this.ctx.lineTo(histPos.x, histPos.y);
            }
          }
          
          this.ctx.strokeStyle = this.colorMap.trail;
          this.ctx.lineWidth = 1.5;
          this.ctx.stroke();
        }
      }
      
      // 绘制目标轨迹
      for (let i = 0; i < targetsArray.length; i++) {
        const target = targetsArray[i];
        if (target && target.history && Array.isArray(target.history) && target.history.length > 1) {
          this.ctx.beginPath();
          const startPos = this.transformPosition(target.history[0]);
          this.ctx.moveTo(startPos.x, startPos.y);
          
          for (let j = 1; j < target.history.length; j++) {
            if (Array.isArray(target.history[j])) {
              const histPos = this.transformPosition(target.history[j]);
              this.ctx.lineTo(histPos.x, histPos.y);
            }
          }
          
          this.ctx.strokeStyle = this.colorMap.target;
          this.ctx.lineWidth = 1.5;
          this.ctx.stroke();
        }
      }
    },
    
    // 单独绘制视野和通信范围
    drawRanges() {
      // 获取处理后的数据
      const huntersArray = this.ensureHuntersArray();
      const targetsArray = this.ensureTargetsArray();
      
      // 绘制猎手视野和通信范围
      for (let i = 0; i < huntersArray.length; i++) {
        const hunter = huntersArray[i];
        if (!hunter || !Array.isArray(hunter.position)) continue;
        
        const pos = this.transformPosition(hunter.position);
        
        // 绘制视野范围
        if (this.showVisionRange && hunter.vision_range) {
          this.ctx.beginPath();
          this.ctx.arc(pos.x, pos.y, hunter.vision_range * this.scale, 0, Math.PI * 2);
          this.ctx.fillStyle = this.colorMap.vision;
          this.ctx.fill();
        }
        
        // 绘制通信范围
        if (this.showCommunicationRange && hunter.communication_range) {
          this.ctx.beginPath();
          this.ctx.arc(pos.x, pos.y, hunter.communication_range * this.scale, 0, Math.PI * 2);
          this.ctx.fillStyle = this.colorMap.communication;
          this.ctx.fill();
        }
        
        // 绘制捕获范围
        this.ctx.beginPath();
        this.ctx.arc(pos.x, pos.y, 10 * this.scale, 0, Math.PI * 2); // 捕获范围固定为10
        this.ctx.fillStyle = this.colorMap.captureRange;
        this.ctx.fill();
      }
      
      // 绘制目标视野范围
      for (let i = 0; i < targetsArray.length; i++) {
        const target = targetsArray[i];
        if (!target || !Array.isArray(target.position)) continue;
        
        if (this.showVisionRange && target.vision_range) {
          const pos = this.transformPosition(target.position);
          this.ctx.beginPath();
          this.ctx.arc(pos.x, pos.y, target.vision_range * this.scale, 0, Math.PI * 2);
          this.ctx.fillStyle = 'rgba(244, 67, 54, 0.1)'; // 半透明红色
          this.ctx.fill();
        }
      }
    },
    
    // 绘制智能体
    drawAgent(agent, type) {
      const pos = this.transformPosition(agent.position);
      
      // 目标的浮动动画
      let offsetY = 0;
      if (type === 'target') {
        offsetY = Math.sin(this.floatOffset) * 3; // 浮动效果
        this.drawCaptureRadius(pos, offsetY);
      }
      
      // 绘制智能体
      this.ctx.beginPath();
      const radius = type === 'hunter' ? 6 : 8; // 稍微增大智能体尺寸
      this.ctx.arc(pos.x, pos.y + offsetY, radius, 0, Math.PI * 2);
      this.ctx.fillStyle = this.colorMap[type];
      this.ctx.fill();
      
      // 添加发光效果
      this.ctx.shadowColor = type === 'hunter' ? 'rgba(63, 81, 181, 0.5)' : 'rgba(244, 67, 54, 0.5)';
      this.ctx.shadowBlur = 10;
      this.ctx.stroke();
      this.ctx.shadowBlur = 0; // 重置阴影效果
      
      // 绘制ID标签（可选，使UI更干净）
      if (this.showLabels) { // 使用配置选项
        this.ctx.font = '10px Arial';
        this.ctx.fillStyle = '#000';
        this.ctx.textAlign = 'center';
        this.ctx.fillText(agent.id.toString(), pos.x, pos.y + offsetY + (type === 'hunter' ? 15 : 20));
      }
    },
    
    // 新增方法：绘制目标捕获半径
    drawCaptureRadius(pos, offsetY) {
      const pulseScale = 1 + (this.pulseState * 0.15); // 脉冲效果，范围是1.0到1.15
      
      this.ctx.beginPath();
      this.ctx.arc(pos.x, pos.y + offsetY, 30 * pulseScale, 0, Math.PI * 2);
      this.ctx.strokeStyle = 'rgba(76, 175, 80, 0.6)';
      this.ctx.setLineDash([5, 3]); // 虚线效果
      this.ctx.lineWidth = 1.5;
      this.ctx.stroke();
      this.ctx.setLineDash([]); // 重置线型
    },
    
    // 转换坐标
    transformPosition(position) {
      // 检查position是否有效
      if (!Array.isArray(position) || position.length < 2) {
        console.warn('无效的position数据:', position);
        return { x: 0, y: 0 };
      }
      
      // 将模拟坐标转换为画布坐标
      return {
        x: position[0] * this.scale,
        y: position[1] * this.scale
      }
    },
    
    // 清除特定区域
    clearAgentArea(position, radius = 20) {
      const pos = this.transformPosition(position);
      this.ctx.clearRect(pos.x - radius, pos.y - radius, radius * 2, radius * 2);
    }
  },
  watch: {
    hunters: {
      handler() {
        // 设置需要渲染标记
        this.needsRender = true;
      },
      deep: true
    },
    targets: {
      handler() {
        // 设置需要渲染标记
        this.needsRender = true;
      },
      deep: true
    },
    obstacles: {
      handler(newObstacles) {
        if (Array.isArray(newObstacles)) {
          this.localObstacles = [...newObstacles];
          // 设置需要渲染标记
          this.needsRender = true;
        }
      },
      deep: true,
      immediate: true
    },
    isRunning(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.needsRender = true;
      }
    },
    isCaptured(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.needsRender = true;
        this.lastRenderState.isCaptured = newVal;
      }
    },
    escaped(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.needsRender = true;
        this.lastRenderState.isEscaped = newVal;
      }
    },
    showTrails(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.needsRender = true;
      }
    },
    showVisionRange(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.needsRender = true;
      }
    },
    showCommunicationRange(newVal, oldVal) {
      if (newVal !== oldVal) {
        this.needsRender = true;
      }
    },
    environmentSize() {
      this.scale = this.canvasSize / this.environmentSize;
      this.needsRender = true;
    }
  }
};
</script>

<style scoped>
.simulation-canvas {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  margin: 16px 0;
}

.simulation-canvas__area {
  border: none;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  background-color: #fcfcff;
}

.capture-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.7);
  border-radius: 8px;
  animation: fadeIn 0.5s ease-in-out;
}

.capture-message {
  background-color: rgba(255, 255, 255, 0.9);
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 1.5rem;
  font-weight: bold;
  color: #4caf50;
  animation: pulse 2s infinite;
}

.escape-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 248, 225, 0.7);
  border-radius: 8px;
  animation: fadeIn 0.5s ease-in-out;
}

.escape-message {
  background-color: rgba(255, 255, 255, 0.9);
  padding: 16px 24px;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  font-size: 1.5rem;
  font-weight: bold;
  color: #ff9800;
  animation: pulse 2s infinite;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes pulse {
  0% { transform: scale(1); }
  50% { transform: scale(1.05); }
  100% { transform: scale(1); }
}
</style>