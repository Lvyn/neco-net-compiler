#!/bin/sh

model_gen=cNsN.py
max_clients=3
max_steps=5
max_runs=10

config=$1
shift 1
options=$@

for clients in `seq ${max_clients}`
do
    folder=results_${config}_c${clients}
    mkdir -p $folder
    for steps in `seq ${max_steps}`
    do
	model="c${clients}s${steps}"
	echo "////////////////////////////////////////////////////////////////////////////////"
	echo "// Model ${model} ${config} (options: ${options})"
	echo "////////////////////////////////////////////////////////////////////////////////"

        # generate model file
	sed s/{{{CLIENTS}}}/${clients}/ ${model_gen} | sed s/{{{STEPS}}}/${steps}/ > ${model}.py

	# run the can "max_runs" times
	for run in `seq ${max_runs}`
	do
	    rm -f perm_log

	    outfile="${folder}/${model}_${config}_${run}.out"

	    neco-compile -m ${model} -i neco.extsnakes ${options} | tee -a ${outfile}
	    neco-explore | tee -a ${outfile}

	    touch perm_log
	    mv perm_log ${folder}/perm_log_${model}_${run}.txt
	    rm -f net.py
	    rm -f trace
	    rm -f *.pyc
	done
	rm -f ${model}.py
    done
done