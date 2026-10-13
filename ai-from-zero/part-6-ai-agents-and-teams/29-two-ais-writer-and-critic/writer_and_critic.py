# Two AIs work together: the WRITER writes, the CRITIC gives a score and feedback, the writer improves it. Repeat.
import sys

from pydantic import BaseModel

import ai


class Review(BaseModel):          # the critic must answer with exactly this form
    score: int                    # 1 to 10
    feedback: list[str]           # specific things to fix


WRITER = "You are a great writer. Write clearly and concretely, no clichés. Output only the text."
CRITIC = "You are a strict editor. Score from 1 to 10 (10 = perfect, rare). Give 2-4 specific, fixable feedback points."

task = " ".join(sys.argv[1:]) or "A 100-word LinkedIn post: I just built my first AI chatbot with a web page, as a complete beginner."
draft = ai.ask(task, system=WRITER)

for round_number in range(1, 4):
    review = ai.ask_for_data(f"Task: {task}\n\nDraft:\n{draft}\n\nReview this draft.", Review, system=CRITIC)
    print(f"\n--- Round {round_number}: score {review.score}/10 ---")
    for point in review.feedback:
        print(f"   • {point}")
    if review.score >= 8:
        break
    draft = ai.ask(f"Task: {task}\n\nYour draft:\n{draft}\n\nImprove it using this feedback:\n" + "\n".join(review.feedback), system=WRITER)

print(f"\n✨ FINAL VERSION:\n{draft}")
