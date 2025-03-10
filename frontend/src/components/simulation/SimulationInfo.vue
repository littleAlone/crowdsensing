<template>
  <v-card class="simulation-info-card">
    <v-card-title class="info-title">模拟信息</v-card-title>
    <v-list dense class="info-list">
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">算法类型</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ formatAlgorithm(simulation.algorithm_type) }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">猎手数量</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ simulation.hunters ? simulation.hunters.length : 0 }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">目标数量</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ simulation.targets ? simulation.targets.length : 0 }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">环境大小</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ simulation.environment_size || 500 }} x {{ simulation.environment_size || 500 }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">当前步数</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ simulation.step_count || 0 }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item v-if="simulation.is_captured">
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">捕获时间</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ formatCaptureTime(simulation.capture_time) }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">创建时间</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ formatDate(simulation.created_at) }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      
      <v-list-item>
        <v-list-item-content>
          <v-list-item-subtitle class="info-subtitle">障碍物数量</v-list-item-subtitle>
          <v-list-item-title class="info-value">{{ getObstaclesCount() }}</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
    </v-list>
  </v-card>
</template>

<script>
export default {
  name: 'SimulationInfo',
  props: {
    simulation: {
      type: Object,
      required: true,
      default: () => ({})
    }
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return '未知';
      try {
        const date = new Date(dateString);
        // 检查日期是否有效
        if (isNaN(date.getTime())) return '未知';
        return date.toLocaleString();
      } catch (e) {
        console.error('日期格式化错误:', e, dateString);
        return '未知';
      }
    },
    
    formatAlgorithm(algorithm) {
      const map = {
        'APF': '人工势场法',
        'CONSENSUS': '共识算法',
        'ENCIRCLEMENT': '包围策略',
        'ROLE_BASED': '基于角色的策略'
      };
      return map[algorithm] || algorithm;
    },

    formatCaptureTime(timeInSeconds) {
      if (!timeInSeconds && timeInSeconds !== 0) return '未知';
      
      // 格式化时间为分钟:秒
      const minutes = Math.floor(timeInSeconds / 60);
      const seconds = Math.floor(timeInSeconds % 60);
      return `${minutes}分${seconds}秒`;
    },
    
    getObstaclesCount() {
      if (this.simulation.obstacles && Array.isArray(this.simulation.obstacles)) {
        return this.simulation.obstacles.length;
      } else {
        return 0;
      }
    }
  }
}
</script>

<style scoped>
.simulation-info-card {
  border-radius: 4px;
  margin-bottom: 8px;
}

.info-title {
  font-size: 0.9rem;
  padding: 8px 12px !important;
  min-height: 32px !important;
  background-color: #f5f5f5;
}

.info-list {
  padding: 0 !important;
}

.v-list-item {
  min-height: 28px !important;
  padding: 4px 12px !important;
}

.v-list-item__content {
  padding: 2px 0 !important;
}

.info-subtitle {
  font-size: 0.7rem !important;
  color: rgba(0, 0, 0, 0.6) !important;
}

.info-value {
  font-size: 0.8rem !important;
  line-height: 1.2 !important;
}

@media (max-height: 768px) {
  .v-list-item {
    min-height: 24px !important;
  }
  
  .info-value {
    font-size: 0.75rem !important;
  }
}
</style>