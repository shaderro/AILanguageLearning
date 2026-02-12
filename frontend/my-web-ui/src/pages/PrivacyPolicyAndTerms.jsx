import { useUIText } from '../i18n/useUIText'
import { useUiLanguage } from '../contexts/UiLanguageContext'

const PrivacyPolicyAndTerms = ({ onBack }) => {
  const t = useUIText()
  const { uiLanguage } = useUiLanguage()
  const isEnglish = uiLanguage === 'en'

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          {onBack && (
            <button
              onClick={onBack}
              className="mb-4 text-gray-600 hover:text-gray-900 transition-colors flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              {t('返回')}
            </button>
          )}
          <h1 className="text-3xl font-bold text-gray-900">
            {isEnglish ? 'Privacy Policy & Terms of Service' : '隐私政策与服务条款'}
          </h1>
        </div>

        {/* Content */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 space-y-12">
          {/* Privacy Policy */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {isEnglish ? 'Privacy Policy (Private Beta)' : '隐私政策（内测版）'}
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              {isEnglish ? 'Last updated:' : '最近更新日期：'} DateDateDate
            </p>

            <div className="space-y-6 text-gray-700">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '1. Information We Collect' : '1. 我们收集的信息'}
                </h3>
                <div className="space-y-4 ml-4">
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">
                      {isEnglish ? '1.1 Account Information' : '1.1 账户信息'}
                    </h4>
                    <p className="text-sm">
                      {isEnglish
                        ? 'We collect basic account information such as email address or username, and encrypted authentication credentials, solely for account identification and login purposes.'
                        : '我们会收集用于账户识别和登录的基本信息，例如电子邮箱地址或用户名，以及加密后的认证凭据。'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">
                      {isEnglish ? '1.2 User Content' : '1.2 用户内容'}
                    </h4>
                    <p className="text-sm">
                      {isEnglish
                        ? 'We collect text or other content that you voluntarily submit to the Service, including interactions related to AI-generated responses.'
                        : '我们会收集您主动提交给本服务的文本或其他内容，包括与 AI 生成内容相关的交互信息。'}
                    </p>
                  </div>
                  <div>
                    <h4 className="font-medium text-gray-900 mb-2">
                      {isEnglish ? '1.3 Usage Data' : '1.3 使用数据'}
                    </h4>
                    <p className="text-sm">
                      {isEnglish
                        ? 'We may collect basic usage data such as timestamps, feature usage, and error logs for debugging and product improvement.'
                        : '我们可能会收集基础使用数据，如时间戳、功能使用情况和错误日志，用于调试和改进产品。'}
                    </p>
                  </div>
                </div>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '2. How We Use Your Information' : '2. 信息的使用方式'}
                </h3>
                <p className="text-sm mb-2">
                  {isEnglish ? 'We use your information only to:' : '我们仅将您的信息用于：'}
                </p>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>{isEnglish ? 'Provide and operate the Service' : '提供和运行本服务'}</li>
                  <li>{isEnglish ? 'Improve product functionality and user experience' : '改进产品功能和用户体验'}</li>
                  <li>{isEnglish ? 'Ensure system security and stability' : '确保系统安全与稳定'}</li>
                </ul>
                <p className="text-sm mt-3">
                  {isEnglish
                        ? 'We do not sell your personal data, use it for advertising, or share it with unrelated third parties.'
                        : '我们不会出售您的个人数据，不会将其用于广告目的，也不会与无关的第三方共享。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '3. AI and Third-Party Services' : '3. AI 与第三方服务'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'The Service may use third-party AI models or cloud infrastructure to process user input. Data is transmitted only as necessary to provide the Service and is handled according to industry-standard security practices.'
                        : '本服务可能使用第三方 AI 模型或云基础设施来处理用户输入。数据仅在提供服务所必需的范围内进行传输，并遵循行业标准的安全实践。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '4. Data Storage and Location' : '4. 数据存储与位置'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'User data may be stored on servers located outside your country of residence. We take reasonable measures to protect your data, but no system can be guaranteed to be completely secure.'
                        : '用户数据可能存储在您所在国家或地区以外的服务器上。我们会采取合理措施保护您的数据，但无法保证绝对安全。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '5. Data Retention and Deletion' : '5. 数据保留与删除'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'As this Service is provided as a private beta, data may be deleted, reset, or modified at any time. You may request deletion of your account or data by contacting: contactemailcontact emailcontactemail.'
                        : '由于本服务处于内测阶段，数据可能会被随时删除、重置或修改。您可以通过 联系邮箱联系邮箱联系邮箱 请求删除账户或相关数据。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '6. Your Rights' : '6. 您的权利'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'You may request access to or deletion of your data. Requests will be handled on a best-effort basis during the beta period.'
                        : '您有权请求访问或删除您的数据。在内测期间，我们将尽力处理相关请求。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '7. Changes to This Policy' : '7. 政策变更'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'We may update this Privacy Policy from time to time. Continued use of the Service indicates acceptance of the updated policy.'
                        : '我们可能会不定期更新本隐私政策。继续使用本服务即表示您同意更新后的政策内容。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '8. Contact' : '8. 联系方式'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'For questions about this Privacy Policy, contact: contactemailcontact emailcontactemail.'
                        : '如对本隐私政策有任何疑问，请联系：联系邮箱联系邮箱联系邮箱。'}
                </p>
              </div>
            </div>
          </section>

          <hr className="border-gray-200" />

          {/* Terms of Service */}
          <section>
            <h2 className="text-2xl font-bold text-gray-900 mb-6">
              {isEnglish ? 'Beta Terms of Service' : '内测服务条款'}
            </h2>
            <p className="text-sm text-gray-500 mb-6">
              {isEnglish ? 'Last updated:' : '最近更新日期：'} DateDateDate
            </p>

            <div className="space-y-6 text-gray-700">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '1. Beta Nature' : '1. 内测说明'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'The Service is provided as a private beta and is not a final product. Features may change, be removed, or become unavailable at any time. The Service is provided "as is" and "as available."'
                        : '本服务为内测版本，并非最终产品。功能可能随时变更、移除或不可用。本服务按"现状"和"可用状态"提供。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '2. Eligibility' : '2. 使用资格'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'Access to the Service is limited to invited users only. We reserve the right to revoke access at any time without notice.'
                        : '本服务仅限受邀用户使用。我们保留在任何时间、无需通知即取消访问权限的权利。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '3. Acceptable Use' : '3. 使用规范'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'You agree not to misuse the Service, attempt to reverse-engineer it, bypass usage limits, or use it for illegal or harmful activities.'
                        : '您同意不会滥用本服务、尝试逆向工程、绕过使用限制，或将其用于任何非法或有害的活动。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '4. Intellectual Property' : '4. 知识产权'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'All rights to the Service, including its design and code, belong to you/yourorganization. You retain ownership of the content you submit, while granting us a limited right to process it to provide the Service.'
                        : '本服务的设计、代码及相关权利归 你/你的组织 所有。您保留所提交内容的所有权，但同意我们为提供服务而对其进行必要处理。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '5. No Guarantees' : '5. 无保证声明'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'We do not guarantee the accuracy of AI-generated content, uninterrupted service, or data persistence. You use the Service at your own risk.'
                        : '我们不保证 AI 生成内容的准确性、不保证服务持续可用或数据永久保存。您需自行承担使用本服务的风险。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '6. Termination' : '6. 终止'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'We may suspend or terminate your access to the Service at any time, for any reason, during the beta period.'
                        : '在内测期间，我们可基于任何原因随时暂停或终止您对本服务的访问。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '7. Changes to These Terms' : '7. 条款变更'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'We may update these Terms from time to time. Continued use of the Service constitutes acceptance of the updated Terms.'
                        : '我们可能会不定期更新本条款。继续使用本服务即表示您接受更新后的条款。'}
                </p>
              </div>

              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-3">
                  {isEnglish ? '8. Contact' : '8. 联系方式'}
                </h3>
                <p className="text-sm">
                  {isEnglish
                        ? 'For questions regarding these Terms, contact: contactemailcontact emailcontactemail.'
                        : '如对本条款有任何疑问，请联系：联系邮箱联系邮箱联系邮箱。'}
                </p>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}

export default PrivacyPolicyAndTerms

