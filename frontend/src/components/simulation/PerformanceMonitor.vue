<template>
  <v-card class="performance-card">
    <v-card-title class="performance-title">性能监控</v-card-title>
    <v-card-text class="performance-content">
      <v-row>
        <v-col cols="6">
          <div class="perf-label">渲染时间</div>
          <div class="perf-value">{{ renderTime }} ms</div>
        </v-col>
        <v-col cols="6">
          <div class="perf-label">WebSocket延迟</div>
          <div class="perf-value">{{ wsLatency }} ms</div>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'PerformanceMonitor',
  props: {
    renderTime: {
      type: Number,
      default: 0
    },
    wsLatency: {
      type: Number,
      default: 0
    }
  }
}
</script>

<style scoped>
.performance-card {
  border-radius: 4px;
  margin-bottom: 8px;
}

.performance-title {
  font-size: 0.9rem;
  padding: 4px 12px !important;
  min-height: 32px !important;
}

.performance-content {
  padding: 4px 12px 8px !important;
}

.perf-label {
  font-size: 0.75rem;
  font-weight: 500;
  color: rgba(0, 0, 0, 0.6);
}

.perf-value {
  font-size: 0.8rem;
}

.v-row, .v-col {
  padding: 0 !important;
  margin: 0 !important;
}

@media (max-height: 768px) {
  .performance-title {
    padding: 2px 12px !important;
    min-height: 28px !important;
  }
  
  .performance-content {
    padding: 2px 12px 6px !important;
  }
  
  .perf-label {
    font-size: 0.7rem;
  }
  
  .perf-value {
    font-size: 0.75rem;
  }
}
</style>