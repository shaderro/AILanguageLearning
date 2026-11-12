# Standalone Analyze Text

Open `http://localhost:5173/analyze-text.html`. This is a separate static entry served by Vite and copied to `dist` by the normal build. Main Assistant React routes and styles are unchanged.

The entry uses `public/analyze-text/styles.css` for the Figma design tokens and shared visual primitives, `engine.js` for the existing reading API adapters and review state, and `flow.js` for the independent upload → preview → reading → review → results renderers.

## Live flow

Sign in through Main Assistant on the same origin first. The independent page uses the existing `access_token` and reading APIs. Paste and TXT/MD imports run in the browser; URL/PDF extraction uses the authenticated `/api/v2/german-reading/import` endpoints. Limits are 800 words / 12,000 characters and 10 MB for PDF files. The interface only advertises formats supported by the backend.

Paragraph mode uses sentence segmentation; line mode preserves nonempty source lines. Both use paragraph knowledge analysis. Preview saves mastered/learning flags, reading highlights each expression, and review excludes mastered points. Questions require explicit confirmation and manual continuation. Mistake review keeps the original score.

The sample link (`?sample=1`) provides a clearly labeled, local three-sentence interaction walkthrough. It does not call AI or write data. Live AI analysis and question generation require authentication and configured model credentials.

## Verification

- Vite production build passes; existing bundle-size and duplicate-attribute warnings remain outside this change.
- Browser checks cover paste import status, vocabulary/grammar preview, known-point filtering, translation, sentence advancement, wrong-answer feedback, results and mistake review.
- Desktop layout checked at 1440 px; mobile layout checked at the browser's narrow default size.
- JavaScript syntax, Python compilation and a line-segmentation check pass.
- Live backend health and registration of reading import routes verified. No authenticated live AI submission was performed.
