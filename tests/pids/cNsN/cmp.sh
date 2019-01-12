#!/bin/sh

perm_log=$1

nb() {
    grep -o $1 $2 | wc -l
}

echo -n "normalize_marking calls: "
nb "\." ${perm_log}

echo -n "hash detected new_state: "
nb "h" ${perm_log}

echo -n "unknown marking: "
nb "\+" ${perm_log}

echo -n "permutations: "
nb "\*" ${perm_log}

echo -n "wasteful enumeration: "
nb "\%" ${perm_log}
