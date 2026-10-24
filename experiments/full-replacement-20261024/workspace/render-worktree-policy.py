#!/usr/bin/env python3
"""Render exact-path policy for the current checkout root."""
import pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3]
FIX=ROOT/'results/full-replacement-20261024/workspace/jfr-20261024-ws'
template=(pathlib.Path(__file__).with_name('architect-worktree-policy.yaml.template')).read_text()
out=ROOT/'results/full-replacement-20261024/workspace/architect-worktree-policy.rendered.yaml'
out.write_text(template.replace('__POC_ROOT__',str(ROOT)).replace('__FIXTURE_ROOT__',str(FIX)))
print(out)
