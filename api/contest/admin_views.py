from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
import re

from .models import Contest, ContestProblem
from problem.models import Problem


def get_next_saturday(now=None):
    now = now or timezone.now()
    days_until_sat = (5 - now.weekday()) % 7
    if days_until_sat == 0 and now.hour >= 20:
        days_until_sat = 7
    return (now + timedelta(days=days_until_sat)).replace(
        hour=20, minute=0, second=0, microsecond=0
    )


@staff_member_required
def set_contest(request, contest_id=None):
    contest = get_object_or_404(Contest, id=contest_id) if contest_id else None

    if request.method == "POST":
        action = request.POST.get("action", "save_contest")

        if action == "save_contest":
            title = request.POST.get("title", "").strip()
            start_time_str = request.POST.get("start_time", "").strip()
            duration_minutes = int(request.POST.get("duration_minutes", 90))
            description = request.POST.get("description", "").strip()
            is_published = request.POST.get("is_published") == "on"

            try:
                start_time = (
                    timezone.make_aware(datetime.fromisoformat(start_time_str))
                    if start_time_str
                    else get_next_saturday()
                )
            except (ValueError, TypeError):
                start_time = get_next_saturday()

            if contest:
                contest.title, contest.start_time, contest.duration_minutes = (
                    title,
                    start_time,
                    duration_minutes,
                )
                contest.end_time = start_time + timedelta(minutes=duration_minutes)
                contest.description, contest.is_published = description, is_published
                contest.save()
                messages.success(
                    request, f"Contest '{contest.title}' updated successfully!"
                )
            else:
                contest = Contest.objects.create(
                    title=title,
                    start_time=start_time,
                    duration_minutes=duration_minutes,
                    end_time=start_time + timedelta(minutes=duration_minutes),
                    description=description,
                    is_published=is_published,
                    created_by=request.user,
                )
                messages.success(
                    request, f"Contest '{contest.title}' created! Now add problems."
                )

            return redirect("set_contest_edit", contest_id=contest.id)

        elif action == "add_problem" and contest:
            problem = get_object_or_404(Problem, id=request.POST.get("problem_id"))
            order = int(request.POST.get("order", contest.contest_problems.count() + 1))
            pts_in = request.POST.get("points", "")
            points = (
                int(pts_in)
                if pts_in.isdigit()
                else {"EASY": 3, "MEDIUM": 5, "HARD": 7}.get(problem.difficulty, 3)
            )

            ContestProblem.objects.update_or_create(
                contest=contest,
                problem=problem,
                defaults={"order": order, "points": points},
            )
            messages.success(
                request,
                f"Added '{problem.name}' as Q{order} with {points} points to {contest.title}.",
            )
            return redirect("set_contest_edit", contest_id=contest.id)

        elif action == "update_problem_points" and contest:
            cp = get_object_or_404(
                ContestProblem,
                id=request.POST.get("contest_problem_id"),
                contest=contest,
            )
            pts_in = request.POST.get("points", "")
            if pts_in.isdigit():
                cp.points = int(pts_in)
                cp.save()
                messages.success(
                    request,
                    f"Updated Q{cp.order} ({cp.problem.name}) points to {cp.points}.",
                )
            return redirect("set_contest_edit", contest_id=contest.id)

        elif action == "remove_problem" and contest:
            ContestProblem.objects.filter(
                id=request.POST.get("contest_problem_id"), contest=contest
            ).delete()
            for idx, cp in enumerate(
                contest.contest_problems.order_by("order"), start=1
            ):
                cp.order = idx
                cp.save()
            messages.success(request, "Problem removed from contest.")
            return redirect("set_contest_edit", contest_id=contest.id)

        elif action == "delete_contest" and contest:
            title = contest.title
            contest.delete()
            messages.success(request, f"Contest '{title}' deleted.")
            return redirect("set_contest")

    weekly_nums = [
        int(m.group(1))
        for c in Contest.objects.filter(is_weekly=True)
        if (m := re.search(r"Weekly run (\d+)", c.title, re.I))
    ]
    next_weekly_name = f"Weekly run {max(weekly_nums, default=0) + 1}"
    next_sat = get_next_saturday()

    return render(
        request,
        "contest/set_contest.html",
        {
            "contest": contest,
            "contest_problems": (
                contest.contest_problems.select_related("problem").order_by("order")
                if contest
                else []
            ),
            "all_contests": Contest.objects.all().order_by("-start_time"),
            "available_problems": Problem.objects.all().order_by("-created_at")[:100],
            "next_weekly_name": next_weekly_name,
            "next_sat_iso": next_sat.strftime("%Y-%m-%dT%H:%M"),
            "now": timezone.now(),
        },
    )
