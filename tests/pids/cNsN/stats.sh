#!/bin/sh

model_gen=cNsN.py
max_clients=5
max_steps=10

config=$1
shift 1
options=$@

for clients in `seq ${max_clients}`
do
    folder=results_${config}_c${clients}
    stats=stats_${config}_c${clients}
    mkdir -p $folder $stats
    for steps in `seq ${max_steps}`
    do
	model="c${clients}s${steps}"
	outfile="${folder}/${model}_${config}.out"
	permlog="${folder}/perm_log_${model}.txt"

	grep exploration ${outfile} | sed s/exploration\ time:\ *// | tee -a ${stats}/exploration_times
	grep visited ${outfile} | sed s/len\ visited\ *=\ *// | tee -a ${stats}/state_space_sizes
	tmpfile="tmp"
	./cmp.sh ${permlog} > ${tmpfile}
	grep normalize ${tmpfile} | sed s/normalize_marking\ calls:\ *// | tee -a ${stats}/normalize_marking_calls
	grep hash ${tmpfile} | sed s/hash\ detected\ new_state:\ *// | tee -a ${stats}/hash_detected_states
	grep unknown ${tmpfile} | sed s/unknown\ marking:\ *// | tee -a ${stats}/unknow_marking_detected
	grep permutations: ${tmpfile} | sed s/permutations:\ *// | tee -a ${stats}/permutations
	grep wasteful ${tmpfile} | sed s/wasteful\ enumeration:\ *// | tee -a ${stats}/wasteful_enumerations
	rm -f ${tmpfile}
    done
done