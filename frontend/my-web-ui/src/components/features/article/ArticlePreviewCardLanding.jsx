import { ArticlePreviewCard } from './ArticlePreviewCard'

const ArticlePreviewCardLanding = (props) => {
  return (
    <ArticlePreviewCard
      {...props}
      showEditButton={false}
      showDeleteButton={false}
    />
  )
}

export default ArticlePreviewCardLanding

