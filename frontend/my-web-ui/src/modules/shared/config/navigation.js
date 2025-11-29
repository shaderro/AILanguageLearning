// 导航栏配置
export const navigationConfig = {
  title: "React Demo",
  pages: [
    {
      id: 'wordDemo',
      label: 'Word Demo',
      icon: '📚',
      description: '单词定义查询演示',
      path: '/word-demo'
    },
    {
      id: 'grammarDemo',
      label: 'Grammar Demo',
      icon: '📝',
      description: '语法规则学习演示',
      path: '/grammar-demo'
    },
    {
      id: 'article',
      label: 'Article',
      icon: '📖',
      description: '文章阅读和聊天',
      path: '/article'
    }
  ]
}

// 获取页面配置
export const getPageConfig = (pageId) => {
  return navigationConfig.pages.find(page => page.id === pageId)
}

// 获取所有页面
export const getAllPages = () => {
  return navigationConfig.pages
}

// 检查页面是否存在
export const isValidPage = (pageId) => {
  return navigationConfig.pages.some(page => page.id === pageId)
} 