import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { useState } from 'react';

export const QueryProvider = ({ children }) => {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // 全局查询配置
            staleTime: 5 * 60 * 1000, // 5分钟
            gcTime: 10 * 60 * 1000, // 10分钟 (原 cacheTime)
            retry: (failureCount, error) => {
              // 网络错误重试3次
              if (error?.response?.status >= 500) {
                return failureCount < 3;
              }
              return false;
            },
            refetchOnWindowFocus: false, // 窗口聚焦时不重新获取
          },
          mutations: {
            // 全局变更配置
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {/* 开发环境下的调试工具 */}
      {process.env.NODE_ENV === 'development' && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
};
