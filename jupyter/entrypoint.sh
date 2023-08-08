#!/bin/bash
set -e

command=$1
arguments=${*:2}
if [[ -z $arguments ]]; then
  arguments_debug="no arguments"
else
  arguments_debug="arguments ($arguments)"
fi

# echo "Running \"$command\" with $arguments_debug"

show_help() {
  echo """
  Available commands:

  notebook            : start notebook server
  pipeline            : run pipeline in local or cloud mode (ex: pipeline cloudrun '{}')
  
  Any arguments passed will be forwarded to the executed command
  """
}

case "$command" in
"notebook")
  start-notebook.sh
  ;;
"pipeline")
  python /home/hexa/.hexa_scripts/bootstrap_pipeline.py $arguments
  ;;
"help")
  show_help
  ;;
esac
