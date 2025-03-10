<template>
  <div class="simulation-create">
    <v-container>
      <v-row>
        <v-col cols="12" md="8" offset-md="2">
          <v-card>
            <v-card-title class="headline">创建新模拟</v-card-title>
            
            <v-card-text>
              <v-form ref="form" v-model="valid" lazy-validation>
                <v-text-field
                  v-model="simulation.name"
                  label="模拟名称"
                  required
                  :rules="[v => !!v || '名称不能为空']"
                ></v-text-field>
                
                <v-textarea
                  v-model="simulation.description"
                  label="模拟描述"
                  rows="3"
                ></v-textarea>
                
                <v-select
                  v-model="simulation.algorithm_type"
                  :items="algorithmOptions"
                  label="算法类型"
                  required
                  :rules="[v => !!v || '请选择算法类型']"
                ></v-select>
                
                <v-slider
                  v-model="simulation.environment_size"
                  label="环境大小"
                  min="200"
                  max="1000"
                  step="50"
                  thumb-label="always"
                  class="mt-4"
                ></v-slider>
                
                <v-slider
                  v-model="simulation.num_hunters"
                  label="猎手数量"
                  min="1"
                  max="10"
                  step="1"
                  thumb-label="always"
                  class="mt-4"
                ></v-slider>
                
                <v-slider
                  v-model="simulation.num_targets"
                  label="目标数量"
                  min="1"
                  max="3"
                  step="1"
                  thumb-label="always"
                  class="mt-4"
                ></v-slider>
                
                <v-slider
                  v-model="simulation.max_steps"
                  label="最大步数"
                  min="500"
                  max="5000"
                  step="500"
                  thumb-label="always"
                  class="mt-4"
                ></v-slider>
              </v-form>
            </v-card-text>
            
            <v-card-actions>
              <v-btn text color="primary" @click="$router.push('/simulations')">
                <v-icon left>mdi-arrow-left</v-icon> 返回列表
              </v-btn>
              <v-spacer></v-spacer>
              <v-btn text @click="resetForm">
                <v-icon left>mdi-refresh</v-icon> 重置
              </v-btn>
              <v-btn color="primary" :disabled="!valid" :loading="loading" @click="createSimulation">
                <v-icon left>mdi-plus</v-icon> 创建
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
  name: 'SimulationCreate',
  data() {
    return {
      valid: true,
      loading: false,
      simulation: {
        name: '',
        description: '',
        environment_size: 500,
        num_hunters: 5,
        num_targets: 1,
        algorithm_type: 'APF',
        max_steps: 1000
      },
      algorithmOptions: [
      { text: '人工势场法 (APF)', value: 'APF' },
      { text: '共识算法 (CONSENSUS)', value: 'CONSENSUS' },
      { text: '包围策略 (ENCIRCLEMENT)', value: 'ENCIRCLEMENT' }
      ]
    }
  },
  methods: {
    resetForm() {
      this.$refs.form.reset()
      this.simulation = {
        name: '',
        description: '',
        environment_size: 500,
        num_hunters: 5,
        num_targets: 1,
        algorithm_type: 'APF',
        max_steps: 1000
      }
    },
    async createSimulation() {
      if (!this.$refs.form.validate()) return
      
      this.loading = true
      
      try {
        console.log('创建模拟:', this.simulation);
        
        // 使用正确的Axios引用方式
        const response = await this.axios.post('/simulations/', this.simulation);
        
        // 添加响应验证和调试
        console.log('API响应:', response);
        
        if (response && response.data) {
          this.$toast.success('模拟创建成功');
          
          // 确保ID存在且类型正确
          const simulationId = response.data.id;
          console.log('新创建的模拟ID:', simulationId);
          
          if (simulationId) {
            // 在Vuex中添加新模拟
            this.$store.commit('ADD_SIMULATION', response.data);
            
            // 添加短延迟确保状态更新
            setTimeout(() => {
              // 导航到模拟详情页
              this.$router.push(`/simulations/${simulationId}`);
            }, 100);
          } else {
            throw new Error('响应中缺少模拟ID');
          }
        } else {
          throw new Error('无效的服务器响应');
        }
      } catch (error) {
        console.error('创建模拟失败:', error);
        
        // 详细错误信息
        let errorMessage = '创建模拟失败';
        
        if (error.response) {
          // 服务器返回错误状态码
          errorMessage += `: 服务器错误 (${error.response.status})`;
          console.error('错误响应:', error.response);
        } else if (error.request) {
          // 请求发出但未收到响应
          errorMessage += ': 网络连接问题';
        } else {
          // 请求设置错误
          errorMessage += `: ${error.message}`;
        }
        
        this.$toast.error(errorMessage);
      } finally {
        this.loading = false;
      }
    }
  }
}
</script>

<style scoped>
.simulation-create {
  padding-top: 16px;
}
</style>