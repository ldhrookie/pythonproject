# tier_logic.py

Cutline_point = [0, 100, 300, 500, 700, 1000, 1300, 1600, 2000, 2400,
                 2800, 3400, 4000, 4600, 5400, 6200, 7000, 8000, 9000, 10000, 1000000000]
Daily_required   = [0, 0, 10, 20, 30, 40, 50, 60, 80, 100,
                    120, 140, 160, 180, 210, 240, 270, 300, 330, 360]
Maximum          = [80, 100, 100, 100, 100, 100, 100, 100, 100, 100,
                    120, 120, 120, 120, 120, 120, 150, 150, 150, 150]
Minimum          = [0, -25, -25, -25, -50, -50, -50, -75, -75, -75,
                    -100, -100, -100, -150, -150, -150, -200, -200, -200, -300]
Avoid_fall       = [True, True, True, True, True, True, True, True, True, True,
                    True, False, False, True, False, False, False, False, False, False]
Tier = [
    '루키',
    '브론즈1', '브론즈2', '브론즈3',
    '실버1', '실버2', '실버3',
    '골드1', '골드2', '골드3',
    '다이아1', '다이아2', '다이아3',
    '크리스탈1', '크리스탈2', '크리스탈3',
    '레전드1', '레전드2', '레전드3',
    '얼티밋'
]

def update_tier_and_score(rank: int, rank_point: int, study_time: int):
    """
    rank: 현재 티어 인덱스 (Tier 리스트의 인덱스)
    rank_point: 현재 랭크 포인트(점수)
    study_time: 오늘 총 공부 시간(분 단위) – Daily_required와 비교하여 점수 변동량 계산
    return: (new_rank, new_rank_point, new_tier_name, message)
    """
    change = max(Minimum[rank], min(Maximum[rank], (study_time - Daily_required[rank])))
    msg = ""
    # 상위 컷라인 돌파
    if rank_point + change >= Cutline_point[rank + 1]:
        rank_point += change
        rank += 1
        msg = f"✅ 티어 상승: {Tier[rank - 1]} → {Tier[rank]}\n점수: {rank_point - change} → {rank_point} (+{change})"
    # 하위 컷라인 미달
    elif rank_point + change < Cutline_point[rank]:
        if Avoid_fall[rank]:
            change = rank_point - Cutline_point[rank]
            rank_point = Cutline_point[rank]
            msg = f"⚠️ 티어 강등 방지: {Tier[rank]} 유지\n점수: {rank_point - change} → {rank_point} ({change})"
        else:
            rank_point += change
            rank -= 1
            msg = f"❌ 티어 하락: {Tier[rank + 1]} → {Tier[rank]}\n점수: {rank_point - change} → {rank_point} ({change})"
    else:
        rank_point += change
        msg = f"ℹ️ 점수 변화: {rank_point - change} → {rank_point} ({change})"
    return rank, rank_point, Tier[rank], msg
