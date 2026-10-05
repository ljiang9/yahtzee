#!/usr/bin/env python3
"""Yahtzee 骰子游戏:掷 5 颗骰子,最多重掷 2 次,13 个计分项打满一局。"""
import argparse
import random
import secrets
import sys
from collections import Counter

UPPER = [("ones", "一点", 1), ("twos", "二点", 2), ("threes", "三点", 3),
         ("fours", "四点", 4), ("fives", "五点", 5), ("sixes", "六点", 6)]
UPPER_FACE = {k: face for k, _, face in UPPER}
UPPER_NAME = {k: name for k, name, _ in UPPER}
LOWER = [("three_of_a_kind", "三条"), ("four_of_a_kind", "四条"),
         ("full_house", "葫芦(25)"), ("small_straight", "小顺(30)"),
         ("large_straight", "大顺(40)"), ("yahtzee", "Yahtzee(50)"),
         ("chance", "机会")]
LOWER_NAME = dict(LOWER)

DICE_FACES = ["\u2680", "\u2681", "\u2682", "\u2683", "\u2684", "\u2685"]


def roll(n, rng):
    return [rng.randint(1, 6) for _ in range(n)]


def score_upper(dice, face):
    return sum(d for d in dice if d == face)


def score_three_of_a_kind(dice):
    return sum(dice) if max(Counter(dice).values()) >= 3 else 0


def score_four_of_a_kind(dice):
    return sum(dice) if max(Counter(dice).values()) >= 4 else 0


def score_full_house(dice):
    counts = sorted(Counter(dice).values())
    return 25 if counts == [2, 3] else 0


def _straights(dice):
    s = set(dice)
    small = any(all(v in s for v in seq) for seq in
                ([1, 2, 3, 4], [2, 3, 4, 5], [3, 4, 5, 6]))
    large = set(dice) in ({1, 2, 3, 4, 5}, {2, 3, 4, 5, 6})
    return small, large


def score_small_straight(dice):
    return 30 if _straights(dice)[0] else 0


def score_large_straight(dice):
    return 40 if _straights(dice)[1] else 0


def score_yahtzee(dice):
    return 50 if len(set(dice)) == 1 else 0


SCORERS = {
    "three_of_a_kind": score_three_of_a_kind,
    "four_of_a_kind": score_four_of_a_kind,
    "full_house": score_full_house,
    "small_straight": score_small_straight,
    "large_straight": score_large_straight,
    "yahtzee": score_yahtzee,
    "chance": sum,
}


def upper_bonus(upper_scores):
    return 35 if sum(upper_scores.values()) >= 63 else 0


def fmt_dice(dice):
    return " ".join(f"{DICE_FACES[d - 1]}({d})" for d in dice)


def play_interactive(rng):
    scores, upper_scores = {}, {}
    for rnd in range(1, 14):
        dice = roll(5, rng)
        print(f"\n第 {rnd}/13 轮")
        for reroll in range(3):
            print("  骰子:", fmt_dice(dice))
            if reroll == 2:
                break
            raw = input("  保留哪些?(如 1 3 5,回车全重掷, q 退出): ").strip()
            if raw.lower() == "q":
                print("已退出。")
                return
            try:
                keep = [int(x) - 1 for x in raw.split()] if raw else []
            except ValueError:
                print("  输入无效,全部重掷。")
                keep = []
            if any(k < 0 or k >= 5 for k in keep):
                print("  序号只能是 1-5,全部重掷。")
                keep = []
            held = [dice[k] for k in keep]
            dice = held + roll(5 - len(held), rng)
        print("  最终:", fmt_dice(dice))
        avail = [k for k, _, _ in UPPER if k not in upper_scores]
        avail += [k for k, _ in LOWER if k not in scores]
        labels = {}
        for i, k in enumerate(avail, 1):
            if k in SCORERS:
                pts = SCORERS[k](dice)
            else:
                face = UPPER_FACE[k]
                pts = score_upper(dice, face)
            name = {**UPPER_NAME, **LOWER_NAME}[k]
            labels[str(i)] = (k, pts, name)
            print(f"    {i}. {name}: {pts} 分")
        while True:
            choice = input("  选计分项序号: ").strip()
            if choice in labels:
                break
            print("  无效序号,请重选。")
        k, pts, name = labels[choice]
        if k in UPPER_FACE:
            upper_scores[k] = pts
        else:
            scores[k] = pts
        print(f"  已记 {name}: {pts} 分")
    bonus = upper_bonus(upper_scores)
    total = sum(upper_scores.values()) + sum(scores.values()) + bonus
    print(f"\n上半区奖励: {bonus} 分")
    print(f"总分: {total} 分")


def play_auto(rng):
    scores, upper_scores = {}, {}
    order = [k for k, _, _ in UPPER] + [k for k, _ in LOWER]
    for k in order:
        dice = roll(5, rng)
        # 简单策略:保留出现最多的点数,重掷两次
        for _ in range(2):
            common = Counter(dice).most_common(1)[0][0]
            dice = [d for d in dice if d == common] + roll(
                5 - sum(1 for d in dice if d == common), rng)
        if k in SCORERS:
            scores[k] = SCORERS[k](dice)
        else:
            scores[k] = score_upper(dice, UPPER_FACE[k])
    upper = {k: scores[k] for k, _, _ in UPPER}
    bonus = upper_bonus(upper)
    total = sum(scores.values()) + bonus
    print(f"自动演示完成:上半区 {sum(upper.values())} 分,奖励 {bonus} 分,总分 {total} 分")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Yahtzee 骰子游戏")
    ap.add_argument("--auto", action="store_true", help="自动演示一局")
    ap.add_argument("--seed", type=int, default=None, help="随机种子")
    args = ap.parse_args(argv)
    rng = random.Random(args.seed) if args.seed is not None else secrets.SystemRandom()
    if args.auto:
        play_auto(rng)
    else:
        if not sys.stdin.isatty():
            print("error: 交互模式需要终端,请用 --auto", file=sys.stderr)
            return 2
        play_interactive(rng)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
