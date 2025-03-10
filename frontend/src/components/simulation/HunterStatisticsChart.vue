<template>
  <v-card class="hunter-chart-card">
    <v-card-title class="chart-title">猎手统计</v-card-title>
    <v-card-text class="chart-content">
      <div id="hunter-distance-chart" ref="chartContainer" class="chart-container">
        <div v-if="!chartInitialized || chartLoading" class="chart-placeholder">
          正在加载图表...
        </div>
      </div>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'HunterStatisticsChart',
  props: {
    hunters: {
      type: Array,
      default: () => []
    },
    targets: {
      type: Array,
      default: () => []
    },
    stepCount: {
      type: Number,
      default: 0
    },
    isRunning: {
      type: Boolean,
      default: false
    }
  },
  data() {
    return {
      chartInstance: null,
      chartInitialized: false,
      chartLoading: false,
      distanceChartSeries: [],
      agentDistances: {},
      maxDataPoints: 100,
      chartUpdateTimer: null,
      lastChartUpdate: 0,
      optimizeChartUpdates: true,
      colorPalette: ['#4285F4', '#34A853', '#EA4335', '#FBBC05'] // 谷歌色彩，更鲜明的对比
    }
  },
  mounted() {
    this.initChart();
    // 尝试从本地存储恢复数据
    try {
      const savedData = localStorage.getItem('simulation_final_data');
      if (savedData) {
        const parsedData = JSON.parse(savedData);
        // 如果是当前模拟且数据不超过1小时
        if (parsedData.simulationId == this.$route.params.id && 
            (new Date().getTime() - parsedData.timestamp < 3600000)) {
          this.distanceChartSeries = JSON.parse(parsedData.chartData);
          // 强制更新图表
          this.$nextTick(() => {
            if (this.chartInstance) {
              this.chartInstance.updateSeries(this.distanceChartSeries);
            }
          });
        }
      }
    } catch (e) {
      console.error('恢复图表数据失败:', e);
    }
  },
  beforeDestroy() {
    this.destroyChart();
  },
  methods: {
    initChart() {
      this.chartLoading = true;
      
      // 初始化数据系列
      if (this.hunters.length > 0) {
        this.distanceChartSeries = this.hunters.map((hunter, index) => ({
          name: `猎手 ${hunter.id}`,
          data: [],
          color: this.colorPalette[index % this.colorPalette.length]
        }));
        
        this.hunters.forEach(hunter => {
          this.agentDistances[hunter.id] = [];
        });
        
        this.$nextTick(() => {
          setTimeout(() => {
            this.createChartInstance();
          }, 300);
        });
      } else {
        this.chartLoading = false;
      }
    },
    
    createChartInstance() {
      try {
        // 确保没有现有图表实例
        this.destroyChart();
        
        // 确保容器存在
        const container = document.getElementById('hunter-distance-chart');
        if (!container) {
          console.error('找不到图表容器元素');
          return;
        }
        
        // 使用普通方式创建图表而不是Vue组件
        import('apexcharts').then(ApexCharts => {
          this.chartInstance = new ApexCharts.default(
            container,
            {
              chart: {
                type: 'line',
                height: 240, // 增加高度以提供更好的可视性
                animations: { enabled: false },
                toolbar: { show: true }, // 启用工具栏方便查看
                background: '#fff',
                fontFamily: 'Roboto, sans-serif',
                zoom: { enabled: true } // 启用缩放功能
              },
              xaxis: {
                type: 'numeric',
                title: { text: '步数', style: { fontSize: '12px', fontWeight: 600 } },
                labels: { 
                  formatter: (val) => Math.floor(val),
                  style: { fontSize: '11px' }
                },
                tickAmount: 5
              },
              yaxis: {
                title: { 
                  text: '与目标距离', 
                  style: { fontSize: '12px', fontWeight: 600 } 
                },
                min: 0, // 确保从0开始
                labels: { 
                  style: { fontSize: '11px' },
                  formatter: (val) => val.toFixed(1)
                },
                tickAmount: 5
              },
              colors: this.colorPalette,
              stroke: {
                width: 3, // 增加线宽
                curve: 'smooth', // 平滑曲线
                lineCap: 'round'
              },
              markers: { 
                size: 4, // 增加标记大小
                strokeWidth: 0,
                hover: { size: 6 }
              },
              tooltip: {
                x: { title: { formatter: () => '步数' } },
                y: { formatter: (val) => `${val.toFixed(2)} 单位` }
              },
              legend: {
                position: 'top',
                horizontalAlign: 'right',
                fontSize: '12px',
                fontWeight: 500,
                markers: { size: 8, strokeWidth: 0 }
              },
              grid: { 
                borderColor: '#e0e0e0',
                row: { colors: ['#f3f3f3', 'transparent'], opacity: 0.5 }
              },
              series: this.distanceChartSeries,
              noData: {
                text: '暂无数据',
                align: 'center',
                verticalAlign: 'middle',
                style: {
                  fontSize: '14px'
                }
              }
            }
          );
          
          this.chartInstance.render().then(() => {
            console.log('图表渲染成功');
            this.chartInitialized = true;
            this.chartLoading = false;
          }).catch(err => {
            console.error('图表渲染失败:', err);
            this.chartLoading = false;
          });
        }).catch(err => {
          console.error('加载ApexCharts库失败:', err);
          this.chartLoading = false;
        });
      } catch (error) {
        console.error('创建图表实例失败:', error);
        this.chartLoading = false;
      }
    },
    
    destroyChart() {
      if (this.chartInstance) {
        try {
          this.chartInstance.destroy();
          this.chartInstance = null;
        } catch (e) {
          console.error('销毁图表实例失败:', e);
        }
      }
      
      if (this.chartUpdateTimer) {
        clearTimeout(this.chartUpdateTimer);
        this.chartUpdateTimer = null;
      }
    },
    
    updateChart() {
      const now = performance.now();
      const timeSinceLastUpdate = now - this.lastChartUpdate;
      
      // 如果数据是实时的并且距离上次更新不到200ms，延迟更新
      if (this.optimizeChartUpdates && this.isRunning && timeSinceLastUpdate < 200) {
        if (!this.chartUpdateTimer) {
          this.chartUpdateTimer = setTimeout(() => {
            this.updateChartData();
            this.chartUpdateTimer = null;
            this.lastChartUpdate = performance.now();
          }, 200 - timeSinceLastUpdate);
        }
      } else {
        // 直接更新
        if (this.chartUpdateTimer) {
          clearTimeout(this.chartUpdateTimer);
          this.chartUpdateTimer = null;
        }
        this.updateChartData();
        this.lastChartUpdate = now;
      }
      // 添加特殊处理：即使在模拟停止后也要确保最后一次数据更新
      if (this.isCaptured || !this.isRunning) {
        // 确保捕获后或停止后的最后一次数据更新
        this.updateChartData();
        
        // 存储最终状态到本地存储，以便在页面刷新或重新进入时恢复
        const finalData = {
          simulationId: this.$route.params.id,
          chartData: JSON.stringify(this.distanceChartSeries),
          stepCount: this.stepCount,
          timestamp: new Date().getTime()
        };
        localStorage.setItem('simulation_final_data', JSON.stringify(finalData));
      }
    },
    
    updateChartData() {
      try {
        if (!this.chartInitialized || !this.chartInstance || 
            !this.hunters.length || !this.targets.length) {
          return;
        }
        
        const target = this.targets[0];
        if (!target || !target.position) return;
        
        // 更新数据
        let dataUpdated = false;
        
        this.hunters.forEach((hunter, index) => {
          // 确保猎手数据有效
          if (!hunter || !hunter.position) return;
          
          // 计算与目标的距离
          const distance = this.calculateDistance(hunter.position, target.position);
          
          if (!this.agentDistances[hunter.id]) {
            this.agentDistances[hunter.id] = [];
          }
          
          // 添加数据点
          this.agentDistances[hunter.id].push({
            x: this.stepCount,
            y: Math.round(distance * 100) / 100
          });
          
          // 限制数据点数量，保留首尾点以保持图表连续性
          if (this.agentDistances[hunter.id].length > this.maxDataPoints) {
            const firstPoint = this.agentDistances[hunter.id][0];
            const lastPoints = this.agentDistances[hunter.id].slice(-this.maxDataPoints + 1);
            this.agentDistances[hunter.id] = [firstPoint, ...lastPoints];
          }
          
          // 更新系列数据
          if (index < this.distanceChartSeries.length) {
            this.distanceChartSeries[index].data = [...this.agentDistances[hunter.id]];
            dataUpdated = true;
          }
        });
        
        // 仅当数据更新时才更新图表
        if (dataUpdated && this.chartInstance) {
          this.chartInstance.updateSeries(this.distanceChartSeries);
          
          // 根据当前数据动态调整Y轴范围
          this.optimizeYAxisRange();
        }
      } catch (error) {
        console.error('更新图表数据失败:', error);
      }
    },

    // 新增：优化Y轴范围方法
    optimizeYAxisRange() {
      const allDistances = this.distanceChartSeries.flatMap(series => 
        series.data.map(point => point.y)
      );
      
      if (allDistances.length > 0) {
        const maxDistance = Math.max(...allDistances);
        const minDistance = Math.min(...allDistances);
        const range = maxDistance - minDistance;
        
        // 只有当范围足够小时才调整Y轴，避免频繁变化
        if (range < maxDistance * 0.5) {
          const padding = range * 0.2; // 20%的上下边距
          this.chartInstance.updateOptions({
            yaxis: {
              min: Math.max(0, minDistance - padding),
              max: maxDistance + padding,
              labels: { 
                formatter: (val) => val.toFixed(1)
              }
            }
          }, false, true);
        }
      }
    },
    
    calculateDistance(pos1, pos2) {
      return Math.sqrt(
        Math.pow(pos1[0] - pos2[0], 2) + 
        Math.pow(pos1[1] - pos2[1], 2)
      );
    }
  },
  watch: {
    hunters: {
      handler(newHunters) {
        if (!this.chartInitialized && newHunters.length > 0) {
          this.initChart();
        } else if (this.chartInitialized && this.chartInstance) {
          this.updateChart();
        }
      },
      deep: true
    },
    
    targets: {
      handler() {
        if (this.chartInitialized && this.chartInstance) {
          this.updateChart();
        }
      },
      deep: true
    },
    
    stepCount: {
      handler() {
        if (this.chartInitialized && this.chartInstance) {
          this.updateChart();
        }
      }
    }
  }
}
</script>

<style scoped>
.hunter-chart-card {
  margin-bottom: 8px;
  border-radius: 4px;
}

.chart-title {
  font-size: 1rem;
  padding: 8px 12px !important;
  min-height: 32px !important;
  background-color: #f5f5f5;
}

.chart-content {
  padding: 8px !important;
}

.chart-container {
  width: 100%;
  height: 240px;
  position: relative;
  background-color: #fff;
  border-radius: 4px;
  box-shadow: 0 0 2px rgba(0,0,0,0.1) inset;
}

.chart-placeholder {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
  font-size: 0.9rem;
  background-color: rgba(249, 249, 249, 0.7);
  z-index: 1;
}
</style>