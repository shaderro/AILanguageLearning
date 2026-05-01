import { useMemo, useState } from 'react'
import { apiService } from '../services/api'

const DEMO_TEXT = '昨日、学校で日本語の文章を読みました。'

export default function FuriganaSandbox({ onBack }) {
  const [input, setInput] = useState(DEMO_TEXT)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const tokenPreview = useMemo(() => result?.tokens || [], [result])

  const handleRun = async () => {
    const text = input.trim()
    if (!text) {
      setError('请输入日文文本')
      return
    }
    setLoading(true)
    setError('')
    try {
      const response = await apiService.previewFurigana(text)
      setResult(response)
    } catch (e) {
      const detail = e?.response?.data?.detail || e?.message || '请求失败'
      setError(String(detail))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto w-full max-w-4xl p-4">
      <div className="mb-3 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Furigana Sandbox</h1>
        <button
          className="rounded border border-gray-300 px-3 py-1.5 text-sm text-gray-700 hover:bg-gray-50"
          onClick={onBack}
          type="button"
        >
          Back
        </button>
      </div>

      <p className="mb-3 text-sm text-gray-600">输入日文后调用 `fugashi + unidic-lite` 返回注音。</p>

      <textarea
        className="h-28 w-full rounded border border-gray-300 p-3 text-sm outline-none focus:border-emerald-400"
        onChange={(e) => setInput(e.target.value)}
        placeholder="例如：日本語の勉強は楽しいです。"
        value={input}
      />

      <div className="mt-3 flex items-center gap-2">
        <button
          className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={loading}
          onClick={handleRun}
          type="button"
        >
          {loading ? '解析中...' : '生成注音'}
        </button>
      </div>

      {error ? (
        <div className="mt-3 rounded border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</div>
      ) : null}

      {result ? (
        <div className="mt-5 space-y-4">
          <div>
            <div className="mb-2 text-sm font-medium text-gray-700">Ruby 预览</div>
            <div
              className="rounded border border-gray-200 bg-white p-3 text-lg leading-8"
              dangerouslySetInnerHTML={{ __html: result.ruby_text }}
            />
          </div>

          <div>
            <div className="mb-2 text-sm font-medium text-gray-700">分词结果</div>
            <div className="overflow-x-auto rounded border border-gray-200">
              <table className="w-full min-w-[560px] text-left text-sm">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-3 py-2">Surface</th>
                    <th className="px-3 py-2">Reading</th>
                    <th className="px-3 py-2">POS</th>
                    <th className="px-3 py-2">Needs Ruby</th>
                  </tr>
                </thead>
                <tbody>
                  {tokenPreview.map((token, idx) => (
                    <tr className="border-t border-gray-100" key={`${token.surface}-${idx}`}>
                      <td className="px-3 py-2">{token.surface}</td>
                      <td className="px-3 py-2">{token.reading || '-'}</td>
                      <td className="px-3 py-2">{token.pos || '-'}</td>
                      <td className="px-3 py-2">{token.needs_ruby ? 'yes' : 'no'}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      ) : null}
    </div>
  )
}
