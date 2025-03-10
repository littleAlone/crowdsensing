// WebSocketManager.js
const setupWebSocket = (simulationId, options = {}) => {
  const {
    onOpen, 
    onMessage, 
    onClose, 
    onError, 
    onReconnect,
    retryAttempts = 5, 
    initialDelay = 1000
  } = options;
  
  // 创建WebSocket连接
  const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsBaseUrl = `${wsProtocol}//${window.location.hostname}:8000`;
  const wsUrl = `${wsBaseUrl}/api/v1/ws/simulations/${simulationId}`;
  
  console.log(`连接WebSocket: ${wsUrl} (simulationId: ${simulationId})`);
  
  let socket = null;
  try {
    socket = new WebSocket(wsUrl);
  } catch (error) {
    console.error('创建WebSocket连接失败:', error);
    if (onError) onError(error);
    return null;
  }
  
  // 重置连接状态
  let heartbeatInterval = null;
  let heartbeatTimeout = null;
  let reconnectAttempts = 0;
  let connectionEstablished = false;
  
  // 心跳检测
  const startHeartbeat = () => {
    heartbeatInterval = setInterval(() => {
      if (socket && socket.readyState === WebSocket.OPEN) {
        try {
          socket.send(JSON.stringify({ type: 'heartbeat' }));
          
          heartbeatTimeout = setTimeout(() => {
            console.warn('心跳超时，尝试重新连接...');
            cleanupAndReconnect();
          }, 5000);
        } catch (error) {
          console.error('发送心跳消息失败:', error);
          cleanupAndReconnect();
        }
      }
    }, 30000);
  };
  
  // 清理资源并重连
  const cleanupAndReconnect = () => {
    closeWebSocket(socket, heartbeatInterval, heartbeatTimeout);
    
    if (reconnectAttempts < retryAttempts) {
      reconnectAttempts++;
      const delay = Math.min(initialDelay * Math.pow(1.5, reconnectAttempts), 30000);
      console.log(`尝试重新连接WebSocket... (${reconnectAttempts}/${retryAttempts}) 延迟: ${delay}ms`);
      setTimeout(() => {
        const newSocket = setupWebSocket(simulationId, options);
        if (newSocket && typeof onReconnect === 'function') {
          onReconnect(newSocket);
        }
      }, delay);
    }
  };
  
  // 添加事件处理器
  socket.onopen = (event) => {
    console.log(`WebSocket连接已建立 (simulationId: ${simulationId})`);
    connectionEstablished = true;
    reconnectAttempts = 0;
    startHeartbeat();
    if (onOpen) onOpen(event);
  };
  
  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      
      // 如果是心跳响应，重置超时
      if (data.heartbeat && heartbeatTimeout) {
        clearTimeout(heartbeatTimeout);
      }
      
      // 检查错误消息
      if (data.error) {
        console.warn('WebSocket接收到错误消息:', data.error);
        if (typeof onError === 'function') {
          onError(new Error(data.error));
        }
        return;
      }
      
      // 数据完整性检查
      if (!data.hunters && !data.targets && !data.is_running === undefined) {
        console.warn('WebSocket接收到不完整的数据:', data);
        return; // 忽略不完整的数据而不是抛出错误
      }
      
      if (onMessage) onMessage(data, event);
    } catch (error) {
      console.error('解析WebSocket消息失败:', error);
      // 不要传播错误，只记录它
    }
  };
  
  socket.onclose = (event) => {
    // 正常关闭代码：1000（正常关闭）,1001（离开页面）,1005（无状态关闭）
    const normalCloseCodes = [1000, 1001, 1005];
    const wasEstablished = connectionEstablished;
    
    connectionEstablished = false;
    console.log(`WebSocket连接已关闭 (code: ${event.code}, reason: ${event.reason || '无原因'}, simulationId: ${simulationId})`);
    
    if (heartbeatInterval) {
      clearInterval(heartbeatInterval);
      heartbeatInterval = null;
    }
    
    if (heartbeatTimeout) {
      clearTimeout(heartbeatTimeout);
      heartbeatTimeout = null;
    }
    
    if (onClose) onClose(event);
    
    // 仅在连接曾经成功建立且非正常关闭时尝试重连
    // 添加延迟，避免过快重连
    if (wasEstablished && !normalCloseCodes.includes(event.code) && reconnectAttempts < retryAttempts) {
      const delay = Math.min(initialDelay * Math.pow(1.5, reconnectAttempts), 30000);
      console.log(`连接异常关闭，将在${delay}ms后尝试重新连接...`);
      
      setTimeout(() => {
        reconnectAttempts++;
        const newSocket = setupWebSocket(simulationId, options);
        if (newSocket && typeof onReconnect === 'function') {
          onReconnect(newSocket);
        }
      }, delay);
    }
  };
  
  socket.onerror = (error) => {
    console.error('WebSocket错误:', error);
    if (onError) onError(error);
  };
  
  return socket;
};

const closeWebSocket = (socket, heartbeatInterval = null, heartbeatTimeout = null) => {
  // 清理心跳
  if (heartbeatInterval) {
    clearInterval(heartbeatInterval);
  }
  
  if (heartbeatTimeout) {
    clearTimeout(heartbeatTimeout);
  }
  
  // 关闭连接
  if (socket) {
    try {
      console.log('正在关闭WebSocket连接...');
      if (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING) {
        socket.close(1000, "正常关闭");
      } else {
        console.log(`WebSocket连接已处于关闭状态 (readyState: ${socket.readyState})`);
      }
    } catch (error) {
      console.error('关闭WebSocket连接时出错:', error);
    } finally {
      // 清理事件处理器
      socket.onopen = null;
      socket.onmessage = null;
      socket.onclose = null;
      socket.onerror = null;
      console.log('WebSocket连接已关闭并清理事件处理器');
    }
  } else {
    console.log('没有活动的WebSocket连接需要关闭');
  }
};

export { setupWebSocket, closeWebSocket };