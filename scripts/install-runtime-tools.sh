#!/usr/bin/env bash
set -euo pipefail

PEEP_DATA_ROOT="${XDG_DATA_HOME:-${HOME}/.local/share}/peep-skills/tools"
PEEP_BIN_ROOT="${XDG_BIN_HOME:-${HOME}/.local/bin}"
GRAPHIFY_SPEC="graphifyy @ git+https://github.com/Graphify-Labs/graphify.git@edec9eabeceeae6aa2375eddb3835efa1a32c0a3"
NOTEBOOKLM_SPEC="notebooklm-py[browser] @ git+https://github.com/teng-lin/notebooklm-py.git@45fd4258e608fbb9685496f26cfcea48810c44ee"

install_tool() {
  local env_name="$1"
  local command_name="$2"
  local package_spec="$3"
  local env_dir="${PEEP_DATA_ROOT}/${env_name}"
  local command_source="${env_dir}/bin/${command_name}"
  local command_target="${PEEP_BIN_ROOT}/${command_name}"

  python3 -m venv "${env_dir}"
  "${env_dir}/bin/python" -m pip install --upgrade pip
  "${env_dir}/bin/python" -m pip install --upgrade "${package_spec}"

  mkdir -p "${PEEP_BIN_ROOT}"
  if [[ -e "${command_target}" || -L "${command_target}" ]]; then
    if [[ "$(readlink -f "${command_target}")" != "$(readlink -f "${command_source}")" ]]; then
      printf 'Conflito: %s já existe e não foi sobrescrito.\n' "${command_target}" >&2
      return 1
    fi
  else
    ln -s "${command_source}" "${command_target}"
  fi
}

install_tool "graphify" "graphify" "${GRAPHIFY_SPEC}"
install_tool "notebooklm" "notebooklm" "${NOTEBOOKLM_SPEC}"

graphify --version
notebooklm --version
