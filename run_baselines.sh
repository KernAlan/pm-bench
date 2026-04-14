#!/usr/bin/env bash
# Idempotent baseline runner. Skips work already done.
set -u
cd "$(dirname "$0")"
export PYTHONIOENCODING=utf-8

MODELS=(gpt-4.1-nano gpt-4.1-mini gpt-5-nano gpt-5-mini gpt-5.4-nano gpt-5.4-mini)
JUDGE="gpt-4.1-mini"

count_runs() {
    # Args: model, kind ("sh20" matches files with total=20, "full48" total>20)
    local model="$1" kind="$2" total
    local n=0
    for f in results/*_mcq_openai_${model}.json; do
        [ -f "$f" ] || continue
        total=$(python -c "import json; print(json.load(open('$f'))['total'])" 2>/dev/null)
        if [ "$kind" = "sh20" ] && [ "$total" = "20" ]; then n=$((n+1)); fi
        if [ "$kind" = "full48" ] && [ "$total" -gt 20 ]; then n=$((n+1)); fi
    done
    echo "$n"
}

count_open() {
    local model="$1" n=0
    for f in results/*_open-ended_openai_${model}.json; do
        [ -f "$f" ] || continue
        n=$((n+1))
    done
    echo "$n"
}

echo "==== Stage 1: Superhuman 20 to 3 iterations per model ===="
for m in "${MODELS[@]}"; do
    have=$(count_runs "$m" "sh20")
    need=$((3 - have))
    if [ "$need" -le 0 ]; then
        echo ">>> $m: have $have runs, skipping"
        continue
    fi
    for i in $(seq 1 "$need"); do
        echo ">>> $m: superhuman iter $((have + i))"
        python run.py --provider openai --model "$m" --superhuman-only 2>&1 | tail -2
    done
done

echo ""
echo "==== Stage 2: Full 48 (1 iteration per model) ===="
for m in "${MODELS[@]}"; do
    have=$(count_runs "$m" "full48")
    if [ "$have" -ge 1 ]; then
        echo ">>> $m: full48 already done"
        continue
    fi
    echo ">>> $m: full 48"
    python run.py --provider openai --model "$m" 2>&1 | tail -2
done

echo ""
echo "==== Stage 3: Open-ended 20 (1 iteration, judge=$JUDGE) ===="
for m in "${MODELS[@]}"; do
    have=$(count_open "$m")
    if [ "$have" -ge 1 ]; then
        echo ">>> $m: open-ended already done"
        continue
    fi
    echo ">>> $m: open-ended"
    python run.py --provider openai --model "$m" --mode open-ended --judge-provider openai --judge-model "$JUDGE" 2>&1 | tail -2
done

echo ""
echo "==== ALL BASELINES COMPLETE ===="
ls -1 results/*.json | wc -l
