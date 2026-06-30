#!/usr/bin/env bash
set -u

tex_file=""

usage() {
  echo "Usage: $0 --tex-file path/to/paper.tex"
  echo "       $0 -TexFile path/to/paper.tex"
  echo "       $0 path/to/paper.tex"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --tex-file|-TexFile|-f)
      if [[ $# -lt 2 ]]; then
        usage
        exit 2
      fi
      tex_file="$2"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ -z "$tex_file" ]]; then
        tex_file="$1"
        shift
      else
        echo "Unexpected argument: $1" >&2
        usage
        exit 2
      fi
      ;;
  esac
done

if [[ -z "$tex_file" ]]; then
  usage
  exit 2
fi

if [[ ! -f "$tex_file" ]]; then
  echo "File not found: $tex_file" >&2
  exit 2
fi

content=$(sed '/^[[:space:]]*%/d' "$tex_file")
issues=()
warnings=()

add_issue() { issues+=("$1"); }
add_warning() { warnings+=("$1"); }

if ! grep -Eq '\\documentclass\[[^]]*journal[^]]*twocolumn[^]]*\]\{IEEEtran\}' <<< "$content"; then
  add_issue "Document class is not IEEEtran journal twocolumn."
fi

if ! grep -Eq '\\maketitle' <<< "$content"; then
  add_issue "Missing \\maketitle."
fi

if grep -Eq '\\IEEEauthorblockN|\\IEEEauthorblockA' <<< "$content"; then
  add_issue "Conference-style IEEEauthorblock commands remain in journal mode."
fi

if grep -Eq '\\begin\{IEEEbiography\}|\\begin\{IEEEbiographynophoto\}|PLACE PHOTO HERE' <<< "$content"; then
  add_issue "Author biography/photo placeholder content remains."
fi

if grep -Eq '\\hfill[[:space:]]*\(e-mail|Corresponding author:.*\\hfill' <<< "$content"; then
  add_issue "Potentially unsafe \\hfill in author/corresponding-author email text."
fi

if awk '
  /\\begin\{figure\}(\[[^]]*\])?/ { infig=1; block="" }
  infig { block = block $0 "\n" }
  /\\end\{figure\}/ && infig {
    if (block ~ /\\includegraphics\[[^]]*width[[:space:]]*=[[:space:]]*\\textwidth/) found=1
    infig=0; block=""
  }
  END { exit(found ? 0 : 1) }
' <<< "$content"; then
  add_warning "A single-column figure appears to use width=\\textwidth; consider \\columnwidth or figure*."
fi

if grep -Eq 'width[[:space:]]*=[[:space:]]*1\.[0-9]+\\textwidth' <<< "$content"; then
  add_warning "Overwide draft graphic/table sizing remains, e.g. width=1.x\\textwidth."
fi

if grep -Eq '\\begin\{figure\}\[H\]|\\begin\{table\}\[H\]' <<< "$content"; then
  add_warning "Pinned [H] floats remain; verify they are intentional in two-column mode."
fi

if grep -Eq '\\end\{thebibliography\}' <<< "$content"; then
  tail_content=$(awk '
    /\\end\{thebibliography\}/ { seen=1; next }
    /\\end\{document\}/ { exit }
    seen { print }
  ' <<< "$content" | sed '/^[[:space:]]*$/d')
  if [[ -n "$tail_content" ]]; then
    add_warning "Content remains between \\end{thebibliography} and \\end{document}."
  fi
fi

echo "IEEE two-column audit: $tex_file"

if [[ ${#issues[@]} -eq 0 ]]; then
  echo "Fatal/structural issues: none"
else
  echo "Fatal/structural issues:"
  for item in "${issues[@]}"; do
    echo "  - $item"
  done
fi

if [[ ${#warnings[@]} -eq 0 ]]; then
  echo "Warnings: none"
else
  echo "Warnings:"
  for item in "${warnings[@]}"; do
    echo "  - $item"
  done
fi

if [[ ${#issues[@]} -gt 0 ]]; then
  exit 1
fi

exit 0