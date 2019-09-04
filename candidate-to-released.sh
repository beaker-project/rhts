#!/bin/bash
set -e
usage() {
    echo "Moves all builds from their *-candidate tags to *" >&2
    echo "Usage: $0 <ver-rel>, example: $0 0.7.2-1" >&2
    exit 1
}
[[ -z "$VERREL" ]] && VERREL="$1"
[[ -z "$VERREL" ]] && usage
brew move-pkg beaker-harness-rhel-5{-candidate,} rhts-$VERREL.el5bkr
brew move-pkg beaker-harness-rhel-6{-candidate,} rhts-$VERREL.el6bkr
brew move-pkg beaker-harness-rhel-7{-candidate,} rhts-$VERREL.el7bkr
brew move-pkg beaker-harness-rhel-8{-candidate,} rhts-$VERREL.el8bkr
brew move-pkg eng-fedora-29{-candidate,} rhts-$VERREL.f29eng
brew move-pkg eng-fedora-30{-candidate,} rhts-$VERREL.f30eng
brew move-pkg eng-fedora-31{-candidate,} rhts-$VERREL.f31eng
brew move-pkg eng-fedora-32{-candidate,} rhts-$VERREL.f32eng
