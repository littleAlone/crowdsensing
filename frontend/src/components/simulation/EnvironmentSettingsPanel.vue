<template>
  <v-card class="environment-panel">
    <v-card-title class="panel-title">环境设置</v-card-title>
    <v-card-text>
      <v-row dense>
        <v-col cols="6">
          <v-text-field
            v-model.number="obstacleCount"
            label="障碍物数量"
            type="number"
            min="0"
            max="8"
            dense
            outlined
            hide-details
            :disabled="isRunning"
            @input="validateObstacleCount"
          ></v-text-field>
        </v-col>
        <v-col cols="6">
          <v-btn
            color="primary"
            small
            block
            :disabled="isRunning"
            @click="regenerateObstacles"
          >
            重新生成障碍物
          </v-btn>
        </v-col>
      </v-row>
      
      <v-divider class="my-3"></v-divider>
      
      <v-row dense>
        <v-col cols="12">
          <v-switch
            v-model="showObstacles"
            label="显示障碍物"
            dense
            hide-details
            class="mt-0"
          ></v-switch>
        </v-col>
      </v-row>
    </v-card-text>
  </v-card>
</template>

<script>
export default {
  name: 'EnvironmentSettingsPanel',
  props: {
    isRunning: {
      type: Boolean,
      default: false
    },
    currentObstacles: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      obstacleCount: 3,
      showObstacles: true
    }
  },
  watch: {
    currentObstacles: {
      handler(newObstacles) {
        if (newObstacles && newObstacles.length > 0) {
          this.obstacleCount = newObstacles.length;
        }
      },
      immediate: true
    },
    showObstacles(newValue) {
      this.$emit('toggle-obstacles', newValue);
    }
  },
  methods: {
    validateObstacleCount(value) {
      // 确保障碍物数量是一个有效的数字且在限制范围内
      let count = parseInt(value);
      if (isNaN(count) || count < 0) {
        this.obstacleCount = 0;
      } else if (count > 8) {
        this.obstacleCount = 8;
      } else {
        this.obstacleCount = count;
      }
    },
    regenerateObstacles() {
      console.log('发送重新生成障碍物请求，数量:', this.obstacleCount);
      this.$emit('regenerate-obstacles', this.obstacleCount);
    }
  }
}
</script>

<style scoped>
.environment-panel {
  margin-bottom: 8px;
  border-radius: 4px;
}

.panel-title {
  font-size: 0.9rem;
  padding: 8px 12px !important;
  min-height: 32px !important;
  background-color: #f5f5f5;
}
</style>