#!/usr/bin/env python3
# ============================================================
# CrewAI Crew - CLI entry point
# Usage: python crew.py --task week1
#        python crew.py --task week1 --dry-run
# ============================================================

import argparse
import sys

from crewai import Crew, ManagerAgent
from agents import data_engineer, iot_engineer, frontend_developer, devops_engineer, project_manager
from tasks import week1_tasks, week2_tasks, week3_tasks, week4_tasks


def get_tasks_for_week(week):
    week_map = {
        "week1": week1_tasks,
        "week2": week2_tasks,
        "week3": week3_tasks,
        "week4": week4_tasks
    }
    return week_map.get(week.lower(), week1_tasks)


def create_crew(tasks, week_name):
    manager = ManagerAgent(
        role="Project Manager",
        goal="Coordinate the team and ensure tasks are completed efficiently",
        backstory="Experienced manager who coordinates IoT development projects"
    )

    return Crew(
        agents=[
            data_engineer,
            iot_engineer,
            frontend_developer,
            devops_engineer,
            project_manager
        ],
        tasks=tasks,
        manager_agent=manager,
        verbose=True
    )


def print_task_plan(tasks):
    print("\n" + "=" * 60)
    print("  TASK PLAN - Dry Run")
    print("=" * 60 + "\n")

    for i, task in enumerate(tasks, 1):
        print(f"Task {i}:")
        print(f"  Agent: {task.agent.role if task.agent else 'Not assigned'}")
        print(f"  Description: {task.description[:200]}...")
        print(f"  Expected: {task.expected_output}")
        print()

    print("=" * 60)
    print(f"Total Tasks: {len(tasks)}")
    print("=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(description="IoT Forge CrewAI CLI")
    parser.add_argument(
        "--task",
        choices=["week1", "week2", "week3", "week4"],
        default="week1",
        help="Which week's tasks to execute"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print task plan without executing"
    )

    args = parser.parse_args()

    print(f"\n[CREW] Loading {args.task} tasks...")
    tasks = get_tasks_for_week(args.task)()

    if args.dry_run:
        print_task_plan(tasks)
        print("[CREW] Dry run complete. No tasks were executed.")
        sys.exit(0)

    print(f"[CREW] Building crew with {len(tasks)} tasks...")
    crew = create_crew(tasks, args.task)

    print(f"[CREW] Starting execution...\n")
    result = crew.kickoff()

    print(f"\n[CREW] Execution completed!")
    print(f"Result: {result}")


if __name__ == "__main__":
    main()