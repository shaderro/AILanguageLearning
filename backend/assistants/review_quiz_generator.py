"""Generate validated, session-only review questions for CONTENT_LANGUAGE reading MVP."""

import json
from typing import Any, Dict, List

from backend.assistants.sub_assistants.sub_assistant import SubAssistant


QUESTION_TYPES = {
    "vocabulary_in_context",
    "expression_usage",
    "grammar_understanding",
}


class ReviewQuizGenerator(SubAssistant):
    def __init__(self, content_language="German", ui_language="English"):
        super().__init__(
            sys_prompt=(
                "You create a gentle first-review comprehension check for CONTENT_LANGUAGE B1 learners who have just "
                "seen these knowledge points for the first time. Test recognition and understanding only, "
                "not independent application, transfer, or CONTENT_LANGUAGE production. Use only the supplied article, "
                "selected knowledge points, and their preview explanations. Do not test mastered or unselected "
                "knowledge, and do not introduce grammar concepts that the selected point does not explain.\n\n"
                "Question design:\n"
                "- Use one short four-option single-choice question per selected point when reliable. Rank by "
                "learning value; generate exactly one question for EVERY supplied point. Never omit a point "
                "or test one point twice. Use a simple context-meaning question when necessary.\n"
                "- For vocabulary and expressions, ask what the expression means in the supplied sentence, e.g. "
                "'What does Kontakte knüpfen mean in this sentence?' translated into UI_LANGUAGE. "
                "Every question stem MUST use UI_LANGUAGE; only the cited knowledge point stays in CONTENT_LANGUAGE. "
                "Never append or quote the original sentence in the question field: the UI displays it separately below.\n"
                "- All four answer options for vocabulary and expressions must be concise UI_LANGUAGE meanings. Use "
                "plausible confusions from the same semantic area, but make exactly one option correct in context.\n"
                "- For grammar, test only the basic meaning, relationship, or function of the structure in its "
                "original sentence. Prefer concise UI_LANGUAGE question wording and UI_LANGUAGE options. Do not ask for "
                "case selection, sentence transformation, gap filling, rule recall beyond the preview, or sentence "
                "construction.\n"
                "- Keep the stem and options short, familiar, and similar in length. Do not make the correct option "
                "stand out through detail or wording. Do not repeat the full preview explanation in the question.\n\n"
                "JSON safety: return syntactically valid JSON. Inside any JSON string value, never use an unescaped "
                "ASCII double-quote character. Avoid quotation marks around CONTENT_LANGUAGE expressions, or use single quotes. "
                "When quoting an original excerpt, preserve it exactly without wrapping it in double quotes.\n\n"
                "Feedback: after the answer, give one concise UI_LANGUAGE explanation of why the correct meaning fits. "
                "Use at most two short clauses; mention one common confusion only when it helps. Avoid a lecture.\n\n"
                "Every question must have exactly four distinct, plausible options and exactly one unambiguously "
                "correct answer. For each question, copy the exact ID of the single knowledge point it tests into "
                "related_knowledge_point_ids; do not omit the field or invent IDs. Return JSON only "
                "with this exact shape: "
                '{"questions":[{"question_id":"q1",'
                '"question_type":"vocabulary_in_context",'
                '"question":"...","options":["...","...","...","..."],'
                '"correct_answer":0,"explanation":"...",'
                '"related_knowledge_point_ids":["vocab:1"]}]}. '
                "question_type must be one of vocabulary_in_context, expression_usage, or grammar_understanding. "
                "correct_answer is a zero-based option index from 0 to 3. Return an empty questions array only if "
                "none of the selected points supports a reliable first-review comprehension question."
            ).replace('CONTENT_LANGUAGE', content_language).replace('UI_LANGUAGE', ui_language),
            max_tokens=3000,
            parse_json=True,
        )

    def build_prompt(
        self,
        article: str,
        knowledge_points: List[dict],
        learner_level: str = "B1",
        max_questions: int = 5,
    ) -> str:
        return (
            f"Learner level: {learner_level}\n"
            f"Question limit: {max_questions}\n"
            "The IDs below are the only IDs allowed in related_knowledge_point_ids.\n"
            f"Article:\n{article}\n"
            f"Selected learning points:\n{json.dumps(knowledge_points, ensure_ascii=False)}"
        )

    def generate(
        self,
        article: str,
        knowledge_points: List[dict],
        learner_level: str = "B1",
    ) -> List[dict]:
        """Cover every point, using small batches and retrying missing associations."""
        result = []
        for start in range(0, len(knowledge_points), 5):
            pending = knowledge_points[start:start + 5]
            for attempt in range(3):
                generated = self._generate_batch(article, pending, learner_level)
                covered = set()
                for question in generated:
                    related = question["related_knowledge_point_ids"]
                    if len(related) != 1 or related[0] in covered:
                        continue
                    covered.add(related[0])
                    question["question_id"] = f"q{len(result) + 1}"
                    result.append(question)
                pending = [point for point in pending if str(point["id"]) not in covered]
                if not pending:
                    break
            if pending:
                raise ValueError("Review generation did not cover every knowledge point")
        by_point = {q["related_knowledge_point_ids"][0]: q for q in result}
        return [by_point[str(point["id"])] for point in knowledge_points]

    def _generate_batch(
        self,
        article: str,
        knowledge_points: List[dict],
        learner_level: str = "B1",
    ) -> List[dict]:
        if not knowledge_points:
            return []

        allowed_ids = {
            str(point.get("id"))
            for point in knowledge_points
            if isinstance(point, dict) and point.get("id") is not None
        }
        if not allowed_ids:
            raise ValueError("No valid knowledge point IDs were supplied")
        points_by_id = {
            str(point["id"]): point
            for point in knowledge_points
            if isinstance(point, dict) and point.get("id") is not None
        }

        response = self.run(
            article=article,
            knowledge_points=knowledge_points,
            learner_level=learner_level,
            max_questions=min(5, len(allowed_ids)),
        )
        if not isinstance(response, dict) or not isinstance(response.get("questions"), list):
            raise ValueError("Review model must return a questions array")

        questions = response["questions"]
        if len(questions) > min(5, len(allowed_ids)):
            raise ValueError("Review model exceeded the question limit")

        validated: List[dict] = []
        seen_question_ids = set()
        tested_point_ids = set()
        for index, question in enumerate(questions):
            if not isinstance(question, dict):
                raise ValueError(f"Question {index + 1} must be an object")
            question_id = question.get("question_id")
            question_type = question.get("question_type")
            prompt = question.get("question")
            options = question.get("options")
            correct = question.get("correct_answer")
            explanation = question.get("explanation")
            related = question.get("related_knowledge_point_ids")

            if not isinstance(related, list) or not related:
                related = self._infer_related_ids(question, points_by_id, tested_point_ids)
                if related:
                    print(
                        f"[CONTENT_LANGUAGEReadingReview] Recovered missing knowledge-point association "
                        f"for {question_id}: {related}"
                    )
                else:
                    print(
                        f"[CONTENT_LANGUAGEReadingReview] Skipping {question_id}: missing or ambiguous "
                        "knowledge-point association"
                    )
                    continue

            if not isinstance(question_id, str) or not question_id.strip() or question_id in seen_question_ids:
                raise ValueError(f"Question {index + 1} has a missing or duplicate question_id")
            if question_type not in QUESTION_TYPES:
                raise ValueError(f"Question {question_id} has an unsupported question_type")
            if not isinstance(prompt, str) or not prompt.strip():
                raise ValueError(f"Question {question_id} has no prompt")
            if not isinstance(options, list) or len(options) != 4 or any(
                not isinstance(option, str) or not option.strip() for option in options
            ):
                raise ValueError(f"Question {question_id} must have exactly four non-empty options")
            if len({" ".join(option.casefold().split()) for option in options}) != 4:
                raise ValueError(f"Question {question_id} contains duplicate options")
            if isinstance(correct, bool) or not isinstance(correct, int) or correct not in range(4):
                raise ValueError(f"Question {question_id} has an invalid correct_answer index")
            if not isinstance(explanation, str) or not explanation.strip():
                raise ValueError(f"Question {question_id} has no feedback explanation")
            if not isinstance(related, list) or not related:
                raise ValueError(f"Question {question_id} must reference a knowledge point")
            normalized_related = list(dict.fromkeys(str(point_id) for point_id in related))
            if any(point_id not in allowed_ids for point_id in normalized_related):
                print(
                    f"[CONTENT_LANGUAGEReadingReview] Skipping {question_id}: references an unselected "
                    f"knowledge point {normalized_related}"
                )
                continue
            if tested_point_ids.intersection(normalized_related):
                print(
                    f"[CONTENT_LANGUAGEReadingReview] Skipping {question_id}: repeats a knowledge point "
                    f"{normalized_related}"
                )
                continue

            seen_question_ids.add(question_id)
            tested_point_ids.update(normalized_related)
            validated.append({
                "question_id": question_id,
                "question_type": question_type,
                "question": prompt.strip(),
                "options": [option.strip() for option in options],
                "correct_answer": correct,
                "explanation": explanation.strip(),
                "related_knowledge_point_ids": normalized_related,
            })

        return validated

    @staticmethod
    def _infer_related_ids(question: dict, points_by_id: dict, tested_point_ids: set) -> List[str]:
        """Recover a missing point ID only when question text uniquely identifies a supplied point."""
        question_text = " ".join(
            str(question.get(field) or "")
            for field in ("question", "explanation")
        ).casefold()
        question_text = " ".join(question_text.split())
        scores = {}
        for point_id, point in points_by_id.items():
            if point_id in tested_point_ids:
                continue
            score = 0
            display_name = " ".join(str(point.get("display_name") or "").casefold().split())
            name_variants = [variant.strip() for variant in display_name.replace("…", "...").split("/")]
            if any(len(variant) >= 4 and variant in question_text for variant in name_variants):
                score = 3
            for context in point.get("sentence_contexts") or []:
                normalized_context = " ".join(str(context).casefold().split())
                if len(normalized_context) >= 24 and normalized_context in question_text:
                    score = max(score, 2)
            if score:
                scores[point_id] = score
        if not scores:
            return []
        best_score = max(scores.values())
        best_ids = [point_id for point_id, score in scores.items() if score == best_score]
        return best_ids if len(best_ids) == 1 else []
