<template>
  <div class="simulation-list">
    <v-container>
      <v-row>
        <v-col cols="12">
          <v-card>
            <v-card-title>
              模拟列表
              <v-spacer></v-spacer>
              <v-text-field
                v-model="search"
                append-icon="mdi-magnify"
                label="搜索"
                single-line
                hide-details
                class="ml-4"
              ></v-text-field>
            </v-card-title>
            
            <v-card-text class="pa-0">
              <v-data-table
                :headers="headers"
                :items="simulations"
                :search="search"
                :loading="loading"
                :items-per-page="10"
                :footer-props="{
                  'items-per-page-options': [5, 10, 20, -1],
                  'items-per-page-text': '每页显示'
                }"
                class="elevation-0"
              >
              <template v-slot:[`item.name`]="{ item }">
                  <router-link 
                    :to="{ name: 'SimulationDetail', params: { id: item.id }}"
                    class="text-decoration-none"
                  >
                    {{ item.name }}
                  </router-link>
                </template>
                
                <template v-slot:[`item.algorithm_type`]="{ item }">
                  <v-chip small>{{ formatAlgorithm(item.algorithm_type) }}</v-chip>
                </template>
                
                <template v-slot:[`item.is_captured`]="{ item }">
                  <v-chip
                    small
                    :color="item.is_captured ? 'success' : 'grey'"
                    text-color="white"
                  >
                    {{ item.is_captured ? '已捕获' : '未捕获' }}
                  </v-chip>
                </template>
                
                <template v-slot:[`item.created_at`]="{ item }">
                  {{ formatDate(item.created_at) }}
                </template>
                
                <template v-slot:[`item.actions`]="{ item }">
                  <v-btn 
                    icon
                    small
                    :to="{ name: 'SimulationDetail', params: { id: item.id }}"
                    class="mr-2"
                  >
                    <v-icon small>mdi-eye</v-icon>
                  </v-btn>
                  <v-btn 
                    icon
                    small
                    color="error"
                    @click.stop="confirmDelete(item)"
                  >
                    <v-icon small>mdi-delete</v-icon>
                  </v-btn>
                </template>
                
                <template v-slot:no-data>
                  <div class="pa-4 text-center">
                    <p>暂无模拟数据</p>
                    <v-btn color="primary" @click="$router.push('/simulations/create')">
                      <v-icon left>mdi-plus</v-icon> 创建模拟
                    </v-btn>
                  </div>
                </template>
              </v-data-table>
            </v-card-text>
          </v-card>
          
          <v-btn
            color="primary"
            fab
            large
            dark
            fixed
            bottom
            right
            class="mb-4 mr-4"
            @click="$router.push('/simulations/create')"
          >
            <v-icon>mdi-plus</v-icon>
          </v-btn>
        </v-col>
      </v-row>
    </v-container>

    <!-- 删除确认对话框 -->
    <v-dialog v-model="showDeleteDialog" max-width="400">
      <v-card>
        <v-card-title class="headline">确认删除?</v-card-title>
        <v-card-text>
          此操作将永久删除"{{ selectedSimulation ? selectedSimulation.name : '' }}"及其所有相关数据，无法恢复。
        </v-card-text>
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
export default {
  name: 'SimulationList',
  data() {
    return {
      loading: false,
      search: '',
      simulations: [],
      headers: [
        { text: '名称', value: 'name', sortable: true },
        { text: '算法', value: 'algorithm_type', sortable: true },
        { text: '猎手数量', value: 'num_hunters', sortable: true, align: 'center' },
        { text: '目标数量', value: 'num_targets', sortable: true, align: 'center' },
        { text: '步数', value: 'step_count', sortable: true, align: 'center' },
        { text: '状态', value: 'is_captured', sortable: true, align: 'center' },
        { text: '创建时间', value: 'created_at', sortable: true },
        { text: '操作', value: 'actions', sortable: false, align: 'center' }
      ],
      showDeleteDialog: false,
      selectedSimulation: null,
      deleteLoading: false
    }
  },
  async created() {
    await this.fetchSimulations()
  },
  methods: {
    async fetchSimulations() {
      this.loading = true
      
      try {
        const response = await this.axios.get('/simulations/')
        this.simulations = response.data
      } catch (error) {
        console.error('Failed to fetch simulations:', error)
        this.$toast.error('获取模拟列表失败')
      } finally {
        this.loading = false
      }
    },
    formatDate(dateString) {
      if (!dateString) return '未知'
      const date = new Date(dateString)
      return date.toLocaleString()
    },
    formatAlgorithm(algorithm) {
      const map = {
        'APF': '人工势场法',
        'CONSENSUS': '共识算法',
        'ROLE_BASED': '基于角色策略',
        'ENCIRCLEMENT': '包围策略'
      }
      return map[algorithm] || algorithm
    },
    // 显示删除确认对话框
    confirmDelete(simulation) {
      this.selectedSimulation = simulation;
      this.showDeleteDialog = true;
    },
    
    // 执行删除操作
    async deleteSimulation() {
      if (!this.selectedSimulation) return;
      
      this.deleteLoading = true;
      
      try {
        await this.axios.delete(`/simulations/${this.selectedSimulation.id}`);
        
        // 从本地列表中移除已删除的模拟
        this.simulations = this.simulations.filter(s => s.id !== this.selectedSimulation.id);
        
        this.$toast.success('模拟已成功删除');
        this.showDeleteDialog = false;
        this.selectedSimulation = null;
      } catch (error) {
        console.error('删除模拟失败:', error);
        this.$toast.error('删除模拟失败');
      } finally {
        this.deleteLoading = false;
      }
    }
  }
}
</script>

<style scoped>
.simulation-list {
  padding-top: 16px;
}
</style>