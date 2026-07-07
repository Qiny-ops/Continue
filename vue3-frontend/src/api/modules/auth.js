import api from '../axios';

const authApi = {
  login: (data) => {
    return api.post('/users/login/', data);
  },

  register: (data) => {
    return api.post('/users/register/', data);
  },

  forgotPassword: (data) => {
    return api.post('/users/forgot-password/', data);
  },

  resetPassword: (token, data) => {
    return api.post(`/users/reset-password/${token}/`, data);
  },

  logout: () => {
    return api.post('/users/logout/');
  },

  refreshToken: () => {
    return api.post('/users/refresh-token/');
  },

  getProfile: () => {
    return api.get('/users/profile/');
  },

  getUserInfo: () => {
    return api.get('/users/profile/');
  },

  updateProfile: (data) => {
    return api.put('/users/profile/', data);
  },

  updateUserInfo: (data) => {
    return api.put('/users/profile/', data);
  },

  // 用户管理
  getUsers: (params = {}) => {
    return api.get('/users/', { params });
  },

  getUser: (userId) => {
    return api.get(`/users/${userId}/`);
  },

  updateUser: (userId, data) => {
    return api.put(`/users/${userId}/update/`, data);
  },

  deleteUser: (userId) => {
    return api.delete(`/users/${userId}/delete/`);
  },

  batchDeleteUsers: (userIds) => {
    return api.post('/users/batch-delete/', { user_ids: userIds });
  },

  updateUserStatus: (userId, status) => {
    return api.put(`/users/${userId}/status/`, { status });
  },

  // 角色管理
  getRoles: (params = {}) => {
    return api.get('/users/roles/', { params });
  },

  createRole: (data) => {
    return api.post('/users/roles/', data);
  },

  updateRole: (roleId, data) => {
    return api.put(`/users/roles/${roleId}/`, data);
  },

  deleteRole: (roleId) => {
    return api.delete(`/users/roles/${roleId}/`);
  },

  getRolePermissions: (roleId) => {
    return api.get(`/users/roles/${roleId}/permissions/`);
  },

  updateRolePermissions: (roleId, data) => {
    return api.put(`/users/roles/${roleId}/permissions/update/`, data);
  },

  getSystemPermissions: () => {
    return api.get('/users/system-permissions/');
  },

  // 获取权限体系信息（系统权限 + 项目权限）
  getPermissionInfo: () => {
    return api.get('/users/permission-info/');
  },

  // 权限管理
  getPermissions: (params = {}) => {
    return api.get('/users/permissions/', { params });
  },

  updateUserRole: (userId, roleId) => {
    return api.put(`/users/${userId}/role/`, { roleId });
  },

  sendEmailCode: (data) => {
    return api.post('/users/send-email-code/', data);
  },

  changePassword: (data) => {
    return api.put('/users/change-password/', data);
  },

  updateEmail: (data) => {
    return api.put('/users/update-email/', data);
  },

  uploadAvatar: (file) => {
    const formData = new FormData();
    formData.append('avatar', file);
    return api.post('/users/upload-avatar/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  }
};

export default authApi;
