from django.utils import timezone
from django.db import transaction
from django.core.cache import cache
from .models import (
    Contest,
    ContestProblem,
    ContestRegistration,
    ContestParticipant,
    ContestSubmission,
)
from problem.models import AnswerStatus


def record_contest_submission(contest, problem, user, final_status, results=None):
    """
    Atomically records contest submission and updates ContestParticipant score & penalty.
    """
    now = timezone.now()
    time_taken_seconds = max(0, int((now - contest.start_time).total_seconds()))
    is_ac = final_status == AnswerStatus.ACCEPTED

    with transaction.atomic():
        # Ensure user is registered
        ContestRegistration.objects.get_or_create(contest=contest, user=user)

        # Create contest submission
        csub = ContestSubmission.objects.create(
            contest=contest,
            problem=problem,
            user=user,
            status=final_status,
            is_accepted=is_ac,
            time_taken_seconds=time_taken_seconds,
        )

        # Get or create participant
        participant, _ = ContestParticipant.objects.select_for_update().get_or_create(
            contest=contest, user=user
        )

        # Get contest problem points
        cp = ContestProblem.objects.filter(contest=contest, problem=problem).first()
        pts = cp.points if cp else 3

        prob_key = str(problem.id)
        details = dict(participant.problem_details or {})
        prob_info = details.get(
            prob_key,
            {
                "status": "NOT_SOLVED",
                "wrong_attempts": 0,
                "time_seconds": 0,
                "points": 0,
            },
        )

        if is_ac and prob_info.get("status") != "AC":
            prob_info["status"] = "AC"
            prob_info["time_seconds"] = time_taken_seconds
            prob_info["points"] = pts

            participant.score += pts
            participant.problems_solved += 1
            # Penalty: finish time + 5 mins (300s) per wrong submission
            wrong_count = prob_info.get("wrong_attempts", 0)
            penalty_for_this_problem = time_taken_seconds + (wrong_count * 300)
            participant.penalty_seconds += penalty_for_this_problem
            participant.finish_time_seconds = max(
                participant.finish_time_seconds, time_taken_seconds
            )

        elif not is_ac and prob_info.get("status") != "AC":
            prob_info["wrong_attempts"] = prob_info.get("wrong_attempts", 0) + 1

        details[prob_key] = prob_info
        participant.problem_details = details
        participant.save()

        # Invalidate leaderboard cache
        cache.delete(f"contest_leaderboard_{contest.id}")

    return csub
