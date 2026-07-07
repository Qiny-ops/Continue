import { PROJECT_ROUTE_PREFIX } from '@/router/constants'

export const getEmptyMessage = (activeTab) => {
  if (activeTab === 'managed') {
    return '您还没有管理的项目，或尝试切换到"我参与的"标签'
  }
  return '还没有项目，创建第一个项目开始测试之旅吧！'
}

export const getModuleRoute = (moduleType, projectCode) => {
  if (!projectCode) return null

  const routes = {
    testcase: `${PROJECT_ROUTE_PREFIX}/${projectCode}/testcases`,
    testplan: `${PROJECT_ROUTE_PREFIX}/${projectCode}/testplans`,
    bug: `${PROJECT_ROUTE_PREFIX}/${projectCode}/bugs`,
    settings: `${PROJECT_ROUTE_PREFIX}/${projectCode}/settings`
  }

  return routes[moduleType] || null
}

/**
 * 获取项目详情路由路径
 * @param {string|number} projectCode - 项目代码或ID
 * @param {string} [path] - 子路径（可选）
 * @returns {string} 完整路由路径
 */
export const getProjectRoute = (projectCode, path = '') => {
  if (!projectCode) return '/projects'
  const basePath = `${PROJECT_ROUTE_PREFIX}/${projectCode}`
  return path ? `${basePath}/${path}` : `${basePath}/`
}

export const filterProjects = (projects, { activeTab, searchKeyword }) => {
  if (!projects || projects.length === 0) {
    return []
  }

  let filtered = [...projects]

  if (activeTab === 'managed') {
    filtered = filtered.filter(p => p?.isAdmin === true)
  }

  if (searchKeyword) {
    const keyword = searchKeyword.toLowerCase()
    filtered = filtered.filter(
      project =>
        project?.name?.toLowerCase().includes(keyword) ||
        project?.description?.toLowerCase().includes(keyword)
    )
  }

  return filtered
}
