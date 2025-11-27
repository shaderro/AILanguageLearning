import { BaseButtonDemo } from '../components/base/BaseButton.demo';
import { BaseCardDemo } from '../components/base/BaseCard.demo';
import { BaseBadgeDemo } from '../components/base/BaseBadge.demo';
import { BaseModalDemo } from '../components/base/BaseModal.demo';
import { BaseInputDemo } from '../components/base/BaseInput.demo';
import { BaseSpinnerDemo } from '../components/base/BaseSpinner.demo';
import { ConfirmDialogDemo } from '../components/base/ConfirmDialog.demo';
import { LoadingOverlayDemo } from '../components/base/LoadingOverlay.demo';
import { ArticlePreviewCard } from '../components/features/article/ArticlePreviewCard';

const demoSections = [
  {
    title: 'BaseButton',
    description: '统一按钮样式，支持 variant/size/fullWidth/loading。',
    component: BaseButtonDemo,
  },
  {
    title: 'BaseCard',
    description: '增强卡片结构，内置 header/footer/actions 与交互态。',
    component: BaseCardDemo,
  },
  {
    title: 'BaseBadge',
    description: '语义标签组件，适配状态/语言/难度等场景。',
    component: BaseBadgeDemo,
  },
  {
    title: 'BaseModal',
    description: '模态框容器，支持标题、描述、footer 按钮。',
    component: BaseModalDemo,
  },
  {
    title: 'BaseInput',
    description: '统一输入框样式，支持 label/helper/error/prefix/suffix。',
    component: BaseInputDemo,
  },
  {
    title: 'BaseSpinner',
    description: '加载指示器，可配置尺寸与语义色。',
    component: BaseSpinnerDemo,
  },
  {
    title: 'ConfirmDialog',
    description: '基于 BaseModal 的确认操作模态框，附带 meta 信息展示。',
    component: ConfirmDialogDemo,
  },
  {
    title: 'LoadingOverlay',
    description: '局部或全屏的加载遮罩，可搭配 BaseSpinner。',
    component: LoadingOverlayDemo,
  },
];

const functionSections = [
  {
    title: 'ArticlePreviewCard',
    description: '文章列表中的预览卡片，基于 BaseCard + BaseButton 实现。',
    component: function ArticlePreviewCardDemo() {
      return (
        <ArticlePreviewCard
          title="Some Name Of An Article which is too long to display"
          wordCount="1500"
          noteCount="5"
          preview="This is a two-line preview sentence of this article. If it's too long, it will only display the first two line... Check it out!"
          onEdit={() => {}}
          onDelete={() => {}}
          onRead={() => {}}
        />
      );
    },
  },
];

export default function UIDemoPage() {
  return (
    <div className="min-h-[calc(100vh-64px)] bg-gray-50 pb-16">
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 lg:px-8">
        <header className="mb-10 space-y-3">
          <p className="text-sm font-semibold uppercase tracking-wide text-blue-600">
            UI Design System / Base Components
          </p>
          <h1 className="text-3xl font-bold text-gray-900">基础组件 Demo</h1>
          <p className="text-gray-600">
            通过访问 <code className="rounded bg-gray-100 px-1.5 py-0.5 text-sm">?api=db&amp;page=UIDemo</code>{' '}
            可快速预览当前已实现的基础组件。所有示例均直接引用组件本身，便于验证样式与交互。
          </p>
        </header>

        <div className="space-y-8">
          {demoSections.map(({ title, description, component: Component }) => (
            <section
              key={title}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
                  <p className="text-sm text-gray-500">{description}</p>
                </div>
              </div>
              <div className="mt-6">
                <Component />
              </div>
            </section>
          ))}
        </div>

        <div className="mt-12 space-y-8">
          <header className="space-y-2">
            <h2 className="text-2xl font-bold text-gray-900">Function Components</h2>
            <p className="text-gray-600">
              基于基础组件组合出的业务组件示例，将逐步扩展。
            </p>
          </header>
          {functionSections.map(({ title, description, component: Component }) => (
            <section
              key={title}
              className="rounded-2xl border border-gray-200 bg-white p-6 shadow-sm"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                <div>
                  <h3 className="text-xl font-semibold text-gray-900">{title}</h3>
                  <p className="text-sm text-gray-500">{description}</p>
                </div>
              </div>
              <div className="mt-6">
                <Component />
              </div>
            </section>
          ))}
        </div>
      </div>
    </div>
  );
}


