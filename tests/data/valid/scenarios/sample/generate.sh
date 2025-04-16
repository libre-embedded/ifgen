#!/bin/bash

safe_pushd() {
	pushd "$1" >/dev/null || exit
}

safe_popd() {
	popd >/dev/null 2>&1 || exit
}

REPO=$(git rev-parse --show-toplevel)

safe_pushd "$REPO/tests/data/valid/scenarios/sample"

rm -rf src/generated src/apps/generated
../../../../../venv/bin/ig gen

safe_popd
