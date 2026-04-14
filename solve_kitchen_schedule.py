"""Solve the restaurant kitchen scheduling case with Google OR-Tools CP-SAT.

Outputs:
  - schedule_results.csv
  - gantt_chart.svg
  - machine_utilization.svg

Install dependency if needed:
  python -m pip install ortools
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Sequence

try:
    from ortools.sat.python import cp_model
except ImportError as exc:  # pragma: no cover - user environment dependent
    raise SystemExit(
        "Missing dependency: ortools\n"
        "Install it with: python -m pip install ortools"
    ) from exc


@dataclass(frozen=True)
class Operation:
    key: str
    dish: str
    label: str
    resource: str
    duration: int


@dataclass(frozen=True)
class ScheduledOperation:
    key: str
    dish: str
    label: str
    resource: str
    duration: int
    start: int
    finish: int


OPERATIONS: Sequence[Operation] = (
    Operation("FR_1", "Fried rice", "FR-1: ingredient preparation", "Prep", 4),
    Operation("FR_2", "Fried rice", "FR-2: wok cooking", "Stove 1", 8),
    Operation("FR_3", "Fried rice", "FR-3: plating", "Plate", 2),
    Operation("GC_1", "Grilled chicken", "GC-1: marinating and preparation", "Prep", 5),
    Operation("GC_2", "Grilled chicken", "GC-2: grilling", "Stove 2", 12),
    Operation("GC_3", "Grilled chicken", "GC-3: plating", "Plate", 3),
    Operation("BP_1", "Baked pasta", "BP-1: ingredient preparation", "Prep", 6),
    Operation("BP_2", "Baked pasta", "BP-2: baking", "Oven", 15),
    Operation("BP_3", "Baked pasta", "BP-3: plating", "Plate", 3),
    Operation("VS_1", "Vegetable salad", "VS-1: washing and cutting", "Prep", 4),
    Operation("VS_2", "Vegetable salad", "VS-2: plating", "Plate", 2),
    Operation("OM_1", "Omelette", "OM-1: ingredient preparation", "Prep", 3),
    Operation("OM_2", "Omelette", "OM-2: pan cooking", "Stove 1", 5),
    Operation("OM_3", "Omelette", "OM-3: plating", "Plate", 2),
)

PRECEDENCE: Sequence[tuple[str, str]] = (
    ("FR_1", "FR_2"),
    ("FR_2", "FR_3"),
    ("GC_1", "GC_2"),
    ("GC_2", "GC_3"),
    ("BP_1", "BP_2"),
    ("BP_2", "BP_3"),
    ("VS_1", "VS_2"),
    ("OM_1", "OM_2"),
    ("OM_2", "OM_3"),
)

RESOURCE_ORDER = ("Prep", "Stove 1", "Stove 2", "Oven", "Plate")

COLORS = {
    "Fried rice": "#2f80ed",
    "Grilled chicken": "#eb5757",
    "Baked pasta": "#27ae60",
    "Vegetable salad": "#00a7a7",
    "Omelette": "#f2994a",
}


def solve_schedule(max_time_seconds: float = 10.0) -> tuple[int, List[ScheduledOperation]]:
    model = cp_model.CpModel()
    horizon = sum(op.duration for op in OPERATIONS)
    operations_by_key = {op.key: op for op in OPERATIONS}

    starts = {}
    ends = {}
    intervals = {}
    intervals_by_resource: Dict[str, List[cp_model.IntervalVar]] = {}

    for op in OPERATIONS:
        starts[op.key] = model.NewIntVar(0, horizon, f"start_{op.key}")
        ends[op.key] = model.NewIntVar(0, horizon, f"end_{op.key}")
        intervals[op.key] = model.NewIntervalVar(
            starts[op.key],
            op.duration,
            ends[op.key],
            f"interval_{op.key}",
        )
        intervals_by_resource.setdefault(op.resource, []).append(intervals[op.key])

    for before, after in PRECEDENCE:
        model.Add(starts[after] >= ends[before])

    for resource_intervals in intervals_by_resource.values():
        model.AddNoOverlap(resource_intervals)

    makespan = model.NewIntVar(0, horizon, "makespan")
    last_operation_keys = ("FR_3", "GC_3", "BP_3", "VS_2", "OM_3")
    model.AddMaxEquality(makespan, [ends[key] for key in last_operation_keys])

    # Makespan is the primary objective. The small secondary term gives a stable,
    # compact schedule when multiple schedules have the same makespan.
    scale = horizon * len(OPERATIONS) + 1
    model.Minimize(makespan * scale + sum(starts[key] for key in starts))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_time_seconds
    solver.parameters.num_search_workers = 8

    status = solver.Solve(model)
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        raise RuntimeError(f"No feasible schedule found. Solver status: {solver.StatusName(status)}")

    schedule = []
    for key, op in operations_by_key.items():
        start = solver.Value(starts[key])
        finish = solver.Value(ends[key])
        schedule.append(
            ScheduledOperation(
                key=key,
                dish=op.dish,
                label=op.label,
                resource=op.resource,
                duration=op.duration,
                start=start,
                finish=finish,
            )
        )

    schedule.sort(key=lambda item: (item.start, item.resource, item.key))
    return solver.Value(makespan), schedule


def write_schedule_csv(path: Path, schedule: Sequence[ScheduledOperation]) -> None:
    with path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["dish", "operation", "resource", "duration", "start", "finish"])
        for item in schedule:
            writer.writerow([item.dish, item.label, item.resource, item.duration, item.start, item.finish])


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def write_gantt_svg(path: Path, makespan: int, schedule: Sequence[ScheduledOperation]) -> None:
    left = 140
    top = 95
    row_height = 80
    bar_height = 48
    scale = 20
    axis_end = left + makespan * scale
    width = axis_end + 160
    height = top + row_height * len(RESOURCE_ORDER) + 120

    rows = {resource: top + index * row_height for index, resource in enumerate(RESOURCE_ORDER)}

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc" style="max-width:100%;height:auto;">',
        '  <title id="title">Gantt chart of the optimal kitchen schedule</title>',
        f'  <desc id="desc">Optimal small restaurant kitchen schedule with makespan {makespan} minutes.</desc>',
        f'  <rect width="{width}" height="{height}" fill="#ffffff"/>',
        f'  <text x="{width / 2:.0f}" y="34" text-anchor="middle" font-family="Arial, sans-serif" '
        'font-size="22" font-weight="700" fill="#222222">Optimal Kitchen Schedule</text>',
        f'  <text x="{width / 2:.0f}" y="62" text-anchor="middle" font-family="Arial, sans-serif" '
        f'font-size="15" fill="#444444">Makespan = {makespan} minutes</text>',
    ]

    lines.append('  <g stroke="#e6e6e6" stroke-width="1">')
    ticks = list(range(0, makespan + 1, 5))
    if ticks[-1] != makespan:
        ticks.append(makespan)
    for tick in ticks:
        x = left + tick * scale
        lines.append(f'    <line x1="{x}" y1="{top}" x2="{x}" y2="{top + row_height * len(RESOURCE_ORDER) + 5}"/>')
    lines.append("  </g>")

    axis_y = top + row_height * len(RESOURCE_ORDER) + 5
    lines.extend(
        [
            '  <g stroke="#222222" stroke-width="1.5">',
            f'    <line x1="{left}" y1="{axis_y}" x2="{axis_end}" y2="{axis_y}"/>',
            f'    <line x1="{left}" y1="{top}" x2="{left}" y2="{axis_y}"/>',
            "  </g>",
            '  <g font-family="Arial, sans-serif" font-size="13" fill="#555555" text-anchor="middle">',
        ]
    )
    for tick in ticks:
        x = left + tick * scale
        lines.append(f'    <text x="{x}" y="{axis_y + 23}">{tick}</text>')
    lines.append(f'    <text x="{(left + axis_end) / 2:.0f}" y="{axis_y + 52}" font-size="15" fill="#333333">Time (minutes)</text>')
    lines.append("  </g>")

    lines.append('  <g font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#333333" text-anchor="end">')
    for resource in RESOURCE_ORDER:
        lines.append(f'    <text x="{left - 18}" y="{rows[resource] + 31}">{esc(resource)}</text>')
    lines.append("  </g>")

    lines.append('  <g font-family="Arial, sans-serif" font-size="13" font-weight="700" text-anchor="middle">')
    for item in schedule:
        x = left + item.start * scale
        y = rows[item.resource] + 15
        w = item.duration * scale
        label = item.label.split(":")[0]
        color = COLORS[item.dish]
        lines.extend(
            [
                f'    <rect x="{x}" y="{y}" width="{w}" height="{bar_height}" rx="6" fill="{color}"/>',
                f'    <text x="{x + w / 2:.0f}" y="{y + 20}" fill="#ffffff">{esc(label)}</text>',
                f'    <text x="{x + w / 2:.0f}" y="{y + 38}" fill="#ffffff" font-size="12">{item.start}-{item.finish}</text>',
            ]
        )
    lines.append("  </g>")

    legend_x = 145
    legend_y = height - 35
    lines.append('  <g font-family="Arial, sans-serif" font-size="13" fill="#333333">')
    for dish in ("Fried rice", "Grilled chicken", "Baked pasta", "Vegetable salad", "Omelette"):
        lines.append(f'    <rect x="{legend_x}" y="{legend_y - 12}" width="14" height="14" rx="3" fill="{COLORS[dish]}"/>')
        lines.append(f'    <text x="{legend_x + 22}" y="{legend_y}">{esc(dish)}</text>')
        legend_x += 145
    lines.append("  </g>")
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_utilization_svg(path: Path, makespan: int, schedule: Sequence[ScheduledOperation]) -> None:
    workloads = {resource: 0 for resource in RESOURCE_ORDER}
    for item in schedule:
        workloads[item.resource] += item.duration

    width = 820
    height = 480
    left = 170
    top = 105
    bar_width = 500
    row_gap = 50

    lines = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'role="img" aria-labelledby="title desc" style="max-width:100%;height:auto;">',
        '  <title id="title">Resource utilization chart</title>',
        '  <desc id="desc">Resource utilization rates for the small restaurant kitchen schedule.</desc>',
        f'  <rect width="{width}" height="{height}" fill="#ffffff"/>',
        '  <text x="410" y="38" text-anchor="middle" font-family="Arial, sans-serif" font-size="22" '
        'font-weight="700" fill="#222222">Kitchen Resource Utilization</text>',
        f'  <text x="410" y="66" text-anchor="middle" font-family="Arial, sans-serif" font-size="14" fill="#555555">'
        f'Utilization = resource workload / {makespan}-minute makespan</text>',
        '  <g stroke="#e7e7e7" stroke-width="1">',
    ]
    for tick in range(0, 101, 20):
        x = left + bar_width * tick / 100
        lines.append(f'    <line x1="{x:.0f}" y1="{top}" x2="{x:.0f}" y2="{top + 280}"/>')
    lines.extend(
        [
            "  </g>",
            '  <g stroke="#222222" stroke-width="1.5">',
            f'    <line x1="{left}" y1="{top + 280}" x2="{left + bar_width}" y2="{top + 280}"/>',
            f'    <line x1="{left}" y1="{top}" x2="{left}" y2="{top + 280}"/>',
            "  </g>",
            '  <g font-family="Arial, sans-serif" font-size="13" fill="#555555" text-anchor="middle">',
        ]
    )
    for tick in range(0, 101, 20):
        x = left + bar_width * tick / 100
        lines.append(f'    <text x="{x:.0f}" y="{top + 305}">{tick}%</text>')
    lines.append('    <text x="420" y="440" font-size="15" fill="#333333">Utilization rate</text>')
    lines.append("  </g>")

    lines.append('  <g font-family="Arial, sans-serif" font-size="15" font-weight="700" fill="#333333" text-anchor="end">')
    for index, resource in enumerate(RESOURCE_ORDER):
        y = top + 32 + index * row_gap
        lines.append(f'    <text x="150" y="{y}">{esc(resource)}</text>')
    lines.append("  </g>")

    bar_colors = ["#eb5757", "#2f80ed", "#27ae60", "#00a7a7", "#f2994a"]
    lines.append('  <g font-family="Arial, sans-serif" font-size="14" font-weight="700">')
    for index, resource in enumerate(RESOURCE_ORDER):
        y = top + 10 + index * row_gap
        workload = workloads[resource]
        utilization = workload / makespan * 100
        w = bar_width * utilization / 100
        color = bar_colors[index]
        lines.append(f'    <rect x="{left}" y="{y}" width="{w:.2f}" height="34" rx="6" fill="{color}"/>')
        lines.append(f'    <text x="{left + w + 14:.2f}" y="{y + 23}" fill="#222222">{utilization:.2f}%</text>')
        lines.append(f'    <text x="{left + 15}" y="{y + 23}" fill="#ffffff">{workload} / {makespan} min</text>')
    lines.append("  </g>")
    lines.append("</svg>")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def print_schedule(makespan: int, schedule: Iterable[ScheduledOperation]) -> None:
    print(f"Optimal makespan: {makespan} minutes")
    print()
    print(f"{'Dish':<18} {'Operation':<34} {'Resource':<8} {'Start':>5} {'Finish':>6}")
    print("-" * 78)
    for item in sorted(schedule, key=lambda op: (op.start, op.resource, op.key)):
        print(f"{item.dish:<18} {item.label:<34} {item.resource:<8} {item.start:>5} {item.finish:>6}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Solve the small restaurant kitchen scheduling case.")
    parser.add_argument("--output-dir", default=".", help="Directory for generated CSV and SVG outputs.")
    parser.add_argument("--max-time", type=float, default=10.0, help="CP-SAT max solve time in seconds.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    makespan, schedule = solve_schedule(max_time_seconds=args.max_time)
    print_schedule(makespan, schedule)

    write_schedule_csv(output_dir / "schedule_results.csv", schedule)
    write_gantt_svg(output_dir / "gantt_chart.svg", makespan, schedule)
    write_utilization_svg(output_dir / "machine_utilization.svg", makespan, schedule)
    print()
    print(f"Wrote outputs to: {output_dir.resolve()}")


if __name__ == "__main__":
    main()
