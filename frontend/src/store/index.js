import Vue from 'vue'
import Vuex from 'vuex'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    simulations: [],
    currentSimulation: null,
    loading: false,
    error: null,
    simulationAgents: {}, // 新增：分离智能体状态存储
  },
  mutations: {
    SET_SIMULATIONS(state, simulations) {
      state.simulations = simulations;
    },
    SET_CURRENT_SIMULATION(state, simulation) {
      state.currentSimulation = simulation;
      
      // 同时更新智能体状态
      if (simulation && simulation.id) {
        state.simulationAgents[simulation.id] = {
          hunters: simulation.hunters || [],
          targets: simulation.targets || []
        };
      }
    },
    UPDATE_SIMULATION(state, simulation) {
      // 更新列表中的模拟
      const index = state.simulations.findIndex(s => s.id === simulation.id);
      if (index !== -1) {
        // 创建新对象进行更新（更好的响应式性能）
        state.simulations = [
          ...state.simulations.slice(0, index),
          simulation,
          ...state.simulations.slice(index + 1)
        ];
      }
      
      // 更新当前模拟
      if (state.currentSimulation && state.currentSimulation.id === simulation.id) {
        state.currentSimulation = {...simulation};
      }
    },
    UPDATE_SIMULATION_STATUS(state, { simulationId, isRunning, isCaptured, isEscaped }) {
      // 更新列表中的模拟
      const index = state.simulations.findIndex(s => s.id === simulationId);
      if (index !== -1) {
        // 创建新对象更新状态
        const updatedSimulation = {
          ...state.simulations[index],
          is_running: isRunning,
          is_captured: isCaptured,
          escaped: isEscaped
        };
        
        state.simulations = [
          ...state.simulations.slice(0, index),
          updatedSimulation,
          ...state.simulations.slice(index + 1)
        ];
      }
      
      // 更新当前模拟
      if (state.currentSimulation && state.currentSimulation.id === simulationId) {
        state.currentSimulation = {
          ...state.currentSimulation,
          is_running: isRunning,
          is_captured: isCaptured,
          escaped: isEscaped
        };
      }
    },    
    // 新增：只更新智能体状态，避免不必要的完整更新
    UPDATE_SIMULATION_AGENTS(state, { simulationId, hunters, targets }) {
      if (state.simulationAgents[simulationId]) {
        state.simulationAgents[simulationId] = {
          hunters: [...hunters],
          targets: [...targets]
        };
        
        // 如果是当前模拟，同步更新currentSimulation
        if (state.currentSimulation && state.currentSimulation.id === simulationId) {
          state.currentSimulation = {
            ...state.currentSimulation,
            hunters: [...hunters],
            targets: [...targets]
          };
        }
      }
    },
    // 更新模拟的单个属性
    UPDATE_SIMULATION_PROPERTY(state, { simulationId, property, value }) {
      // 更新列表中的模拟
      const index = state.simulations.findIndex(s => s.id === simulationId);
      if (index !== -1) {
        const updatedSimulation = {
          ...state.simulations[index],
          [property]: value
        };
        
        state.simulations = [
          ...state.simulations.slice(0, index),
          updatedSimulation,
          ...state.simulations.slice(index + 1)
        ];
      }
      
      // 更新当前模拟
      if (state.currentSimulation && state.currentSimulation.id === simulationId) {
        state.currentSimulation = {
          ...state.currentSimulation,
          [property]: value
        };
      }
    },
    ADD_SIMULATION(state, simulation) {
      state.simulations = [...state.simulations, simulation];
      
      // 初始化智能体状态
      if (simulation && simulation.id) {
        state.simulationAgents[simulation.id] = {
          hunters: simulation.hunters || [],
          targets: simulation.targets || []
        };
      }
    },
    REMOVE_SIMULATION(state, id) {
      state.simulations = state.simulations.filter(s => s.id !== id);
      
      if (state.currentSimulation && state.currentSimulation.id === id) {
        state.currentSimulation = null;
      }
      
      // 清理智能体状态
      if (state.simulationAgents[id]) {
        Vue.delete(state.simulationAgents, id);
      }
    },
    SET_LOADING(state, loading) {
      state.loading = loading;
    },
    SET_ERROR(state, error) {
      state.error = error;
    }
  },
  actions: {
    async fetchSimulations({ commit }) {
      commit('SET_LOADING', true);
      try {
        const response = await Vue.axios.get('/simulations/');
        commit('SET_SIMULATIONS', response.data);
        commit('SET_ERROR', null);
        return response.data;
      } catch (error) {
        console.error('Error fetching simulations:', error);
        commit('SET_ERROR', '获取模拟列表失败');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async fetchSimulation({ commit }, id) {
      commit('SET_LOADING', true);
      try {
        const response = await Vue.axios.get(`/simulations/${id}`);
        
        // 确保时间戳字段存在且格式正确
        const simulation = response.data;
        
        // 如果创建时间为null或undefined，使用当前时间
        if (!simulation.created_at) {
          simulation.created_at = new Date().toISOString();
          // 可选：尝试更新数据库中的记录
          try {
            await Vue.axios.put(`/simulations/${id}/update-timestamp`, { 
              created_at: simulation.created_at 
            });
          } catch (updateError) {
            console.warn('更新时间戳失败，使用本地时间:', updateError);
          }
        }
        
        commit('SET_CURRENT_SIMULATION', simulation);
        commit('SET_ERROR', null);
        return simulation;
      } catch (error) {
        console.error(`获取模拟详情失败(ID: ${id}):`, error);
        commit('SET_ERROR', `获取模拟详情失败`);
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async updateSimulationStatus({ commit }, { simulationId, isRunning, isCaptured, isEscaped }) {
      commit('UPDATE_SIMULATION_STATUS', { simulationId, isRunning, isCaptured, isEscaped });
    },
    async createSimulation({ commit }, simulation) {
      commit('SET_LOADING', true);
      try {
        const response = await Vue.axios.post('/simulations/', simulation);
        commit('ADD_SIMULATION', response.data);
        commit('SET_ERROR', null);
        return response.data;
      } catch (error) {
        console.error('Error creating simulation:', error);
        commit('SET_ERROR', '创建模拟失败');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async startSimulation({ commit }, id) {
      commit('SET_LOADING', true);
      try {
        const response = await Vue.axios.post(`/simulations/${id}/start`);
        // 更新模拟状态为运行中
        commit('UPDATE_SIMULATION_PROPERTY', { 
          simulationId: id, 
          property: 'is_running', 
          value: true 
        });
        commit('SET_ERROR', null);
        return response;
      } catch (error) {
        console.error(`Error starting simulation ${id}:`, error);
        commit('SET_ERROR', '启动模拟失败');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async stopSimulation({ commit }, id) {
      commit('SET_LOADING', true);
      try {
        const response = await Vue.axios.post(`/simulations/${id}/stop`);
        // 更新模拟状态为停止
        commit('UPDATE_SIMULATION_PROPERTY', { 
          simulationId: id, 
          property: 'is_running', 
          value: false 
        });
        commit('SET_ERROR', null);
        return response;
      } catch (error) {
        console.error(`Error stopping simulation ${id}:`, error);
        commit('SET_ERROR', '停止模拟失败');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async resetSimulation({ commit }, id) {
      commit('SET_LOADING', true);
      try {
        await Vue.axios.post(`/simulations/${id}/reset`);
        // 重新获取模拟数据
        const response = await Vue.axios.get(`/simulations/${id}`);
        commit('UPDATE_SIMULATION', response.data);
        commit('SET_ERROR', null);
        return response.data;
      } catch (error) {
        console.error(`Error resetting simulation ${id}:`, error);
        commit('SET_ERROR', '重置模拟失败');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    async deleteSimulation({ commit }, id) {
      commit('SET_LOADING', true);
      try {
        await Vue.axios.delete(`/simulations/${id}`);
        commit('REMOVE_SIMULATION', id);
        commit('SET_ERROR', null);
      } catch (error) {
        console.error(`Error deleting simulation ${id}:`, error);
        commit('SET_ERROR', '删除模拟失败');
        throw error;
      } finally {
        commit('SET_LOADING', false);
      }
    },
    // 高效更新智能体状态
    updateSimulationAgents({ commit }, { simulationId, hunters, targets }) {
      commit('UPDATE_SIMULATION_AGENTS', { simulationId, hunters, targets });
    },
    // 高效更新模拟属性
    updateSimulationProperty({ commit }, { simulationId, property, value }) {
      commit('UPDATE_SIMULATION_PROPERTY', { simulationId, property, value });
    }
  },
  getters: {
    getSimulationById: (state) => (id) => {
      return state.simulations.find(s => s.id === id);
    },
    getSimulationAgents: (state) => (id) => {
      return state.simulationAgents[id] || { hunters: [], targets: [] };
    },
    getCapturingTime: (state) => {
      if (state.currentSimulation && state.currentSimulation.capture_time) {
        return state.currentSimulation.capture_time;
      }
      return null;
    },
    // 计算智能体与目标的距离
    getAgentDistances: (state) => (simulationId) => {
      const agents = state.simulationAgents[simulationId];
      if (!agents || !agents.hunters.length || !agents.targets.length) {
        return {};
      }
      
      const target = agents.targets[0]; // 假设单目标
      const distances = {};
      
      agents.hunters.forEach(hunter => {
        const hunterPos = hunter.position;
        const targetPos = target.position;
        const distance = Math.sqrt(
          Math.pow(hunterPos[0] - targetPos[0], 2) + 
          Math.pow(hunterPos[1] - targetPos[1], 2)
        );
        distances[hunter.id] = Math.round(distance * 100) / 100;
      });
      
      return distances;
    }
  }
})