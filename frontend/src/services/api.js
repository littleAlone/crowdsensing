import axios from 'axios';
import Vue from 'vue';

// 创建事件总线用于广播错误
Vue.prototype.$eventBus = new Vue();

// 创建axios实例
const apiClient = axios.create({
  baseURL: process.env.VUE_APP_API_URL || 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
  },
  timeout: 15000 // 增加请求超时时间
});

// 请求拦截器
apiClient.interceptors.request.use(
  config => {
    // 添加请求标识符和时间戳
    config.metadata = {
      requestId: Math.random().toString(36).substring(2, 12),
      startTime: new Date().getTime()
    };
    
    // 在发送请求前做些什么
    return config;
  },
  error => {
    // 对请求错误做些什么
    console.error('Request error:', error);
    return Promise.reject(error);
  }
);

// 响应拦截器
apiClient.interceptors.response.use(
  response => {
    // 计算请求响应时间
    const requestTime = new Date().getTime() - response.config.metadata.startTime;
    console.debug(`Request ${response.config.metadata.requestId} completed in ${requestTime}ms`);
    
    // 对响应数据做点什么
    return response.data;
  },
  error => {
    // 对响应错误做点什么
    // 创建更详细的错误对象
    const errorResponse = {
      status: error.response?.status || 500,
      message: error.response?.data?.detail || '发生未预期的错误',
      originalError: error,
      requestId: error.config?.metadata?.requestId || 'unknown'
    };
    
    // 根据错误类型提供具体信息
    if (error.response) {
      // 服务器返回了错误状态码
      const status = error.response.status;
      if (status === 401) {
        errorResponse.type = 'auth';
        errorResponse.message = '未授权，请登录后重试';
      } else if (status === 403) {
        errorResponse.type = 'permission';
        errorResponse.message = '无权访问该资源';
      } else if (status === 404) {
        errorResponse.type = 'notFound';
        errorResponse.message = '请求的资源不存在';
      } else if (status === 500) {
        errorResponse.type = 'server';
        errorResponse.message = '服务器错误，请稍后重试';
      } else if (status === 503) {
        errorResponse.type = 'unavailable';
        errorResponse.message = '服务暂时不可用，请稍后重试';
      }
    } else if (error.request) {
      // 请求已发出，但没有收到响应
      errorResponse.type = 'network';
      errorResponse.message = '网络连接错误，请检查您的网络连接';
    } else {
      // 设置请求时发生错误
      errorResponse.type = 'request';
      errorResponse.message = '请求配置错误';
    }
    
    // 超时错误特殊处理
    if (error.code === 'ECONNABORTED') {
      errorResponse.type = 'timeout';
      errorResponse.message = '请求超时，请稍后重试';
    }
    
    // 记录错误并广播
    console.error('API Error:', errorResponse);
    Vue.prototype.$eventBus.emit('api-error', errorResponse);
    
    return Promise.reject(errorResponse);
  }
);

// 模拟相关API
const simulationApi = {
  // 获取所有模拟
  getAllSimulations() {
    return apiClient.get('/simulations/');
  },
  
  // 获取单个模拟详情
  getSimulation(id) {
    return apiClient.get(`/simulations/${id}`);
  },
  
  // 创建新模拟
  createSimulation(data) {
    return apiClient.post('/simulations/', data);
  },
  
  // 更新模拟
  updateSimulation(id, data) {
    return apiClient.put(`/simulations/${id}`, data);
  },
  
  // 删除模拟
  deleteSimulation(id) {
    return apiClient.delete(`/simulations/${id}`);
  },
  
  // 启动模拟
  startSimulation(id) {
    return apiClient.post(`/simulations/${id}/start`);
  },
  
  // 停止模拟
  stopSimulation(id) {
    return apiClient.post(`/simulations/${id}/stop`);
  },
  
  // 重置模拟
  resetSimulation(id) {
    return apiClient.post(`/simulations/${id}/reset`);
  },
  
  // 获取模拟快照
  getSimulationSnapshots(id) {
    return apiClient.get(`/simulations/${id}/snapshots`);
  }
};

// 添加重试机制的API工厂
const createRetryableApi = (api, maxRetries = 2) => {
  const retryableApi = {};
  
  // 遍历原始API的所有方法
  Object.keys(api).forEach(key => {
    const originalMethod = api[key];
    
    // 创建支持重试的方法
    retryableApi[key] = async (...args) => {
      let lastError;
      
      // 尝试执行，支持重试
      for (let attempt = 0; attempt <= maxRetries; attempt++) {
        try {
          // 如果不是第一次尝试，添加延迟
          if (attempt > 0) {
            // 指数退避策略: 500ms, 1500ms, 3500ms, ...
            const delay = Math.pow(2, attempt) * 500 - 500;
            await new Promise(resolve => setTimeout(resolve, delay));
            console.log(`Retry attempt ${attempt} for ${key}`);
          }
          
          return await originalMethod(...args);
        } catch (error) {
          lastError = error;
          
          // 只对某些错误类型进行重试
          const shouldRetry = error.type === 'network' || 
                              error.type === 'timeout' || 
                              error.status === 500 || 
                              error.status === 503;
                              
          // 如果不应该重试或已到最大重试次数，则抛出错误
          if (!shouldRetry || attempt === maxRetries) {
            throw error;
          }
        }
      }
      
      // 不应该到达这里，但以防万一
      throw lastError;
    };
  });
  
  return retryableApi;
};

// 创建带重试功能的API
const retryableSimulationApi = createRetryableApi(simulationApi);

export default {
  simulation: retryableSimulationApi
};